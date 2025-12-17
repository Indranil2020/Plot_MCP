# Tiny LLM Setup for Local Execution

This guide explains how to run Plot MCP entirely locally on consumer hardware (CPU only) using specialized "tiny" Large Language Models.

## Why Tiny Models?

Modern quantized models (like Qwen2-0.5B or Phi-3-Mini) are incredibly efficient. They can run on:
- Laptops with no dedicated GPU
- 4GB-8GB RAM systems
- Fast inference speeds (low latency)

## Recommended Models

We recommend the following models for this application:

| Model | Size | RAM Req | Speed |
|-------|------|---------|-------|
| `qwen2:0.5b` | 0.5B Params | < 1GB | Ultra Fast |
| `qwen2:1.5b` | 1.5B Params | ~1.5GB | Very Fast |
| `phi3` | 3.8B Params | ~4GB | Balanced |
| `llama3.2:1b` | 1B Params | ~1.5GB | Fast |

## Setup Instructions

### 1. Install Ollama

If you haven't already, install Ollama from [ollama.com](https://ollama.com).

### 2. Pull a Tiny Model

Open your terminal and pull one of the recommended models:

```bash
# Recommended for absolute lowest resource usage
ollama pull qwen2:0.5b

# Recommended for better reasoning
ollama pull llama3.2:1b
```

### 3. Configure Plot MCP

You can tell the application which model to use by setting an environment variable.

#### On Linux/Mac:
```bash
export OLLAMA_MODEL=qwen2:0.5b
python3 backend/main.py
```

#### On Windows (PowerShell):
```powershell
$env:OLLAMA_MODEL = "qwen2:0.5b"
python3 backend\main.py
```

## Performance Tips

- **Quantization**: Ollama automatically uses 4-bit quantization, which reduces memory usage by 75% compared to full models.
- **Context Window**: For tiny models, keep your data paste size reasonable (under 100 rows preview) to avoid overflowing the context.
