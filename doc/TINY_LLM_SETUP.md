# Tiny LLM Setup (Local, CPU-Friendly)

Run Plot MCP fully local with small models on modest hardware.

## Pick a Tiny Model

| Model | Size | RAM | Notes |
|-------|------|-----|-------|
| `qwen2:0.5b` | 0.5B | <1 GB | Fastest, lowest memory |
| `llama3.2:1b` | 1B | ~1.5 GB | Better reasoning, still light |
| `qwen2:1.5b` | 1.5B | ~1.5 GB | Balanced |
| `phi3` | 3.8B | ~4 GB | Higher quality, slower |

## Steps

1) Install Ollama (https://ollama.com).  
2) Pull a tiny model:
```bash
ollama pull qwen2:0.5b          # minimal
ollama pull llama3.2:1b         # better reasoning
```
3) Point Plot MCP to the model:
```bash
export OLLAMA_MODEL=qwen2:0.5b   # Linux/Mac
python3 backend/main.py
```
PowerShell:
```powershell
$env:OLLAMA_MODEL = "qwen2:0.5b"
python3 backend\main.py
```

## Using the Full UI

```bash
python3 backend/main.py
cd frontend
npm start
```
Frontend runs on `http://localhost:5173`, backend on `http://0.0.0.0:8000`.

## Tips for Tiny Models

- Prefer selecting files in a project; backend sends compact summaries instead of full data.
- If asked a clarification (e.g., columns to plot), answer in the same session so context is preserved.
- To force deterministic templates for data-free requests, set `PLOT_TEMPLATE_MODE=on`.
- Keep pasted data small (<100 rows preview) to stay within context.
- Ollama uses 4-bit quantization automatically; no extra tuning required.
