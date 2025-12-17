# Model Context Protocol (MCP) Integration

This document explains how to integrate Plot MCP with Model Context Protocol (MCP) clients (like Claude Desktop or other AI agents).

## Overview

You can expose the Plot MCP functionality as an MCP Server. This allows any MCP-compliant LLM interface to directly interact with your plotting engine.

## Tool Definitions

To integrate, using an MCP SDK, you would expose the following tools:

### 1. `plot_data`
Accepts raw text data and a plot description.
- **Arguments**:
  - `data` (string): The raw CSV/JSON/Space-separated data.
  - `instruction` (string): What plot to create (e.g., "Scatter plot of x vs y").

### 2. `describe_data`
Analyzes a dataset and returns column info.
- **Arguments**:
  - `data` (string): The raw data.

## Implementation Example

You can run a standalone MCP server using the `mcp` python SDK that wraps this project's logic.

Create a file `mcp_server.py` in the root:

```python
from mcp.server.fastmcp import FastMCP
from backend.data_manager import DataManager
from backend.llm_service import LLMService
from backend.plot_engine import PlotEngine
import asyncio

mcp = FastMCP("PlotMCP")
data_manager = DataManager()
llm_service = LLMService()
plot_engine = PlotEngine()

@mcp.tool()
async def generate_plot_from_text(data_text: str, instruction: str) -> str:
    """Generates a plot from provided text data and returns the image as base64."""
    # 1. Save Data
    file_path = await data_manager.save_text_data(data_text, "mcp_temp.csv")
    
    # 2. Analyze
    context = data_manager.get_data_context(file_path)
    
    # 3. Generate Code
    result = await llm_service.process_query(instruction, context=context)
    if result['type'] != 'plot_code':
        return f"Error or Text Response: {result['text']}"
    
    # 4. Execute
    plot_result = plot_engine.execute_code(result['code'], file_path)
    if plot_result.get('error'):
        return f"Error executing plot: {plot_result['error_message']}"
        
    return f"Plot Generated! Base64 Image: {plot_result['image'][:50]}..."

if __name__ == "__main__":
    mcp.run()
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
