from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import uuid
from typing import Any, Callable

logger = logging.getLogger(__name__)


class SandboxExecutionError(Exception):
    def __init__(self, message: str, logs: str = "") -> None:
        super().__init__(message)
        self.logs = logs


class CadQuerySandbox:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._outputs_dir = os.environ.get("CADGEN_OUTPUT_DIR", "/tmp/cadgen_outputs")

    def execute(
        self,
        code: str,
        parameters: dict[str, Any] | None = None,
        session_id: str | None = None,
        on_error: Callable[[str, str], str] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        self._logger.info("Executing CadQuery code in sandbox")
        substituted_code = self._substitute_params(code, parameters or {})

        if not session_id:
            session_id = str(uuid.uuid4())

        output_dir = os.path.join(self._outputs_dir, session_id)
        os.makedirs(output_dir, exist_ok=True)
        script_path = os.path.join(output_dir, "script.py")

        all_logs: list[str] = []
        current_code = substituted_code
        retry_count = 0

        while True:
            try:
                with open(script_path, "w") as f:
                    f.write(current_code)

                self._logger.info("Running CadQuery script in %s", output_dir)
                result = subprocess.run(
                    ["python", script_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=output_dir,
                )

                logs = result.stdout + result.stderr
                all_logs.append(logs)

                if result.returncode != 0:
                    error_msg = f"CadQuery execution failed with return code {result.returncode}"
                    if on_error is not None and retry_count < max_retries:
                        self._logger.info(
                            "Execution failed, attempting repair (retry %d/%d)",
                            retry_count + 1,
                            max_retries,
                        )
                        current_code = on_error(logs, current_code)
                        retry_count += 1
                        continue
                    raise SandboxExecutionError(error_msg, logs=logs)

                step_path = os.path.join(output_dir, "output.step")
                stl_path = os.path.join(output_dir, "output.stl")
                gltf_path = os.path.join(output_dir, "output.gltf")

                return {
                    "step_path": step_path if os.path.exists(step_path) else "",
                    "stl_path": stl_path if os.path.exists(stl_path) else "",
                    "gltf_path": gltf_path if os.path.exists(gltf_path) else "",
                    "logs": "\n".join(all_logs),
                    "working_dir": output_dir,
                    "retry_count": retry_count,
                }
            except subprocess.TimeoutExpired:
                error_msg = "CadQuery execution timed out after 120s"
                if on_error is not None and retry_count < max_retries:
                    self._logger.info(
                        "Execution timed out, attempting repair (retry %d/%d)",
                        retry_count + 1,
                        max_retries,
                    )
                    current_code = on_error("", current_code)
                    retry_count += 1
                    continue
                raise SandboxExecutionError(error_msg, logs="")
            except FileNotFoundError:
                error_msg = "CadQuery script not found after execution"
                if on_error is not None and retry_count < max_retries:
                    self._logger.info(
                        "Script not found, attempting repair (retry %d/%d)",
                        retry_count + 1,
                        max_retries,
                    )
                    current_code = on_error("", current_code)
                    retry_count += 1
                    continue
                raise SandboxExecutionError(error_msg, logs="")

    def _substitute_params(self, code: str, parameters: dict[str, Any]) -> str:
        result = code
        for name, value in parameters.items():
            result = result.replace(name, str(value))
        return result