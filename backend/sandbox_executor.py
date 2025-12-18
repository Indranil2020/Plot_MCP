"""Run plotting code in a constrained subprocess."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Dict, Optional


class SandboxExecutor:
    """Execute plot code in a subprocess with time and optional memory limits."""

    def __init__(self, timeout_seconds: int = 8, memory_limit_mb: Optional[int] = None) -> None:
        self.timeout_seconds = timeout_seconds
        env_limit = os.getenv("PLOT_EXEC_MEMORY_MB")
        if memory_limit_mb is not None:
            self.memory_limit_mb = memory_limit_mb
        elif env_limit and env_limit.isdigit():
            self.memory_limit_mb = int(env_limit)
        else:
            self.memory_limit_mb = 0

    def execute(
        self,
        code: str,
        data_paths: Dict[str, str],
        dpi: int = 300,
        image_format: str = "png",
    ) -> Dict[str, object]:
        """Execute the code and return image/metadata or an error state."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload_path = os.path.join(tmp_dir, "payload.json")
            output_image = os.path.join(tmp_dir, f"plot.{image_format}")
            output_metadata = os.path.join(tmp_dir, "metadata.json")

            payload = {
                "code": code,
                "data_paths": data_paths,
                "output_image": output_image,
                "output_metadata": output_metadata,
                "dpi": dpi,
                "format": image_format,
                "memory_limit_mb": self.memory_limit_mb,
            }

            with open(payload_path, "w") as f:
                json.dump(payload, f)

            process = subprocess.Popen(
                [
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), "sandbox_runner.py"),
                    "--payload",
                    payload_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            start = time.monotonic()
            while process.poll() is None:
                if time.monotonic() - start > self.timeout_seconds:
                    process.terminate()
                    process.wait()
                    return {"error": True, "error_message": "Plot execution timed out"}
                time.sleep(0.05)

            stdout, stderr = process.communicate()
            if process.returncode != 0:
                detail = (stderr or stdout or "").strip()
                if detail:
                    detail = detail[-2000:]
                    return {"error": True, "error_message": detail}
                return {"error": True, "error_message": "Plot execution failed"}

            if not os.path.isfile(output_image):
                return {"error": True, "error_message": "Plot image not generated"}

            metadata = []
            if os.path.isfile(output_metadata):
                with open(output_metadata, "r") as f:
                    metadata = json.load(f)

            with open(output_image, "rb") as f:
                image_bytes = f.read()

            result = {
                "metadata": metadata,
                "buffer": image_bytes,
            }

            if image_format == "png":
                result["image"] = base64.b64encode(image_bytes).decode("utf-8")

            return result
