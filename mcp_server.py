"""Standalone MCP server for Plot MCP."""

from __future__ import annotations

import base64
import importlib.util
import os
import socket
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = os.path.dirname(__file__)
VENDOR_DIR = os.path.join(ROOT_DIR, "vendor")
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    vendor_priority = os.getenv("PLOT_VENDOR_PRIORITY", "0").strip().lower()
    vendor_first = vendor_priority in {"1", "true", "yes", "on"}
    if vendor_first:
        sys.path.insert(0, VENDOR_DIR)
    else:
        sys.path.append(VENDOR_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

def _require_module(module_name: str) -> None:
    if importlib.util.find_spec(module_name) is not None:
        return

    sys.stderr.write(
        f"Missing dependency: {module_name!r}\n\n"
        "Install dependencies:\n"
        "- User install (recommended): python3 -m pip install --user -r requirements.txt\n"
        "- Repo-local install:         python3 -m pip install --target vendor -r requirements.txt\n\n"
        "Then run:\n"
        "  python3 mcp_server.py\n"
    )
    raise SystemExit(1)

def _read_int_env(env_name: str, default: int) -> int:
    value = os.getenv(env_name, "").strip()
    if value.isdigit():
        return int(value)
    return default


def _select_transport() -> str:
    mode = os.getenv("PLOT_MCP_TRANSPORT", "auto").strip().lower()
    allowed = {"auto", "stdio", "sse", "streamable-http"}
    if mode not in allowed:
        sys.stderr.write(
            "Invalid PLOT_MCP_TRANSPORT value. Use one of: auto, stdio, sse, streamable-http\n"
        )
        raise SystemExit(1)
    if mode != "auto":
        return mode
    if sys.stdin.isatty() and sys.stdout.isatty():
        return "streamable-http"
    return "stdio"


def _write_startup_hint(transport: str, host: str, port: int) -> None:
    if transport == "stdio":
        sys.stderr.write(
            "PlotMCP started in stdio mode (MCP client should launch this process).\n"
        )
        return

    if transport == "sse":
        sys.stderr.write(f"PlotMCP SSE server listening on http://{host}:{port}/sse\n")
        sys.stderr.write(f"Messages endpoint: http://{host}:{port}/messages/\n")
        return

    sys.stderr.write(f"PlotMCP Streamable HTTP server listening on http://{host}:{port}/mcp\n")

def _is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.15)
        return sock.connect_ex((host, port)) == 0


def _choose_available_port(host: str, preferred_port: int, scan_limit: int = 32) -> int:
    if preferred_port <= 0:
        return 8765

    candidate = preferred_port
    for _ in range(max(1, scan_limit)):
        if not _is_port_in_use(host, candidate):
            return candidate
        candidate += 1
    return preferred_port


if importlib.util.find_spec("mcp.server.fastmcp") is None:
    missing_hint = (
        "Missing dependency: 'mcp'\n\n"
        "Install dependencies:\n"
        "- User install: python3 -m pip install --user -r requirements.txt\n"
        "- Repo-local install: python3 -m pip install --target vendor -r requirements.txt\n\n"
        "Then run:\n"
        "  python3 mcp_server.py\n"
    )
    sys.stderr.write(missing_hint)
    raise SystemExit(1)

_require_module("pandas")
_require_module("numpy")
_require_module("matplotlib")
_require_module("seaborn")
_require_module("requests")

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image

from data_manager import DataManager
from data_validator import get_validator
from llm_service import LLMService
from plot_engine import PlotEngine
from plot_templates import maybe_generate_template_plot

