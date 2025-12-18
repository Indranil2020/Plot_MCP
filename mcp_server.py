"""Standalone MCP server for Plot MCP."""

from __future__ import annotations

import uuid
from typing import Dict, Optional

from mcp.server.fastmcp import FastMCP

from backend.data_manager import DataManager
from backend.data_validator import get_validator
from backend.llm_service import LLMService
from backend.plot_engine import PlotEngine

mcp = FastMCP("PlotMCP")

DATA_MANAGER = DataManager()
LLM_SERVICE = LLMService()
PLOT_ENGINE = PlotEngine()


def _build_filename(format_type: str) -> str:
    extension = "csv" if format_type == "csv" else "json"
    return f"mcp_{uuid.uuid4().hex}.{extension}"


@mcp.tool()
async def describe_data(data: str, format: str = "csv") -> Dict[str, object]:
    """Analyze a dataset and return summary plus preview rows."""
    filename = _build_filename(format)
    file_path = await DATA_MANAGER.save_text_data(data, filename)
    df = DATA_MANAGER.load_data(file_path)
    validator = get_validator()
    analysis = validator.analyze_data(df)
    analysis["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    preview = df.head(10).to_dict(orient="records")
    return {"analysis": analysis, "preview": preview}


@mcp.tool()
async def plot_data(
    data: str,
    instruction: str,
    format: str = "csv",
    provider: str = "ollama",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, object]:
    """Generate a plot from raw data and a natural-language instruction."""
    filename = _build_filename(format)
    file_path = await DATA_MANAGER.save_text_data(data, filename)
    df = DATA_MANAGER.load_data(file_path)
    validator = get_validator()
    analysis = validator.analyze_data(df)

    LLM_SERVICE.set_provider(provider, api_key, model)
    response = await LLM_SERVICE.process_query(
        query=instruction,
        context=DATA_MANAGER.get_data_context(file_path),
        data_analysis=analysis,
    )

    if response.get("type") == "clarify":
        return {"type": "clarify", "message": response.get("text", "")}

    if response.get("type") != "plot_code":
        return {"type": "text", "message": response.get("text", "")}

    plot_result = PLOT_ENGINE.execute_code(response["code"], file_path)
    if plot_result.get("error"):
        return {
            "type": "error",
            "message": plot_result.get("error_message", "Plot execution failed"),
            "warnings": plot_result.get("warnings", []),
        }

    return {
        "type": "plot",
        "image": plot_result.get("image"),
        "metadata": plot_result.get("metadata", []),
        "code": response.get("code", ""),
        "warnings": plot_result.get("warnings", []),
    }


if __name__ == "__main__":
    mcp.run()
