"""FastAPI entrypoint for the Plot MCP backend."""

from __future__ import annotations

import io
import json
import os
import re
import signal
import socket
import subprocess
import shutil
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app_logger import setup_app_logger
from data_manager import DataManager
from data_validator import get_validator
from file_utils import build_alias_map
from gallery_adapters import (
    extract_gallery_example_title,
    generate_gallery_fallback_plot,
    maybe_adapt_gallery_example,
)
from intelligent_assistant import get_intelligent_assistant
from join_assistant import JoinAssistant
from llm_service import LLMService
from plot_storage import create_thumbnail, save_plot_assets
from plot_engine import PlotEngine
from plot_templates import maybe_generate_template_plot
from project_manager import ProjectManager
from project_manifest import ProjectManifestManager
from session_manager import SessionManager
from metrics import MetricsStore

app = FastAPI(title="Local Matplotlib LLM Plotter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()
plot_engine = PlotEngine()
data_manager = DataManager()
project_manager = ProjectManager()
manifest_manager = ProjectManifestManager()
session_manager = SessionManager()
join_assistant = JoinAssistant()
metrics_store = MetricsStore()
app_logger = setup_app_logger()


@app.middleware("http")
async def record_metrics(request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start) * 1000
    metrics_store.record(request.url.path, duration_ms)
    app_logger.info(
        "method=%s path=%s status=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


class ProjectRequest(BaseModel):
    name: str


class SessionCreateRequest(BaseModel):
    title: Optional[str] = None
    project_name: Optional[str] = None


class UIStateUpdate(BaseModel):
    selected_files: Optional[List[str]] = None
    last_session_id: Optional[str] = None
    plot_history_index: Optional[int] = None


class PasteDataRequest(BaseModel):
    data: str
    format: str = "csv"
    project_name: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    selected_files: List[str] = Field(default_factory=list)
    current_code: Optional[str] = None
    provider: str = "ollama"
    api_key: Optional[str] = None
    model: Optional[str] = None
    project_name: Optional[str] = None
    session_id: Optional[str] = None


class DownloadRequest(BaseModel):
    code: str
    context: Optional[str] = None
    selected_files: List[str] = Field(default_factory=list)
    format: str = "png"
    dpi: int = 300


class ExecutePlotRequest(BaseModel):
    code: str
    context: Optional[str] = None
    selected_files: List[str] = Field(default_factory=list)
    format: str = "png"
    dpi: int = 300
    project_name: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None


class JoinRequest(BaseModel):
    selected_files: List[str] = Field(default_factory=list)


class PreviewRequest(BaseModel):
    file_path: str


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to Local Matplotlib LLM Plotter API"}


@app.get("/metrics")
async def get_metrics() -> Dict[str, object]:
    return metrics_store.snapshot()


@app.get("/gallery")
async def get_gallery_kb() -> Dict[str, object]:
    kb_path = os.path.join(os.path.dirname(__file__), "matplotlib_gallery_kb.json")
    if not os.path.isfile(kb_path):
        raise HTTPException(status_code=404, detail="Gallery knowledge base not found")
    with open(kb_path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Invalid gallery knowledge base")
    return data


@app.get("/projects")
async def list_projects() -> Dict[str, List[str]]:
    return {"projects": project_manager.list_projects()}


@app.post("/projects")
async def create_project(request: ProjectRequest) -> Dict[str, str]:
    name = _validate_project_name(request.name)
    if name in project_manager.list_projects():
        raise HTTPException(status_code=400, detail="Project already exists")
    project = project_manager.create_project(name)
    manifest_manager.ensure_manifest(name)
    return project


@app.get("/projects/{name}/files")
async def list_project_files(name: str, recursive: bool = False) -> Dict[str, object]:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    entries = project_manager.list_entries(project_name, include_dirs=True, recursive=recursive)
    manifest = manifest_manager.ensure_manifest(project_name)
    return {
        "files": entries,
        "datasets": manifest.get("datasets", []),
        "plots": manifest.get("plots", []),
        "ui_state": manifest.get("ui_state", {}),
    }


@app.get("/projects/{name}/manifest")
async def get_project_manifest(name: str) -> Dict[str, object]:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    manifest = manifest_manager.ensure_manifest(project_name)
    return {"manifest": manifest}


@app.get("/projects/{name}/plots")
async def get_project_plots(name: str) -> Dict[str, List[Dict[str, object]]]:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    plots = manifest_manager.get_plot_history(project_name)
    return {"plots": plots}


@app.get("/projects/{name}/plots/{plot_id}/image")
async def get_plot_image(name: str, plot_id: str) -> StreamingResponse:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    plot_entry = manifest_manager.get_plot_by_id(project_name, plot_id)
    if not plot_entry:
        raise HTTPException(status_code=404, detail="Plot not found")
    project_path = project_manager.get_project_path(project_name)
    rel_image_path = plot_entry.get("image_path")
    if not isinstance(rel_image_path, str) or not rel_image_path:
        raise HTTPException(status_code=404, detail="Image file not available")
    image_path = os.path.join(project_path, rel_image_path)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    return StreamingResponse(open(image_path, "rb"), media_type="image/png")


@app.get("/projects/{name}/plots/{plot_id}/thumbnail")
async def get_plot_thumbnail(name: str, plot_id: str) -> StreamingResponse:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    plot_entry = manifest_manager.get_plot_by_id(project_name, plot_id)
    if not plot_entry:
        raise HTTPException(status_code=404, detail="Plot not found")
    project_path = project_manager.get_project_path(project_name)
    rel_thumb_path = plot_entry.get("thumbnail_path")
    if not isinstance(rel_thumb_path, str) or not rel_thumb_path:
        rel_image_path = plot_entry.get("image_path")
        if not isinstance(rel_image_path, str) or not rel_image_path:
            raise HTTPException(status_code=404, detail="Thumbnail not available")
        image_path = os.path.join(project_path, rel_image_path)
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")

        rel_thumb_path = f"{os.path.splitext(rel_image_path)[0]}_thumb.png"
        thumbnail_path = os.path.join(project_path, rel_thumb_path)
        if not os.path.isfile(thumbnail_path):
            create_thumbnail(image_path, thumbnail_path)
        manifest_manager.set_plot_thumbnail_path(project_name, plot_id, rel_thumb_path)
    else:
        thumbnail_path = os.path.join(project_path, rel_thumb_path)
    if not os.path.isfile(thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    return StreamingResponse(open(thumbnail_path, "rb"), media_type="image/png")


@app.patch("/projects/{name}/ui_state")
async def update_project_ui_state(name: str, request: UIStateUpdate) -> Dict[str, object]:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        raise HTTPException(status_code=404, detail="Project not found")
    updates = request.model_dump(exclude_none=True)
    ui_state = manifest_manager.update_ui_state(project_name, updates)
    return {"ui_state": ui_state}


@app.post("/projects/{name}/upload")
async def upload_to_project(name: str, file: UploadFile = File(...)) -> Dict[str, object]:
    project_name = _validate_project_name(name)
    if project_name not in project_manager.list_projects():
        project_manager.create_project(project_name)
    manifest_manager.ensure_manifest(project_name)
    project_path = project_manager.get_project_path(project_name)

    file_path = await data_manager.save_file(file, target_dir=project_path)
    preview = data_manager.get_preview(file_path)

    validator = get_validator()
    df = data_manager.load_data(file_path)
    analysis = validator.analyze_data(df)
    dataset = manifest_manager.register_dataset(project_name, file_path)

    return {
        "filename": file.filename,
        "path": os.path.abspath(file_path),
        "preview": preview,
        "analysis": analysis,
        "dataset": dataset,
    }


@app.post("/sessions")
async def create_session(request: SessionCreateRequest) -> Dict[str, object]:
    session = session_manager.create_session(request.title, request.project_name)
    if request.project_name:
        project_name = _validate_project_name(request.project_name)
        if project_name in project_manager.list_projects():
            manifest_manager.update_ui_state(
                project_name, {"last_session_id": session.get("id")}
            )
    return {"session": session}


@app.get("/sessions")
async def list_sessions(project_name: Optional[str] = None) -> Dict[str, List[Dict[str, object]]]:
    sessions = session_manager.list_sessions(project_name)
    return {"sessions": sessions}


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str) -> Dict[str, object]:
    if not _session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    session = session_manager.get_session(session_id)
    return {
        "messages": session.get("messages", []),
        "project_name": session.get("project_name"),
        "selected_files": session.get("selected_files", []),
        "plots": session.get("plots", []),
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, object]:
    file_path = await data_manager.save_file(file)
    preview = data_manager.get_preview(file_path)

    validator = get_validator()
    df = data_manager.load_data(file_path)
    analysis = validator.analyze_data(df)

    return {
        "path": file_path,
        "preview": preview,
        "analysis": analysis,
    }


@app.post("/paste_data")
async def paste_data(request: PasteDataRequest) -> Dict[str, object]:
    """Handle pasted data (CSV or JSON) with intelligent delimiter detection."""
    data_content = request.data
    format_type = request.format.lower().strip()

    if not data_content:
        raise HTTPException(status_code=400, detail="No data provided")

    if format_type not in {"csv", "json"}:
        raise HTTPException(status_code=400, detail="Unsupported format")

    project_name = None
    target_dir = data_manager.upload_dir
    if request.project_name:
        project_name = _validate_project_name(request.project_name)
        if project_name not in project_manager.list_projects():
            project_manager.create_project(project_name)
        manifest_manager.ensure_manifest(project_name)
        target_dir = project_manager.get_project_path(project_name)

    if format_type == "csv":
        delimiters = [",", "\t", " ", ";", "|"]
        best_delimiter = ","
        max_columns = 0

        lines = data_content.strip().split("\n")
        check_lines = lines[:5] if len(lines) > 5 else lines

        if check_lines:
            for delim in delimiters:
                first_line_cols = len(check_lines[0].split(delim))
                if first_line_cols > 1:
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

        if best_delimiter == " ":
            cleaned_lines = []
            for line in lines:
                cleaned_line = re.sub(r"\s+", ",", line.strip())
                cleaned_lines.append(cleaned_line)
            data_content = "\n".join(cleaned_lines)
            best_delimiter = ","

        filename = f"pasted_data_{format_type}.{format_type}"
        file_path = await data_manager.save_text_data(
            data_content, filename, target_dir=target_dir
        )
        df = pd.read_csv(io.StringIO(data_content), sep=best_delimiter)
    else:
        filename = f"pasted_data_{format_type}.{format_type}"
        file_path = await data_manager.save_text_data(
            data_content, filename, target_dir=target_dir
        )
        df = pd.read_json(io.StringIO(data_content))

    validator = get_validator()
    analysis = validator.analyze_data(df)
    preview = data_manager.get_preview(file_path)

    parsing_info = {
        "detected_delimiter": best_delimiter if format_type == "csv" else "N/A",
        "rows_parsed": len(df),
        "columns_parsed": len(df.columns),
        "column_names": list(df.columns),
        "sample_data": df.head(3).to_dict(orient="records"),
    }

    return {
        "path": file_path,
        "preview": preview,
        "parsing_info": parsing_info,
        "analysis": analysis,
        "dataset": manifest_manager.register_dataset(project_name, file_path)
        if request.project_name
        else None,
    }


@app.post("/join_suggestions")
async def join_suggestions(request: JoinRequest) -> Dict[str, object]:
    selected_files = _unique_paths(request.selected_files)
    if len(selected_files) < 2:
        raise HTTPException(status_code=400, detail="Select at least two files")

    existing_files, missing_files = _split_existing_files(selected_files)
    if missing_files:
        raise HTTPException(status_code=400, detail="Some selected files are missing")

    alias_map = build_alias_map(existing_files)
    dataframes = {alias: data_manager.load_data(path) for alias, path in alias_map.items()}
    suggestions = join_assistant.suggest_joins(dataframes)
    suggestions["alias_map"] = alias_map
    return suggestions


@app.post("/preview")
async def preview_data(request: PreviewRequest) -> Dict[str, object]:
    if not os.path.isfile(request.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    df = data_manager.load_data(request.file_path)
    validator = get_validator()
    analysis = validator.analyze_data(df)
    analysis["dtypes"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    preview = df.head(10).to_dict(orient="records")
    return {"preview": preview, "analysis": analysis}


@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, object]:
    """Handle chat requests with optional multi-file plot context."""
    if request.provider == "gemini" and not request.api_key:
        return {"response": "API Key required for Gemini", "type": "error"}
    if request.provider == "openai" and not request.api_key:
        return {"response": "API Key required for OpenAI", "type": "error"}

    llm_service.set_provider(request.provider, request.api_key, request.model)

    history_text = None
    if request.session_id:
        if not _session_exists(request.session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        session_messages = session_manager.get_messages(request.session_id)
        session_manager.update_session_context(
            request.session_id, request.project_name, request.selected_files
        )
        history_text = _build_history(session_messages)

    data_context = ""
    data_analysis = None
    file_catalog = None
    alias_map: Dict[str, str] = {}
    data_paths: Optional[object] = None

    selected_files = _unique_paths(request.selected_files)
    if selected_files:
        existing_files, missing_files = _split_existing_files(selected_files)
        if missing_files:
            return {
                "response": f"Missing files: {', '.join(missing_files)}",
                "type": "error",
            }
        alias_map = build_alias_map(existing_files)
        data_context = data_manager.get_multi_data_context(alias_map)
        file_catalog = _build_file_catalog(alias_map)
        data_paths = existing_files
    elif request.context:
        if not os.path.exists(request.context):
            return {"response": "Data file not found", "type": "error"}
        data_context = data_manager.get_data_context(request.context)
        validator = get_validator()
        df = data_manager.load_data(request.context)
        data_analysis = validator.analyze_data(df)
        data_paths = request.context

    url_analysis = None
    url_pattern = re.compile(r"https?://[^\s]+")
    urls = url_pattern.findall(request.message)
    if urls:
        assistant = get_intelligent_assistant()
        url_analysis = assistant.analyze_url(urls[0])

    response: Dict[str, object]
    gallery_title = extract_gallery_example_title(request.message)
    gallery_adaptation = None
    if gallery_title:
        gallery_adaptation = maybe_adapt_gallery_example(
            gallery_title, data_analysis=data_analysis, file_catalog=file_catalog
        )

    if gallery_adaptation:
        response = {
            "type": "plot_code",
            "code": gallery_adaptation.code,
            "text": f"I generated a plot based on the gallery example: {gallery_adaptation.description}.",
        }
    else:
        template_plot = None
        if data_paths is None and not request.current_code:
            template_plot = maybe_generate_template_plot(request.message)

        if template_plot:
            response = {
                "type": "plot_code",
                "code": template_plot.code,
                "text": f"I generated a {template_plot.description}.",
            }
        else:
            response = await llm_service.process_query(
                query=request.message,
                context=data_context,
                current_code=request.current_code,
                history=history_text,
                data_analysis=data_analysis,
                url_analysis=url_analysis,
                file_catalog=file_catalog,
            )

    if request.session_id:
        session_manager.append_message(request.session_id, "user", request.message)
        session_manager.append_message(
            request.session_id,
            "assistant",
            response.get("text", ""),
            code=response.get("code"),
        )

    if response.get("type") == "plot_code":
        plot_result = plot_engine.execute_code(
            response["code"], data_paths, file_aliases=alias_map or None
        )
        if plot_result.get("error"):
            fallback_plot = None
            if gallery_title:
                fallback_plot = generate_gallery_fallback_plot(
                    data_analysis=data_analysis, file_catalog=file_catalog
                )
            if fallback_plot:
                fallback_result = plot_engine.execute_code(
                    fallback_plot.code, data_paths, file_aliases=alias_map or None
                )
                if not fallback_result.get("error"):
                    plot_entry = None
                    if request.project_name and fallback_result.get("image"):
                        project_name = _validate_project_name(request.project_name)
                        if project_name in project_manager.list_projects():
                            project_path = project_manager.get_project_path(project_name)
                            image_path, thumbnail_path = save_plot_assets(
                                project_path, fallback_result["image"]
                            )
                            plot_entry = manifest_manager.register_plot(
                                project_name=project_name,
                                code=fallback_plot.code,
                                selected_files=selected_files,
                                image_path=image_path,
                                thumbnail_path=thumbnail_path,
                                session_id=request.session_id,
                                description=f"Fallback plot for gallery example: {gallery_title}",
                            )
                            if request.session_id and plot_entry:
                                session_manager.append_plot(request.session_id, plot_entry)
                    return {
                        "response": (
                            "The gallery example could not be executed as generated, "
                            "so I created a fallback plot from your data."
                        ),
                        "plot": fallback_result.get("image"),
                        "metadata": fallback_result.get("metadata", []),
                        "code": fallback_plot.code,
                        "plot_entry": plot_entry,
                        "warnings": fallback_result.get("warnings", []),
                    }
            return {
                "response": f"Plot execution failed: {plot_result.get('error_message', 'Unknown error')}",
                "error": True,
                "warnings": plot_result.get("warnings", []),
                "code": response["code"],
            }
        plot_entry = None
        if request.project_name and plot_result.get("image"):
            project_name = _validate_project_name(request.project_name)
            if project_name in project_manager.list_projects():
                project_path = project_manager.get_project_path(project_name)
                image_path, thumbnail_path = save_plot_assets(
                    project_path, plot_result["image"]
                )
                plot_entry = manifest_manager.register_plot(
                    project_name=project_name,
                    code=response["code"],
                    selected_files=selected_files,
                    image_path=image_path,
                    thumbnail_path=thumbnail_path,
                    session_id=request.session_id,
                    description=request.message,
                )
                if request.session_id and plot_entry:
                    session_manager.append_plot(request.session_id, plot_entry)
        return {
            "response": response.get("text", "Here is the plot you requested."),
            "plot": plot_result.get("image"),
            "metadata": plot_result.get("metadata", []),
            "code": response["code"],
            "plot_entry": plot_entry,
            "warnings": plot_result.get("warnings", []),
        }

    if response.get("type") == "error":
        return {"response": response.get("text", "Unable to generate plot."), "type": "text"}

    if response.get("type") == "clarify":
        return {"response": response.get("text", ""), "type": "clarify"}

    return {"response": response.get("text", "")}


@app.post("/execute_plot")
async def execute_plot(request: ExecutePlotRequest) -> Dict[str, object]:
    """Execute user-supplied plot code directly (no LLM rewrite)."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code is required")

    selected_files = _unique_paths(request.selected_files)
    alias_map: Optional[Dict[str, str]] = None
    data_paths: Optional[object] = None

    if selected_files:
        existing_files, missing_files = _split_existing_files(selected_files)
        if missing_files:
            raise HTTPException(status_code=400, detail="Selected files not found")
        alias_map = build_alias_map(existing_files)
        data_paths = existing_files
    elif request.context:
        if not os.path.exists(request.context):
            raise HTTPException(status_code=404, detail="Data file not found")
        data_paths = request.context

    plot_result = plot_engine.execute_code(
        request.code,
        data_paths,
        dpi=request.dpi,
        format=request.format,
        file_aliases=alias_map,
    )

    if plot_result.get("error"):
        return {
            "error": True,
            "error_message": plot_result.get("error_message", "Plot execution failed"),
            "warnings": plot_result.get("warnings", []),
            "code": request.code,
        }

    plot_entry = None
    if request.project_name and plot_result.get("image"):
        project_name = _validate_project_name(request.project_name)
        if project_name in project_manager.list_projects():
            project_path = project_manager.get_project_path(project_name)
            image_path, thumbnail_path = save_plot_assets(project_path, plot_result["image"])
            plot_entry = manifest_manager.register_plot(
                project_name=project_name,
                code=request.code,
                selected_files=selected_files,
                image_path=image_path,
                thumbnail_path=thumbnail_path,
                session_id=request.session_id,
                description=request.description or "Direct code execution",
            )
            if request.session_id and plot_entry:
                session_manager.append_plot(request.session_id, plot_entry)

    return {
        "plot": plot_result.get("image"),
        "metadata": plot_result.get("metadata", []),
        "code": request.code,
        "plot_entry": plot_entry,
        "warnings": plot_result.get("warnings", []),
    }


@app.post("/validate")
async def validate_plot_type(plot_type: str, file_path: str) -> Dict[str, object]:
    """Validate if data is suitable for a specific plot type."""
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
            "schema": schema,
        }

    return {"valid": True, "message": message}


@app.post("/download_plot")
async def download_plot(request: DownloadRequest) -> StreamingResponse:
    """Generate a plot download using the provided code and dataset context."""
    data_paths: Optional[object] = None
    alias_map: Optional[Dict[str, str]] = None

    selected_files = _unique_paths(request.selected_files)
    if selected_files:
        existing_files, missing_files = _split_existing_files(selected_files)
        if missing_files:
            raise HTTPException(status_code=400, detail="Selected files not found")
        alias_map = build_alias_map(existing_files)
        data_paths = existing_files
    elif request.context:
        data_paths = request.context

    result = plot_engine.execute_code(
        request.code,
        data_paths,
        dpi=request.dpi,
        format=request.format,
        file_aliases=alias_map,
    )

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error_message", "Plot failed"))

    buffer = result.get("buffer")
    if buffer is None:
        raise HTTPException(status_code=500, detail="Failed to generate plot")

    buffer.seek(0)
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }

    return StreamingResponse(
        buffer,
        media_type=media_types.get(request.format, "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename=plot.{request.format}"},
    )


def _unique_paths(paths: List[str]) -> List[str]:
    """Return a de-duplicated list while preserving order."""
    seen = set()
    unique = []
    for path in paths:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def _split_existing_files(paths: List[str]) -> Tuple[List[str], List[str]]:
    """Return (existing, missing) file paths."""
    existing = []
    missing = []
    for path in paths:
        if os.path.isfile(path):
            existing.append(path)
        else:
            missing.append(path)
    return existing, missing


def _build_history(messages: List[Dict[str, object]], max_messages: int = 12) -> str:
    """Format a compact conversation history string for the LLM."""
    lines = []
    for message in messages[-max_messages:]:
        role = str(message.get("role", "user")).capitalize()
        content = str(message.get("content", ""))
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _build_file_catalog(alias_map: Dict[str, str]) -> List[Dict[str, object]]:
    """Assemble file summaries for prompt context."""
    catalog = []
    validator = get_validator()
    for alias, path in alias_map.items():
        df = data_manager.load_data(path)
        analysis = validator.analyze_data(df)
        catalog.append(
            {
                "alias": alias,
                "filename": os.path.basename(path),
                "path": os.path.abspath(path),
                "analysis": analysis,
            }
        )
    return catalog


def _validate_project_name(project_name: str) -> str:
    """Validate and normalize a project name."""
    name = project_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")
    if name.startswith("."):
        raise HTTPException(status_code=400, detail="Project name cannot start with dot")
    if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
        raise HTTPException(status_code=400, detail="Invalid project name")
    return name


def _session_exists(session_id: str) -> bool:
    """Return True if a session exists in the index."""
    sessions = session_manager.list_sessions()
    return any(session.get("id") == session_id for session in sessions)


def _is_port_in_use(port: int) -> bool:
    """Return True if a TCP connection can be made to the port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _pid_exists(pid: int) -> bool:
    """Return True if the PID exists on systems with /proc."""
    if os.name != "posix":
        return False
    if not os.path.exists("/proc"):
        return False
    return os.path.exists(f"/proc/{pid}")


def _find_pids_on_port(port: int) -> List[int]:
    """Find process IDs listening on the given port using system tools."""
    pids: List[int] = []
    if shutil.which("lsof"):
        result = subprocess.run(
            ["lsof", "-t", "-i", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            for line in result.stdout.split():
                if line.isdigit():
                    pids.append(int(line))
        return pids

    if shutil.which("fuser"):
        result = subprocess.run(
            ["fuser", "-n", "tcp", str(port)],
            capture_output=True,
            text=True,
            check=False,
        )
        tokens = result.stdout.replace("/", " ").replace(":", " ").split()
        for token in tokens:
            if token.isdigit():
                pids.append(int(token))
        return pids

    return pids


def _terminate_pids(pids: List[int], sig: int) -> None:
    """Send a signal to each PID if it exists."""
    for pid in pids:
        if _pid_exists(pid):
            os.kill(pid, sig)


def _ensure_port_available(port: int) -> None:
    """Terminate processes on the port so the server can bind."""
    if not _is_port_in_use(port):
        return

    pids = _find_pids_on_port(port)
    if not pids:
        raise RuntimeError(f"Port {port} is in use and no process IDs were found")

    _terminate_pids(pids, signal.SIGTERM)
    time.sleep(0.4)

    if _is_port_in_use(port):
        _terminate_pids(pids, signal.SIGKILL)
        time.sleep(0.4)

    if _is_port_in_use(port):
        raise RuntimeError(f"Port {port} is still in use after termination attempts")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    _ensure_port_available(port)
    uvicorn.run(app, host="0.0.0.0", port=port)
