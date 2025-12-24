# Plot MCP - Beginner Guide (Step by Step)

Use this if you are new to MCP and just want the plotting server running with any MCP-capable chat app (Claude Desktop, Windsurf-like agents, custom MCP clients).

## 0) What you need
- Python 3.10+
- `pip`
- An MCP-capable client (examples below)

## 1) Install dependencies
```bash
python3 -m pip install -r requirements.txt
# If you cannot install globally:
python3 -m pip install --target vendor -r requirements.txt
```

## 2) Start the MCP server
```bash
python3 mcp_server.py
```
- Default behavior:
  - If launched by an MCP client: stdio transport
  - If run in a terminal (TTY): streamable HTTP on `127.0.0.1:8765/mcp`
- Force a mode:
```bash
PLOT_MCP_TRANSPORT=stdio python3 mcp_server.py
PLOT_MCP_TRANSPORT=streamable-http FASTMCP_PORT=8765 python3 mcp_server.py
```

## 3) Connect from Claude Desktop
1. Open `~/.config/Claude/claude_desktop_config.json` (path may differ by OS).
2. Add:
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
3. Restart Claude Desktop. In a chat, call tools (e.g., ask for a plot).

## 4) Connect from Windsurf-style or other MCP clients
- If the client supports stdio MCP: point it to `python3 /path/to/Plot_MCP/mcp_server.py`.
- If the client prefers HTTP MCP:
  - Start server in HTTP mode (see step 2).
  - Point the client to `http://127.0.0.1:8765/mcp` (or your chosen host/port).

## 5) Quick tool reference
- `describe_data`:
  - Args: `data` (string), `format` (`csv` or `json`)
  - Returns: column info, inferred types, suggested plots, preview rows
- `plot_data`:
  - Args: `data`, `instruction`, `format` (`csv`|`json`), optional `provider` (`ollama|openai|gemini`), `api_key`, `model`
  - Returns: text block (code + warnings + saved image path) and PNG image block

## 6) Environment knobs (common)
- `PLOT_MCP_TRANSPORT`: `auto` (default) | `stdio` | `sse` | `streamable-http`
- `FASTMCP_PORT`: HTTP/SSE port (default 8765)
- `OLLAMA_MODEL`: default local model (e.g., `llama3`, `qwen2:0.5b`)
- `PLOT_GALLERY_RAG_MODE`: `off` to disable gallery grounding (default on)
- `PLOT_TEMPLATE_MODE`: `on` for deterministic templates when no data is provided
- `PLOT_MCP_OUTPUT_DIR`: directory for saved plot images (default `mcp_outputs`)
- `PLOT_MCP_IMAGE_FALLBACK`: `1` to include a data URL in the text block

## 7) Sanity check (HTTP mode)
If running in HTTP mode, you can probe the MCP endpoint:
```bash
curl -X POST http://127.0.0.1:8765/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
```
You should see a JSON response with `serverInfo.name = "PlotMCP"`.

## 8) Troubleshooting
- “Invalid JSON” when typing in the terminal: stdio MCP servers are not interactive; let the MCP client handle IO or use HTTP mode for manual testing.
- Missing dependencies: install with `pip install -r requirements.txt` (or `--target vendor`).
- Plot errors: check the returned text block for lint errors (disallowed imports, ellipsis placeholders). Fix and call again.
- Image not shown in chat: open the saved image path from the tool output or enable `PLOT_MCP_IMAGE_FALLBACK=1`.
