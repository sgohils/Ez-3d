from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class SandboxExecutionError(Exception):
    def __init__(self, message: str, logs: str = "") -> None:
        super().__init__(message)
        self.logs = logs


class CadQuerySandbox:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._outputs_dir = os.environ.get("CADGEN_OUTPUT_DIR", "/tmp/cadgen_outputs")
        self._sandbox_url = os.environ.get("CADGEN_SANDBOX_URL", "")

    def execute(
        self,
        code: str,
        parameters: dict[str, Any] | None = None,
        session_id: str | None = None,
        export_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._logger.info("Executing CadQuery code in sandbox")
        substituted_code = self._substitute_params(code, parameters or {})
        substituted_code = self._inject_export_options(substituted_code, export_options or {})

        if not session_id:
            session_id = str(uuid.uuid4())

        if self._sandbox_url:
            return self._execute_remote(
                substituted_code, session_id, export_options or {}
            )

        output_dir = os.path.join(self._outputs_dir, session_id)
        os.makedirs(output_dir, exist_ok=True)
        script_path = os.path.join(output_dir, "script.py")

        try:
            with open(script_path, "w") as f:
                f.write(substituted_code)

            self._logger.info("Running CadQuery script in %s", output_dir)
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=output_dir,
            )

            logs = result.stdout + result.stderr
            if result.returncode != 0:
                raise SandboxExecutionError(
                    f"CadQuery execution failed with return code {result.returncode}",
                    logs=logs,
                )

            step_path = os.path.join(output_dir, "output.step")
            stl_path = os.path.join(output_dir, "output.stl")
            gltf_path = os.path.join(output_dir, "output.gltf")

            return {
                "step_path": step_path if os.path.exists(step_path) else "",
                "stl_path": stl_path if os.path.exists(stl_path) else "",
                "gltf_path": gltf_path if os.path.exists(gltf_path) else "",
                "logs": logs,
                "working_dir": output_dir,
            }
        except subprocess.TimeoutExpired:
            raise SandboxExecutionError("CadQuery execution timed out after 120s", logs="")
        except FileNotFoundError:
            raise SandboxExecutionError("CadQuery script not found after execution", logs="")

    def _inject_export_options(self, code: str, export_options: dict[str, Any]) -> str:
        result = code
        tolerance = export_options.get("stl_tolerance", 0.01)
        stl_pattern = r'cq\.exporters\.export\(result,\s*["\']output\.stl["\'](?:,\s*tolerance\s*=\s*[\d.]+)?\)'
        stl_replacement = f'cq.exporters.export(result, "output.stl", tolerance={tolerance})'
        result = re.sub(stl_pattern, stl_replacement, result)
        return result

    def _substitute_params(self, code: str, parameters: dict[str, Any]) -> str:
        result = code
        for name, value in parameters.items():
            result = result.replace(name, str(value))
        return result

    def _execute_remote(
        self,
        code: str,
        session_id: str,
        export_options: dict[str, Any],
    ) -> dict[str, Any]:
        import json
        import urllib.request

        self._logger.info("Using remote sandbox at %s", self._sandbox_url)
        payload = json.dumps({
            "code": code,
            "session_id": session_id,
            "export_options": export_options,
        }).encode()
        req = urllib.request.Request(
            f"{self._sandbox_url.rstrip('/')}/execute",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=130) as resp:
            result = json.loads(resp.read().decode())
        return {
            "step_path": result.get("step_path", ""),
            "stl_path": result.get("stl_path", ""),
            "gltf_path": result.get("gltf_path", ""),
            "logs": result.get("logs", ""),
            "working_dir": result.get("working_dir", ""),
        }