"""In-memory MCP e2e tests for the Plot MCP server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import anyio
import pytest
import mcp_server
from mcp_server import mcp
from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage
from backend.file_utils import build_alias_map
from backend.plot_engine import PlotEngine
from backend.data_manager import DataManager


def _build_message(message_id: str, method: str, params: dict | None = None) -> SessionMessage:
    payload = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params
    message = JSONRPCMessage.model_validate(payload)
    return SessionMessage(message)


def _init_message(message_id: str = "init") -> SessionMessage:
    return _build_message(
        message_id,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    )


def _set_upload_dir(path: str) -> None:
    mcp_server.DATA_MANAGER.upload_dir = path
    if not os.path.isdir(path):
        os.makedirs(path)


async def _run_mcp(messages: list[SessionMessage]):
    read_send, read_recv = anyio.create_memory_object_stream(16)
    write_send, write_recv = anyio.create_memory_object_stream(16)

    async def serve() -> None:
        await mcp._mcp_server.run(
            read_recv, write_send, mcp._mcp_server.create_initialization_options()
        )

    responses = []
    async with anyio.create_task_group() as tg:
        tg.start_soon(serve)
        for message in messages:
            await read_send.send(message)
        for _ in messages:
            responses.append(await write_recv.receive())
        tg.cancel_scope.cancel()

    return [resp.message.model_dump() for resp in responses]


def test_initialize_and_list_tools():
    async def scenario() -> None:
        init = _init_message("1")
        list_tools = _build_message("2", "tools/list", {})

        responses = await _run_mcp([init, list_tools])
        init_resp, list_resp = responses

        assert init_resp["result"]["serverInfo"]["name"] == "PlotMCP"
        tool_names = {tool["name"] for tool in list_resp["result"]["tools"]}
        assert {"describe_data", "plot_data", "describe_file", "plot_file"}.issubset(tool_names)

    anyio.run(scenario)


def test_describe_data_returns_preview_and_analysis():
    async def scenario() -> None:
        init = _init_message("1")
        describe = _build_message(
            "2",
            "tools/call",
            {
                "name": "describe_data",
                "arguments": {"data": "a,b\n1,2\n3,4", "format": "csv"},
            },
        )

        responses = await _run_mcp([init, describe])
        _, describe_resp = responses

        result = describe_resp["result"]
        structured = result.get("structuredContent", {})
        analysis = structured.get("result", {}).get("analysis", {})
        preview = structured.get("result", {}).get("preview", [])

        assert analysis.get("columns") == ["a", "b"]
        assert analysis.get("numeric_cols") == ["a", "b"]
        assert len(preview) == 2

    anyio.run(scenario)


def test_describe_data_handles_json_format(tmp_path):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))
        init = _init_message("1")
        describe = _build_message(
            "2",
            "tools/call",
            {
                "name": "describe_data",
                "arguments": {
                    "data": '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]',
                    "format": "json",
                },
            },
        )

        responses = await _run_mcp([init, describe])
        _, describe_resp = responses

        result = describe_resp["result"]
        structured = result.get("structuredContent", {})
        analysis = structured.get("result", {}).get("analysis", {})
        preview = structured.get("result", {}).get("preview", [])

        assert analysis.get("columns") == ["a", "b"]
        assert len(preview) == 2
        assert preview[0]["a"] == 1

    anyio.run(scenario)


def test_plot_data_returns_clarification(tmp_path, monkeypatch):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))

        async def fake_process_query(**kwargs):
            return {"type": "clarify", "text": "Need columns to plot"}

        monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_data",
                "arguments": {
                    "data": "x,y\n1,2\n3,4",
                    "instruction": "plot the data",
                    "format": "csv",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]

        assert any("Need columns to plot" in text for text in texts)

    anyio.run(scenario)


def test_plot_data_generates_image_and_code(tmp_path, monkeypatch):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))

        async def fake_process_query(**kwargs):
            return {
                "type": "plot_code",
                "code": (
                    "plt.figure(figsize=(4, 3))\n"
                    "plt.plot(df['x'], df['y'], label='series')\n"
                    "plt.xlabel('x')\n"
                    "plt.ylabel('y')\n"
                    "plt.legend()\n"
                ),
                "text": "generated",
            }

        monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_data",
                "arguments": {
                    "data": "x,y\n0,0\n1,1\n2,4",
                    "instruction": "plot y vs x",
                    "format": "csv",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])

        text_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
        image_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "image"]

        assert text_blocks, "Expected a text block in plot response"
        assert image_blocks, "Expected an image block in plot response"
        assert "Plot generated successfully" in text_blocks[0].get("text", "")
        assert len(image_blocks[0].get("data", b"")) > 0

    anyio.run(scenario)


def test_plot_data_with_empty_input_generates_image(tmp_path, monkeypatch):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))

        async def fake_process_query(**kwargs):
            return {
                "type": "plot_code",
                "code": (
                    "x = np.linspace(0, 2 * np.pi, 200)\n"
                    "y = np.sin(x)\n"
                    "plt.figure(figsize=(4, 3))\n"
                    "plt.plot(x, y)\n"
                    "plt.xlabel('x')\n"
                    "plt.ylabel('sin(x)')\n"
                ),
                "text": "generated",
            }

        monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_data",
                "arguments": {
                    "data": "",
                    "instruction": "plot a sine wave",
                    "format": "csv",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])

        text_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
        image_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "image"]

        assert text_blocks, "Expected a text block in plot response"
        assert image_blocks, "Expected an image block in plot response"
        assert "Plot generated successfully" in text_blocks[0].get("text", "")

    anyio.run(scenario)


def test_plot_data_reports_lint_errors(tmp_path, monkeypatch):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))

        async def fake_process_query(**kwargs):
            return {
                "type": "plot_code",
                "code": "plt.plot(df['x'], ...)",  # triggers lint placeholder error
                "text": "generated",
            }

        monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_data",
                "arguments": {
                    "data": "x,y\n0,0\n1,1",
                    "instruction": "plot y vs x",
                    "format": "csv",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]

        assert any("Placeholder" in text or "Plot execution failed" in text for text in texts)

    anyio.run(scenario)


def test_plot_data_rejects_disallowed_import(tmp_path, monkeypatch):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))

        async def fake_process_query(**kwargs):
            return {
                "type": "plot_code",
                "code": "import os\nplt.figure()\nplt.plot([1,2],[3,4])",
                "text": "generated",
            }

        monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_data",
                "arguments": {
                    "data": "x,y\n0,0\n1,1",
                    "instruction": "plot y vs x",
                    "format": "csv",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]

        assert any("Import not allowed" in text or "Plot execution failed" in text for text in texts)

    anyio.run(scenario)


def test_plot_engine_blocks_disallowed_import(tmp_path):
    plot_engine = PlotEngine()
    code = "import os\nplt.figure()\nplt.plot([0, 1], [0, 1])"
    alias_map = build_alias_map([])
    result = plot_engine.execute_code(code, data_paths=alias_map)
    assert result["error"] is True
    assert "Import not allowed" in result["error_message"]


def test_plot_engine_supports_multiple_aliases(tmp_path):
    file_one = tmp_path / "a.csv"
    file_two = tmp_path / "b.csv"
    file_one.write_text("x,y\n0,0\n1,1\n2,4")
    file_two.write_text("y\n0\n1\n2")

    alias_map = {
        "df_one": str(file_one),
        "df_two": str(file_two),
    }

    code_lines = [
        "plt.figure(figsize=(3, 2))",
        "plt.plot(dfs['df_one']['x'], dfs['df_one']['y'], label='main')",
        "plt.plot(dfs['df_one']['x'], dfs['df_two']['y'], label='secondary')",
        "plt.legend()",
    ]
    code = "\n".join(code_lines)

    plot_engine = PlotEngine()
    result = plot_engine.execute_code(code, data_paths=alias_map)

    assert result.get("error") is None
    assert result.get("buffer") is not None
    assert result["buffer"].getbuffer().nbytes > 0


def test_call_unknown_tool_returns_error():
    async def scenario() -> None:
        init = _init_message("1")
        bad_call = _build_message(
            "2",
            "tools/call",
            {"name": "nonexistent_tool", "arguments": {}},
        )

        responses = await _run_mcp([init, bad_call])
        _, bad_resp = responses

        if "error" in bad_resp:
            assert bad_resp["error"]["code"] == -32601
            return

        result = bad_resp.get("result", {})
        assert result.get("isError") is True
        content = result.get("content", [])
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]
        assert any("Unknown tool" in text for text in texts)

    anyio.run(scenario)


def test_unknown_method_returns_jsonrpc_error():
    async def scenario() -> None:
        init = _init_message("1")
        bad_method = _build_message("2", "not_a_method", {})

        responses = await _run_mcp([init, bad_method])
        _, bad_resp = responses

        assert "error" in bad_resp
        assert bad_resp["error"]["code"] in {-32601, -32602}

    anyio.run(scenario)


def test_describe_data_rejects_invalid_format():
    async def scenario() -> None:
        init = _init_message("1")
        describe = _build_message(
            "2",
            "tools/call",
            {
                "name": "describe_data",
                "arguments": {"data": "a,b\n1,2", "format": "txt"},
            },
        )

        responses = await _run_mcp([init, describe])
        _, describe_resp = responses

        assert "error" in describe_resp or describe_resp.get("result", {}).get("isError")

    anyio.run(scenario)


def test_describe_data_preview_is_capped(tmp_path):
    async def scenario() -> None:
        _set_upload_dir(str(tmp_path))
        rows = "\n".join(f"{i},{i*i}" for i in range(25))
        csv = f"a,b\n{rows}"

        init = _init_message("1")
        describe = _build_message(
            "2",
            "tools/call",
            {
                "name": "describe_data",
                "arguments": {"data": csv, "format": "csv"},
            },
        )

        responses = await _run_mcp([init, describe])
        _, describe_resp = responses
        structured = describe_resp["result"].get("structuredContent", {})
        preview = structured.get("result", {}).get("preview", [])

        assert len(preview) == 10

    anyio.run(scenario)


def test_describe_file_reads_allowed_path(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b\n1,2\n3,4")

    monkeypatch.setenv("PLOT_MCP_ALLOWED_DIRS", str(tmp_path))

    async def scenario() -> None:
        init = _init_message("1")
        describe = _build_message(
            "2",
            "tools/call",
            {
                "name": "describe_file",
                "arguments": {"file_path": str(csv_path)},
            },
        )

        responses = await _run_mcp([init, describe])
        _, describe_resp = responses

        result = describe_resp["result"]
        structured = result.get("structuredContent", {})
        analysis = structured.get("result", {}).get("analysis", {})
        preview = structured.get("result", {}).get("preview", [])

        assert analysis.get("columns") == ["a", "b"]
        assert len(preview) == 2

    anyio.run(scenario)


def test_plot_file_generates_image(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("x,y\n0,0\n1,1\n2,4")

    monkeypatch.setenv("PLOT_MCP_ALLOWED_DIRS", str(tmp_path))

    async def fake_process_query(**kwargs):
        return {
            "type": "plot_code",
            "code": (
                "plt.figure(figsize=(4, 3))\n"
                "plt.plot(df['x'], df['y'], label='series')\n"
                "plt.xlabel('x')\n"
                "plt.ylabel('y')\n"
                "plt.legend()\n"
            ),
            "text": "generated",
        }

    monkeypatch.setattr(mcp_server.LLM_SERVICE, "process_query", fake_process_query)

    async def scenario() -> None:
        init = _init_message("1")
        plot_call = _build_message(
            "2",
            "tools/call",
            {
                "name": "plot_file",
                "arguments": {
                    "file_path": str(csv_path),
                    "instruction": "plot y vs x",
                    "provider": "ollama",
                },
            },
        )

        responses = await _run_mcp([init, plot_call])
        _, plot_resp = responses
        result = plot_resp.get("result", {})
        content = result.get("content", [])

        text_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "text"]
        image_blocks = [item for item in content if isinstance(item, dict) and item.get("type") == "image"]

        assert text_blocks, "Expected a text block in plot response"
        assert image_blocks, "Expected an image block in plot response"
        assert "Plot generated successfully" in text_blocks[0].get("text", "")

    anyio.run(scenario)


def test_data_manager_multi_context(tmp_path):
    data_manager = DataManager(upload_dir=str(tmp_path))
    file_one = tmp_path / "one.csv"
    file_two = tmp_path / "two.json"
    file_one.write_text("x,y\n0,1\n2,3")
    file_two.write_text('[{"a": 1, "b": 2}, {"a": 3, "b": 4}]')

    context = data_manager.get_multi_data_context(
        {"alias_one": str(file_one), "alias_two": str(file_two)}
    )

    assert "alias_one" in context
    assert "alias_two" in context
    assert "Columns: ['x', 'y']" in context
    assert "Data Columns: ['a', 'b']" in context or "a', 'b" in context


def test_transport_selection_env(monkeypatch):
    monkeypatch.setenv("PLOT_MCP_TRANSPORT", "stdio")
    assert mcp_server._select_transport() == "stdio"
    monkeypatch.setenv("PLOT_MCP_TRANSPORT", "streamable-http")
    assert mcp_server._select_transport() == "streamable-http"


@pytest.mark.xfail(raises=PermissionError, reason="Socket creation may be blocked in sandbox")
def test_choose_available_port_skips_used_port():
    import socket

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    used_port = sock.getsockname()[1]

    chosen = mcp_server._choose_available_port("127.0.0.1", used_port, scan_limit=4)
    sock.close()

    assert chosen != used_port


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
