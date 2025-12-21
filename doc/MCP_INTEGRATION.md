# Model Context Protocol (MCP) Integration

This document explains how to integrate Plot MCP with Model Context Protocol (MCP) clients (like Claude Desktop or other AI agents).

## Overview

MCP is a tool protocol: an MCP-capable LLM client connects to an MCP server over stdio and calls tools. Plot MCP includes a standalone MCP server so you can use the plotting engine from **any** MCP-compatible chat UI (Claude Desktop, Windsurf-style agents, custom clients, etc.) without using the web frontend.

Plot MCP supports two usage modes:

1. **Web app** (`backend/main.py` + `frontend/`): projects, multi-file selection, plot history, sessions, UI tools.
2. **Standalone MCP server** (`mcp_server.py`): exposes a small set of plotting tools over MCP stdio (single dataset per call today).

## Tool Definitions

The repository ships with a ready-to-run MCP server (`mcp_server.py`) that exposes:

### 1. `plot_data`
Accepts raw text data and a plot description.
- **Arguments**:
  - `data` (string): The raw CSV/JSON/space-separated data.
  - `instruction` (string): What plot to create (e.g., "Scatter plot of x vs y").
  - `format` (string, optional): `csv` or `json`.
  - `provider` (string, optional): `ollama`, `openai`, or `gemini`.
  - `api_key` (string, optional): API key for cloud providers.
  - `model` (string, optional): model name override.
- **Returns**:
  - Unstructured MCP content blocks:
    - A text block with the generated Python code (and any warnings)
    - An image block (PNG) when a plot is successfully generated

### 2. `describe_data`
Analyzes a dataset and returns column info.
- **Arguments**:
  - `data` (string): The raw data.
  - `format` (string, optional): `csv` or `json`.
- **Returns**:
  - `analysis`: columns, inferred types, suggested plots, warnings
  - `preview`: first rows

## Running the MCP Server

Install Python dependencies (including the `mcp` package):

```bash
python3 -m pip install -r requirements.txt
```

If you cannot (or do not want to) install to your user/site packages, you can install into the repo and the server will pick it up automatically:

```bash
python3 -m pip install --target vendor -r requirements.txt
```

```bash
python3 mcp_server.py
```

### Note on “Invalid JSON” errors

MCP stdio servers are **not interactive CLIs**. If you run a stdio MCP server directly in a terminal and type random text (or press Enter), you may see JSON-RPC parsing errors like “Invalid JSON”.

`mcp_server.py` defaults to:
- `stdio` when launched by an MCP client (Claude Desktop, etc.)
- `streamable-http` when run from a terminal (TTY) for easier manual testing

You can force a specific mode with `PLOT_MCP_TRANSPORT`:

```bash
# Force stdio (for MCP clients that launch the process)
PLOT_MCP_TRANSPORT=stdio python3 mcp_server.py

# Run as an HTTP MCP server (manual testing / HTTP-capable clients)
PLOT_MCP_TRANSPORT=streamable-http FASTMCP_PORT=8765 python3 mcp_server.py
```

## Reliability Notes

- `plot_data` uses an LLM to generate Matplotlib code. Reliability is improved by deterministic guardrails:
  - AST linting and import stripping
  - sandboxed execution (no file/network access)
  - structured dataset context and column summaries
- If the tool returns `type: clarify`, respond with the missing details and call `plot_data` again.
- If you want deterministic “run this code exactly” behavior (no LLM rewrite), use the web backend endpoint `POST /execute_plot` or extend the MCP server with an `execute_plot` tool.

## connecting to Claude Desktop

1.  Locate your Claude Desktop config (Linux is typically `~/.config/Claude/claude_desktop_config.json`).
2.  Add the MCP server configuration and restart Claude Desktop:
    ```json
    {
      "mcpServers": {
        "plot-mcp": {
          "command": "python3",
          "args": ["/path/to/Plot_MCP/mcp_server.py"]
        }
      }
    }
    ```

## Environment Variables (Server-Side)

- `OLLAMA_MODEL`: default local model name for Ollama (e.g., `llama3`, `qwen2:0.5b`)
- `PLOT_GALLERY_RAG_MODE`: set to `off` to disable injecting closest Matplotlib gallery snippets into the LLM prompt (default: enabled)
- `PLOT_EXEC_MEMORY_MB`: optional sandbox memory limit (0 = no limit)
- `PLOT_ENFORCE_STYLE`: set to `1` to enforce consistent matplotlib styling defaults in the sandbox
- `PLOT_TEMPLATE_MODE`: set to `on` to enable built-in deterministic templates for data-free requests (default: disabled / LLM-only)
- `PLOT_MCP_TRANSPORT`: `auto` (default), `stdio`, `sse`, or `streamable-http`
- `FASTMCP_HOST`: host for HTTP transports (default `127.0.0.1`)
- `FASTMCP_PORT`: port for HTTP transports (default `8765`)