FASTMCP_HOST = os.getenv("FASTMCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
FASTMCP_PORT = _read_int_env("FASTMCP_PORT", 8765)

mcp = FastMCP("PlotMCP", host=FASTMCP_HOST, port=FASTMCP_PORT)

DATA_MANAGER = DataManager()
LLM_SERVICE = LLMService()
PLOT_ENGINE = PlotEngine()


def _build_filename(format_type: str) -> str:
    extension = "csv" if format_type == "csv" else "json"
    return f"mcp_{uuid.uuid4().hex}.{extension}"


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def _parse_allowed_dirs() -> List[Path]:
    raw = os.getenv("PLOT_MCP_ALLOWED_DIRS", "").strip()
    if not raw:
        return [Path(ROOT_DIR).resolve()]
    parts = [item.strip() for item in raw.split(os.pathsep) if item.strip()]
    return [Path(item).expanduser().resolve() for item in parts]


def _infer_format_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    raise ValueError("Unsupported file format; only .csv and .json are allowed")


def _resolve_allowed_path(file_path: str) -> Path:
    candidate = Path(file_path).expanduser().resolve()
    if not candidate.is_file():
        raise ValueError("File does not exist")

    allowed_dirs = _parse_allowed_dirs()
    if not any(root == candidate or root in candidate.parents for root in allowed_dirs):
        raise ValueError("File is outside allowed directories")

    max_mb = _read_int_env("PLOT_MCP_MAX_FILE_MB", 20)
    if max_mb > 0 and candidate.stat().st_size > max_mb * 1024 * 1024:
        raise ValueError("File exceeds size limit")

    return candidate


def _build_latest_html(latest_filename: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta http-equiv=\"refresh\" content=\"2\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "  <title>Plot MCP Latest</title>\n"
        "  <style>\n"
        "    body { margin: 0; padding: 16px; font-family: serif; background: #f5f5f5; }\n"
        "    .frame { background: #fff; padding: 12px; border-radius: 8px; }\n"
        "    img { max-width: 100%; height: auto; display: block; }\n"
        "    .meta { margin-top: 10px; font-size: 12px; color: #555; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"frame\">\n"
        f"    <img src=\"{latest_filename}\" alt=\"Latest plot\">\n"
        "    <div class=\"meta\">Auto-refresh every 2 seconds.</div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>\n"
    )


def _write_plot_image(image_bytes: bytes, image_format: str) -> Dict[str, str]:
    output_dir = os.getenv("PLOT_MCP_OUTPUT_DIR", os.path.join(ROOT_DIR, "mcp_outputs"))
    _ensure_dir(output_dir)
    filename = f"plot_{uuid.uuid4().hex}.{image_format}"
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    latest_filename = f"latest.{image_format}"
    latest_path = os.path.join(output_dir, latest_filename)
    with open(latest_path, "wb") as f:
        f.write(image_bytes)

    latest_html_path = os.path.join(output_dir, "latest.html")
    latest_html = _build_latest_html(latest_filename)
    with open(latest_html_path, "w") as f:
        f.write(latest_html)

    return {
        "image_path": output_path,
        "latest_path": latest_path,
        "latest_html": latest_html_path,
    }


def _should_embed_image(image_bytes: bytes) -> bool:
    limit_kb = _read_int_env("PLOT_MCP_IMAGE_INLINE_MAX_KB", 256)
    if limit_kb <= 0:
        return True
    return len(image_bytes) <= limit_kb * 1024


@mcp.tool(structured_output=True)
async def describe_data(data: str, format: str = "csv") -> Dict[str, object]:
    """Analyze a dataset and return summary plus preview rows."""
    filename = _build_filename(format)
    file_path = await DATA_MANAGER.save_text_data(data, filename)
    df = DATA_MANAGER.load_data(file_path)
    validator = get_validator()
    analysis = validator.analyze_data(df)
    analysis["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    preview = df.head(10).to_dict(orient="records")
    return {"analysis": analysis, "preview": preview}


@mcp.tool(structured_output=True)
async def describe_file(file_path: str) -> Dict[str, object]:
    """Analyze a local CSV/JSON file and return summary plus preview rows."""
    resolved = _resolve_allowed_path(file_path)
    _infer_format_from_path(resolved)
    df = DATA_MANAGER.load_data(str(resolved))
    validator = get_validator()
    analysis = validator.analyze_data(df)
    analysis["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    preview = df.head(10).to_dict(orient="records")
    return {"analysis": analysis, "preview": preview}


@mcp.tool(structured_output=False)
async def plot_data(
    data: str,
    instruction: str,
    format: str = "csv",
    provider: str = "ollama",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> list[object]:
    """Generate a plot from raw data and a natural-language instruction."""
    data_text = (data or "").strip()
    file_path = None
    analysis = None
    context = None
    if data_text:
        filename = _build_filename(format)
        file_path = await DATA_MANAGER.save_text_data(data_text, filename)
        df = DATA_MANAGER.load_data(file_path)
        validator = get_validator()
        analysis = validator.analyze_data(df)
        context = DATA_MANAGER.get_data_context(file_path)

    template_plot = None
    template_mode = os.getenv("PLOT_TEMPLATE_MODE", "off").strip().lower()
    templates_enabled = template_mode not in {"off", "0", "false", "disabled"}
    if templates_enabled and not data_text:
        template_plot = maybe_generate_template_plot(instruction)

    if template_plot:
        response = {
            "type": "plot_code",
            "code": template_plot.code,
            "text": f"I generated a {template_plot.description}.",
        }
    else:
        LLM_SERVICE.set_provider(provider, api_key, model)
        response = await LLM_SERVICE.process_query(
            query=instruction,
            context=context,
            data_analysis=analysis,
        )

    if response.get("type") == "clarify":
        return [str(response.get("text", ""))]

    if response.get("type") != "plot_code":
        return [str(response.get("text", ""))]

    plot_result = PLOT_ENGINE.execute_code(response["code"], file_path)
    if plot_result.get("error"):
        warnings = plot_result.get("warnings", [])
        warning_text = ""
        if warnings:
            warning_text = "\n\nWarnings:\n- " + "\n- ".join(str(item) for item in warnings)
        message = f"Plot execution failed: {plot_result.get('error_message', 'Unknown error')}{warning_text}"
        return [message]

    buffer = plot_result.get("buffer")
    image_bytes = buffer.getvalue() if hasattr(buffer, "getvalue") else b""
    warnings = plot_result.get("warnings", [])
    warning_text = ""
    if warnings:
        warning_text = "\n\nWarnings:\n- " + "\n- ".join(str(item) for item in warnings)

    code = response.get("code", "")
    image_format = "png"
    image_info = _write_plot_image(image_bytes, image_format)
    image_path = image_info["image_path"]
    latest_path = image_info["latest_path"]
    latest_html = image_info["latest_html"]
    fallback_text = (
        f"\n\nSaved image: {image_path}"
        f"\nLatest image: {latest_path}"
        f"\nLatest viewer: {latest_html}"
    )
    if os.getenv("PLOT_MCP_IMAGE_FALLBACK", "0") == "1":
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/{image_format};base64,{encoded}"
        if _should_embed_image(image_bytes):
            fallback_text += f"\n\nEmbedded image (data URL):\n![plot]({data_url})"
        else:
            fallback_text += "\n\nEmbedded image omitted (too large)."

    message = f"Plot generated successfully.{warning_text}{fallback_text}\n\n```python\n{code}\n```"
    return [message, Image(data=image_bytes, format=image_format)]


@mcp.tool(structured_output=False)
async def plot_file(
    file_path: str,
    instruction: str,
    provider: str = "ollama",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> list[object]:
    """Generate a plot from a local CSV/JSON file and a natural-language instruction."""
    resolved = _resolve_allowed_path(file_path)
    _infer_format_from_path(resolved)
    df = DATA_MANAGER.load_data(str(resolved))
    validator = get_validator()
    analysis = validator.analyze_data(df)

    LLM_SERVICE.set_provider(provider, api_key, model)
    response = await LLM_SERVICE.process_query(
        query=instruction,
        context=DATA_MANAGER.get_data_context(str(resolved)),
        data_analysis=analysis,
    )

    if response.get("type") == "clarify":
        return [str(response.get("text", ""))]

    if response.get("type") != "plot_code":
        return [str(response.get("text", ""))]

    plot_result = PLOT_ENGINE.execute_code(response["code"], str(resolved))
    if plot_result.get("error"):
        warnings = plot_result.get("warnings", [])
        warning_text = ""
        if warnings:
            warning_text = "\n\nWarnings:\n- " + "\n- ".join(str(item) for item in warnings)
        message = f"Plot execution failed: {plot_result.get('error_message', 'Unknown error')}{warning_text}"
        return [message]

    buffer = plot_result.get("buffer")
    image_bytes = buffer.getvalue() if hasattr(buffer, "getvalue") else b""
    warnings = plot_result.get("warnings", [])
    warning_text = ""
    if warnings:
        warning_text = "\n\nWarnings:\n- " + "\n- ".join(str(item) for item in warnings)

    code = response.get("code", "")
    image_format = "png"
    image_info = _write_plot_image(image_bytes, image_format)
    image_path = image_info["image_path"]
    latest_path = image_info["latest_path"]
    latest_html = image_info["latest_html"]
    fallback_text = (
        f"\n\nSaved image: {image_path}"
        f"\nLatest image: {latest_path}"
        f"\nLatest viewer: {latest_html}"
    )
    if os.getenv("PLOT_MCP_IMAGE_FALLBACK", "0") == "1":
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/{image_format};base64,{encoded}"
        if _should_embed_image(image_bytes):
            fallback_text += f"\n\nEmbedded image (data URL):\n![plot]({data_url})"
        else:
            fallback_text += "\n\nEmbedded image omitted (too large)."

    message = f"Plot generated successfully.{warning_text}{fallback_text}\n\n```python\n{code}\n```"
    return [message, Image(data=image_bytes, format=image_format)]


if __name__ == "__main__":
    transport = _select_transport()

    if transport != "stdio":
        selected_port = _choose_available_port(FASTMCP_HOST, FASTMCP_PORT)
        mcp.settings.port = selected_port
        FASTMCP_PORT = selected_port

    if sys.stdin.isatty() and sys.stdout.isatty():
        _write_startup_hint(transport, host=FASTMCP_HOST, port=FASTMCP_PORT)
    mcp.run(transport=transport)
