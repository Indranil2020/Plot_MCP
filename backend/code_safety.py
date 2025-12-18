"""Static validation for LLM-generated plotting code."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List, Set


@dataclass
class LintResult:
    """Lint result container."""

    ok: bool
    errors: List[str]
    warnings: List[str]


class CodeSafetyValidator:
    """Validate plot code for unsafe constructs."""

    def __init__(self) -> None:
        self.allowed_imports = {
            "matplotlib",
            "matplotlib.pyplot",
            "pandas",
            "numpy",
            "seaborn",
        }
        self.disallowed_names = {
            "open",
            "exec",
            "eval",
            "compile",
            "__import__",
            "input",
            "exit",
            "quit",
            "os",
            "sys",
            "subprocess",
            "socket",
            "pathlib",
            "shutil",
            "pd.read_csv",
            "pd.read_json",
            "pd.read_excel",
            "pd.read_parquet",
            "np.load",
        }

    def lint(self, code: str) -> LintResult:
        """Parse and validate code against import and call rules."""
        tree = ast.parse(code)
        errors: List[str] = []
        warnings: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_imports:
                        errors.append(f"Import not allowed: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module not in self.allowed_imports:
                    errors.append(f"Import not allowed: {module}")
            elif isinstance(node, ast.Constant):
                if node.value is Ellipsis:
                    errors.append("Placeholder '...' detected; replace with real values/columns")
            elif isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name in self.disallowed_names:
                    errors.append(f"Call not allowed: {name}")
            elif isinstance(node, ast.Name):
                if node.id in self.disallowed_names:
                    warnings.append(f"Reference to restricted name: {node.id}")

        ok = len(errors) == 0
        return LintResult(ok=ok, errors=errors, warnings=warnings)

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return ""
