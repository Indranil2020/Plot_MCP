# Model Context Protocol (MCP) Integration

Use Plot MCP from any MCP-capable client (Claude Desktop, Windsurf-style agents, custom tooling) without opening the web UI.

## Quickstart (3 steps)

1) **Install deps**
```bash
python3 -m pip install -r requirements.txt
# or repo-local
python3 -m pip install --target vendor -r requirements.txt
```
2) **Run the MCP server**
```bash
# auto-selects stdio when launched by a client, HTTP when run in a TTY
python3 mcp_server.py
```
3) **Point your client to it** (examples below).

## Tool Surface

- `plot_data`  
  - Args: `data` (string), `instruction` (string), `format` (`csv`|`json`), `provider` (`ollama|openai|gemini`), `api_key`, `model`.  
  - Returns: text block (code + warnings + saved image path) and PNG image block on success.
- `describe_data`  
  - Args: `data` (string), `format` (`csv`|`json`).  
  - Returns: `analysis` (columns, inferred types, suggested plots, warnings) + `preview` (first rows).

## Transports

- Default: `auto` → stdio when client-launched, `streamable-http` when run in a terminal.
- Force mode:
```bash
PLOT_MCP_TRANSPORT=stdio python3 mcp_server.py
PLOT_MCP_TRANSPORT=streamable-http FASTMCP_PORT=8765 python3 mcp_server.py
```
- HTTP endpoints (when in HTTP mode):
  - `/mcp` for MCP messages
  - `/sse` and `/messages/` for SSE transport

## Client Recipes

### Claude Desktop
Edit `~/.config/Claude/claude_desktop_config.json` (path may vary):
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
Restart Claude Desktop, open a chat, and call tools.

### Gemini CLI (gcloud genai)
Run the server over HTTP:
```bash
PLOT_MCP_TRANSPORT=streamable-http FASTMCP_PORT=8765 python3 mcp_server.py
```
Then configure your client to post MCP JSON-RPC to `http://127.0.0.1:8765/mcp`.

### OpenAI-compatible agents
Use HTTP transport and point the agent’s MCP client to the `/mcp` endpoint as above.

## Reliability and Safety

- Guardrails: AST lint (blocks imports/calls, ellipsis placeholders), import stripping, sandboxed execution (no file/network access), timeouts, optional memory cap.
- Clarifications: `plot_data` may return `type: clarify`; answer and call again.
- Deterministic code-path: for “run this code exactly” behavior, use the web backend `POST /execute_plot` or add an MCP `execute_plot` tool if needed.

## Environment Variables (server)

- `OLLAMA_MODEL` – default local model (e.g., `llama3`, `qwen2:0.5b`).
- `PLOT_GALLERY_RAG_MODE` – `off` to disable gallery grounding (default on).
- `PLOT_TEMPLATE_MODE` – `on` to enable deterministic templates for data-free requests.
- `PLOT_EXEC_MEMORY_MB` – sandbox memory limit (0 = no limit).
- `PLOT_ENFORCE_STYLE` – `1` to apply consistent Matplotlib styling in the sandbox.
- `PLOT_MCP_TRANSPORT` – `auto` | `stdio` | `sse` | `streamable-http`.
- `FASTMCP_HOST`, `FASTMCP_PORT` – host/port for HTTP transports.
- `PLOT_MCP_OUTPUT_DIR` – directory for saved plot images (default `mcp_outputs`).
- `PLOT_MCP_IMAGE_FALLBACK` – `1` to include a data URL in the text block for clients that cannot render images.

## Troubleshooting

- “Invalid JSON” when typing in the terminal: stdio MCP servers are not interactive; let the MCP client handle IO, or force HTTP mode for manual testing.
- Missing deps: install via `python3 -m pip install -r requirements.txt` or `--target vendor`.
- Plot fails: check lint errors in the returned text block; disallowed imports/calls are blocked before execution.
- Image not shown in chat: open the saved file path from the tool output, or enable `PLOT_MCP_IMAGE_FALLBACK=1`.
