"""Execution engine for matplotlib plot code."""

from __future__ import annotations

import ast
import io
from typing import Dict, List, Optional, Union

from code_safety import CodeSafetyValidator
from file_utils import build_alias_map
from sandbox_executor import SandboxExecutor


class _ImportStripper(ast.NodeTransformer):
    """Remove import statements from generated code."""

    def visit_Import(self, node: ast.Import) -> Optional[ast.AST]:
        return None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Optional[ast.AST]:
        return None


class PlotEngine:
    """Execute LLM-generated matplotlib code with safety checks."""

    def __init__(self) -> None:
        self.validator = CodeSafetyValidator()
        self.executor = SandboxExecutor()

    def execute_code(
        self,
        code: str,
        data_paths: Optional[Union[str, List[str], Dict[str, str]]] = None,
        dpi: int = 300,
        format: str = "png",
        file_aliases: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
        """Execute plot code and return rendered artifacts."""
        lint = self.validator.lint(code)
        if not lint.ok:
            return {
                "error": True,
                "error_message": "; ".join(lint.errors),
                "warnings": lint.warnings,
            }

        sanitized_code = self._strip_imports(code)
        alias_map = self._normalize_alias_map(data_paths, file_aliases)
        result = self.executor.execute(sanitized_code, alias_map, dpi=dpi, image_format=format)
        if result.get("error"):
            return result

        buffer_bytes = result.get("buffer", b"")
        buffer = io.BytesIO(buffer_bytes)

        return {
            "image": result.get("image"),
            "metadata": result.get("metadata", []),
            "buffer": buffer,
            "warnings": lint.warnings,
        }

    def _normalize_alias_map(
        self,
        data_paths: Optional[Union[str, List[str], Dict[str, str]]],
        file_aliases: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        if file_aliases:
            return file_aliases
        if isinstance(data_paths, dict):
            return data_paths
        if isinstance(data_paths, list):
            return build_alias_map(data_paths)
        if isinstance(data_paths, str) and data_paths:
            return build_alias_map([data_paths])
        return {}

    def _strip_imports(self, code: str) -> str:
        """Strip import statements from the code to rely on injected globals."""
        tree = ast.parse(code)
        stripped = _ImportStripper().visit(tree)
        ast.fix_missing_locations(stripped)
        return ast.unparse(stripped)
