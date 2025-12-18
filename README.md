# Plot MCP

## Overview

Plot MCP is a comprehensive plotting system that integrates Matplotlib with logical capabilities using Large Language Models (LLMs). It allows users to generate high-quality, publication-ready plots through natural language requests. The system features an intelligent backend that understands data structures and plotting requirements, coupled with a web-based frontend for interactive visualization.

## Features

- **Natural Language Plotting**: Generate complex Python plotting code from simple text descriptions.
- **Intelligent Data Parsing**: Automatically detects delimiters (CSV, TSV, space-separated) and analyzes data structures.
- **Publication Quality**: Default settings ensure plots meet academic publication standards (fonts, ticks, line widths).
- **Interactive Editing**: Click on plot elements (titles, axis labels) to edit them using natural language.
- **Gallery Integration**: Access over 500 official Matplotlib examples.
- **Local Execution**: Run entirely locally using Ollama, or connect to cloud providers like OpenAI or Gemini.
- **Flexible Export**: Download plots in PNG, PDF, or SVG formats with custom DPI settings.

## Prerequisites

- Python 3.8+
- Node.js and npm (for frontend)
- Ollama (for local LLM support)

## Installation

1.  Clone the repository.
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
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
    The application will be accessible at http://localhost:3000.

### Using the Interface

1.  **Paste Data**: Click "Paste Data" to input your dataset (CSV, JSON, or space-separated text).
2.  **Describe Plot**: Type your request in the chat (e.g., "Create a scatter plot of column A vs B").
3.  **Edit**: Click on the generated plot title or axes to request modification.
4.  **Download**: Use the download menu to save your plot in high resolution.

## Environment Configuration

- **Backend port**: set `PORT=8001` before running `python3 backend/main.py` if 8000 is in use.
- **Frontend API URL**: set `VITE_API_URL` (see `frontend/.env.example`) to point to the backend.
- **Port auto-release**: backend attempts to terminate processes on the chosen port using `lsof` or `fuser` before binding.
- **Sandbox memory**: set `PLOT_EXEC_MEMORY_MB=1024` to enforce a memory cap; default is no limit.

## Happy Path Tutorial (End-to-End)

1.  **Create a project**: In the left sidebar, create a project named `My Experiment`.
2.  **Upload files**: Upload `data_a.csv` and `data_b.csv` into the project.
3.  **Select files**: Check both files in the project explorer.
4.  **Review preview**: Inspect the data preview and type summary at the top of the main panel.
5.  **Join guidance**: Review join suggestions (shared columns and warnings) before plotting.
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
- **Production Setup**: See `doc/QUICKSTART_PROD.md` for standalone deployment instructions.
