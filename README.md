# Plot MCP

## Overview

Plot MCP is a comprehensive plotting system that integrates Matplotlib with logical capabilities using Large Language Models (LLMs). It allows users to generate high-quality, publication-ready plots through natural language requests. The system features an intelligent backend that understands data structures and plotting requirements, coupled with a web-based frontend for interactive visualization.

## Features

- **Natural Language Plotting**: Generate complex Python plotting code from simple text descriptions.
- **Intelligent Data Parsing**: Automatically detects delimiters (CSV, TSV, space-separated) and analyzes data structures.
- **Projects (Origin-style)**: Each project is a folder with a `project.json` manifest (datasets, plot history, UI state).
- **Threaded Chat Sessions**: Multiple chat threads with persistent message history and per-session plot context.
- **Publication Quality (Optional)**: Enable consistent styling defaults for academic plots via the sandbox runner.
- **Interactive Editing**: Click on plot elements (titles, axis labels) to edit them using natural language.
- **Code-First Reproducibility**: Edit plot code and re-execute deterministically (no LLM rewrite) via `/execute_plot`.
- **Gallery Integration**: Browse 500+ official Matplotlib examples and adapt them to your data.
- **Local Execution**: Run entirely locally using Ollama, or connect to cloud providers like OpenAI or Gemini.
- **Flexible Export**: Download plots in PNG, PDF, or SVG formats with custom DPI settings.
- **Safe Execution**: Plot code runs in a sandboxed subprocess with static lint checks (no file/network access).
- **MCP Server**: Use Plot MCP as a standalone MCP server for any MCP-compatible LLM client.

## Prerequisites

- Python 3.9+ (required for `ast.unparse`)
- Node.js and npm (for frontend)
- Ollama (for local LLM support)

## Installation

1.  Clone the repository.
2.  Install Python dependencies:
    ```bash
    python3 -m pip install -r requirements.txt
    ```
3.  Install Frontend dependencies:
    ```bash
    cd frontend
    npm install
    cd ..
    ```

## Usage

### Starting the Application

1.  Start the Backend Server:
    ```bash
    python3 backend/main.py
    ```
    The backend runs on port 8000.

2.  Start the Frontend Interface:
    ```bash
    cd frontend
    npm start
    ```
    The application will be accessible at the Vite dev server URL (usually `http://localhost:5173`).

### Using the Interface

1.  **Create a project**: Use the left sidebar to create/select a project.
2.  **Add data**: Upload files or paste data into the project.
3.  **Select files**: Check one or more files to use as plot context.
4.  **Describe plot**: Ask for a plot in chat (e.g., "Scatter plot of A vs B").
5.  **Refine**: Click plot elements (title/labels) to request edits, or edit code and re-run directly.
6.  **Tools drawer**: Use the plot toolbar `Tools` to open Preview / Join / Analysis / Gallery.

## Environment Configuration

- **Backend port**: set `PORT=8001` before running `python3 backend/main.py` if 8000 is in use.
- **Frontend API URL**: set `VITE_API_URL` (see `frontend/.env.example`) to point to the backend.
- **Port auto-release**: backend attempts to terminate processes on the chosen port using `lsof` or `fuser` before binding.
- **Sandbox memory**: set `PLOT_EXEC_MEMORY_MB=1024` to enforce a memory cap; default is no limit.
- **Sandbox style**: set `PLOT_ENFORCE_STYLE=1` to apply consistent styling defaults (fonts/ticks/spines).
- **Gallery prompt grounding (RAG)**: set `PLOT_GALLERY_RAG_MODE=off` to disable injecting the closest Matplotlib gallery snippets into the LLM prompt (default: enabled).
- **Deterministic templates**: set `PLOT_TEMPLATE_MODE=on` to enable built-in template plots (waves, etc.) as an optional fallback (default: disabled / LLM-only).
- **Projects directory**: set `PROJECTS_DIR=/path/to/projects` to store projects outside the repo.

## Happy Path Tutorial (End-to-End)

1.  **Create a project**: In the left sidebar, create a project named `My Experiment`.
2.  **Upload files**: Upload `data_a.csv` and `data_b.csv` into the project.
3.  **Select files**: Check both files in the project explorer.
4.  **Open Tools → Preview**: Inspect a file preview and inferred dtypes.
5.  **Open Tools → Join**: Review join suggestions (shared columns and warnings) before plotting.
6.  **Ask for a plot**: Example request: `Plot temperature from data_a vs pressure from data_b`.
7.  **Iterate**: Click the plot title/labels to refine the output using natural language.
8.  **History & undo**: Use thumbnails or undo/redo to revisit earlier plots.
9.  **Download**: Export a high-resolution image (PNG/PDF/SVG).

## Configuration

The system uses `Ollama` with the `llama3` model by default. To use a lightweight model for low-resource environments:

1.  Pull the model:
    ```bash
    ollama pull qwen2:0.5b
    ```
2.  Set the environment variable before running the backend:
    ```bash
    export OLLAMA_MODEL=qwen2:0.5b
    python3 backend/main.py
    ```

See `doc/` folder for advanced configuration and Model Context Protocol (MCP) integration.

## Documentation

- **Architecture**: See `doc/ARCHITECTURE.md` for system design diagrams.
- **MCP Integration**: See `doc/MCP_INTEGRATION.md` for connecting to generic LLM clients.
- **Tiny Models**: See `doc/TINY_LLM_SETUP.md` for running with small local LLMs.
