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
  - `type`: `plot` | `clarify` | `text` | `error`
  - When `type == plot`: `image` (base64 png), `code` (python), optional `metadata`, optional `warnings`
  - When `type == clarify`: `message` describing what to answer next

### 2. `describe_data`
Analyzes a dataset and returns column info.
- **Arguments**:
  - `data` (string): The raw data.
  - `format` (string, optional): `csv` or `json`.
- **Returns**:
  - `analysis`: columns, inferred types, suggested plots, warnings
  - `preview`: first rows

## Running the MCP Server

```bash
python3 mcp_server.py
```

## Reliability Notes

- `plot_data` uses an LLM to generate Matplotlib code. Reliability is improved by deterministic guardrails:
  - AST linting and import stripping
  - sandboxed execution (no file/network access)
  - structured dataset context and column summaries
- If the tool returns `type: clarify`, respond with the missing details and call `plot_data` again.
- If you want deterministic “run this code exactly” behavior (no LLM rewrite), use the web backend endpoint `POST /execute_plot` or extend the MCP server with an `execute_plot` tool.

## connecting to Claude Desktop

1.  Navigate to your Claude Desktop config.
2.  Add the MCP server configuration:
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
- `PLOT_EXEC_MEMORY_MB`: optional sandbox memory limit (0 = no limit)
- `PLOT_ENFORCE_STYLE`: set to `1` to enforce consistent matplotlib styling defaults in the sandbox
