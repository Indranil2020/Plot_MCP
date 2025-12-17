from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
import csv
import io
import re
import pandas as pd

from llm_service import LLMService
from plot_engine import PlotEngine
from data_manager import DataManager
from data_validator import get_validator
from intelligent_assistant import get_intelligent_assistant
import re

app = FastAPI(title="Local Matplotlib LLM Plotter")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
plot_engine = PlotEngine()
data_manager = DataManager()

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    current_code: Optional[str] = None
    provider: Optional[str] = "ollama"
    api_key: Optional[str] = None
    model: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Welcome to Local Matplotlib LLM Plotter API"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = await data_manager.save_file(file)
    preview = data_manager.get_preview(file_path)
    
    # Analyze data structure and suggest plots
    validator = get_validator()
    df = data_manager.load_data(file_path)
    analysis = validator.analyze_data(df)
    
    return {
        "path": file_path,
        "preview": preview,
        "analysis": {
            "shape": analysis["shape"],
            "columns": analysis["columns"],
            "numeric_cols": analysis["numeric_cols"],
            "categorical_cols": analysis["categorical_cols"],
            "datetime_cols": analysis["datetime_cols"],
            "suggested_plots": analysis["suggested_plots"],
            "warnings": analysis["warnings"]
        }
    }

@app.post("/paste_data")
async def paste_data(request: dict):
    """Handle pasted data (CSV or JSON) with intelligent delimiter detection"""
    data_content = request.get("data")
    format_type = request.get("format", "csv")
    
    if not data_content:
        raise HTTPException(status_code=400, detail="No data provided")
    
    # Try to intelligently detect the delimiter for CSV-like data
    if format_type == "csv":
        import csv
        import io
        
        # Try different delimiters manually without Sniffer (to avoid try-except)
        delimiters = [',', '\t', ' ', ';', '|']
        best_delimiter = ','
        max_columns = 0
        
        # Manual Consistent Check
        lines = data_content.strip().split('\n')
        # Use first 5 lines
        check_lines = lines[:5] if len(lines) > 5 else lines
        
        if len(check_lines) > 0:
            for delim in delimiters:
                # Check column count of first line
                first_line_cols = len(check_lines[0].split(delim))
                
                # Must have more than 1 column to be a delimiter
                if first_line_cols > 1:
                    # Check consistency
                    consistent = True
                    for line in check_lines:
                        if not line.strip():
                            continue
                        if len(line.split(delim)) != first_line_cols:
                            consistent = False
                            break
                    
                    if consistent and first_line_cols > max_columns:
                        max_columns = first_line_cols
                        best_delimiter = delim
        
        # If space-separated, handle multiple spaces as single delimiter
        if best_delimiter == ' ':
            # Convert multiple spaces to single delimiter
            import re
            lines = data_content.strip().split('\n')
            cleaned_lines = []
            for line in lines:
                # Replace multiple spaces with comma
                cleaned_line = re.sub(r'\s+', ',', line.strip())
                cleaned_lines.append(cleaned_line)
            data_content = '\n'.join(cleaned_lines)
            best_delimiter = ','
        
        # Save with detected delimiter info
        filename = f"pasted_data_{format_type}.{format_type}"
        file_path = await data_manager.save_text_data(data_content, filename)
        
        # Load directly. If it fails, it fails (User rule: no try-except)
        df = pd.read_csv(io.StringIO(data_content), sep=best_delimiter)
    else:
        # JSON format
        filename = f"pasted_data_{format_type}.{format_type}"
        file_path = await data_manager.save_text_data(data_content, filename)
        df = pd.read_json(io.StringIO(data_content))
    
    # Analyze the parsed data
    validator = get_validator()
    analysis = validator.analyze_data(df)
    
    preview = data_manager.get_preview(file_path)
    
    # Add parsing info to response
    parsing_info = {
        "detected_delimiter": best_delimiter if format_type == "csv" else "N/A",
        "rows_parsed": len(df),
        "columns_parsed": len(df.columns),
        "column_names": list(df.columns),
        "sample_data": df.head(3).to_dict(orient='records')
    }
    
    return {
        "path": file_path,
        "preview": preview,
        "parsing_info": parsing_info,
        "analysis": {
            "shape": analysis["shape"],
            "columns": analysis["columns"],
            "numeric_cols": analysis["numeric_cols"],
            "categorical_cols": analysis["categorical_cols"],
            "datetime_cols": analysis["datetime_cols"],
            "suggested_plots": analysis["suggested_plots"],
            "warnings": analysis["warnings"]
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    # Configure LLM Provider
    # Proactive check instead of try-except
    if request.provider == "gemini" and not request.api_key:
        return {"response": "API Key required for Gemini", "type": "error"}
    if request.provider == "openai" and not request.api_key:
        return {"response": "API Key required for OpenAI", "type": "error"}
        
    llm_service.set_provider(request.provider, request.api_key, request.model)

    # Get data context if a file path is provided
    data_context = ""
    data_analysis = None
    if request.context:
        data_context = data_manager.get_data_context(request.context)
        # Get data analysis for intelligent suggestions
        # Assume valid file if context path exists
        if os.path.exists(request.context):
            validator = get_validator()
            df = data_manager.load_data(request.context)
            data_analysis = validator.analyze_data(df)
    
    # Analyze URLs in the message
    url_analysis = None
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(request.message)
    if urls:
        assistant = get_intelligent_assistant()
        url_analysis = assistant.analyze_url(urls[0])

    # Process query with LLM
    response = await llm_service.process_query(
        query=request.message, 
        context=data_context,
        current_code=request.current_code,
        data_analysis=data_analysis,
        url_analysis=url_analysis
    )
    
    if response.get("type") == "plot_code":
        # Execute the generated code
        plot_result = plot_engine.execute_code(response["code"], request.context)
        
        if plot_result:
            # Check if there was an error during execution
            if plot_result.get("error"):
                return {
                    "response": f"❌ Plot execution failed: {plot_result['error_message']}\n\nPlease check your data or try a different plot type.",
                    "code": response["code"],
                    "error": True,
                    "error_details": plot_result.get("traceback", "")
                }
            
            return {
                "response": response.get("text", "Here is the plot you requested."),
                "plot": plot_result["image"],
                "metadata": plot_result["metadata"],
                "code": response["code"]
            }
        else:
            return {
                "response": "❌ Failed to execute the plot code. The code was generated but couldn't be executed.",
                "code": response["code"],
                "error": True
            }
    elif response.get("type") == "error":
        return {
            "response": response.get("text", "I couldn't generate a plot from your request."),
            "type": "text"
        }
    else:
        return {"response": response["text"]}

@app.post("/validate")
async def validate_plot_type(plot_type: str, file_path: str):
    """Validate if data is suitable for a specific plot type"""
    validator = get_validator()
    df = data_manager.load_data(file_path)
    is_valid, message = validator.validate_for_plot_type(df, plot_type)
    
    if not is_valid:
        suggestion = validator.suggest_data_transformation(df, plot_type)
        schema = validator.get_plot_schema(plot_type)
        return {
            "valid": False,
            "message": message,
            "suggestion": suggestion,
            "schema": schema
        }
    
    return {
        "valid": True,
        "message": message
    }

class DownloadRequest(BaseModel):
    code: str
    context: Optional[str] = None
    format: str = "png"
    dpi: int = 300

@app.post("/download_plot")
async def download_plot(request: DownloadRequest):
    # Execute code with specific format and DPI
    result = plot_engine.execute_code(
        request.code, 
        request.context, 
        dpi=request.dpi, 
        format=request.format
    )
    
    if not result or "buffer" not in result:
        raise HTTPException(status_code=500, detail="Failed to generate plot")
        
    # Return as streaming response
    buffer = result["buffer"]
    buffer.seek(0)
    
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml"
    }
    
    return StreamingResponse(
        buffer, 
        media_type=media_types.get(request.format, "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename=plot.{request.format}"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
