# Model Context Protocol (MCP) Integration

This document explains how to integrate Plot MCP with Model Context Protocol (MCP) clients (like Claude Desktop or other AI agents).

## Overview

You can expose the Plot MCP functionality as an MCP Server. This allows any MCP-compliant LLM interface to directly interact with your plotting engine.

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

### 2. `describe_data`
Analyzes a dataset and returns column info.
- **Arguments**:
  - `data` (string): The raw data.
  - `format` (string, optional): `csv` or `json`.

## Running the MCP Server

```bash
python3 mcp_server.py
```

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
