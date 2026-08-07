from __future__ import annotations

import ast
import os
import subprocess
import tempfile
import time
from typing import Any

VALIDATE_TIMEOUT = int(os.environ.get("CADGEN_VALIDATE_TIMEOUT", "60"))


class ScriptValidationError(Exception):
    def __init__(self, message: str, logs: str = "") -> None:
        super().__init__(message)
        self.logs = logs


def _check_imports(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ScriptValidationError(f"Syntax error: {exc}") from exc

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _static_validate(code: str) -> dict[str, Any]:
    logs: list[str] = []
    logs.append("Checking syntax and imports...")

    imports = _check_imports(code)
    if "cadquery" not in imports:
        raise ScriptValidationError("Missing 'import cadquery as cq'")

    logs.append("Syntax OK, cadquery import found.")

    if "cq.Workplane" not in code:
        raise ScriptValidationError("Missing cq.Workplane usage")

    required_exports = ['cq.exporters.export(result, "output.step")', 'cq.exporters.export(result, "output.stl")', 'cq.exporters.export(result, "output.gltf")']
    for export in required_exports:
        if export not in code:
            raise ScriptValidationError(f"Missing export: {export}")

    logs.append("Static structure validation passed.")
    return {
        "valid": True,
        "logs": "\n".join(logs),
        "execution_time": 0.0,
        "mode": "static",
    }


def validate_script(code: str) -> dict[str, Any]:
    try:
        return _static_validate(code)
    except ScriptValidationError as static_exc:
        logs = [static_exc.logs] if static_exc.logs else []
        logs.append("Falling back to subprocess execution...")

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "validate_script.py")
            with open(script_path, "w") as f:
                f.write(code)

            start = time.time()
            try:
                result = subprocess.run(
                    ["python", script_path],
                    capture_output=True,
                    text=True,
                    timeout=VALIDATE_TIMEOUT,
                    cwd=tmpdir,
                )
                elapsed = time.time() - start
                exec_logs = f"Execution finished in {elapsed:.2f}s with return code {result.returncode}\n{result.stdout}\n{result.stderr}"
                logs.append(exec_logs)

                if result.returncode != 0:
                    raise ScriptValidationError(
                        f"CadQuery script failed with return code {result.returncode}",
                        logs="\n".join(logs),
                    )

                required = ["output.step", "output.stl", "output.gltf"]
                missing = [f for f in required if not os.path.exists(os.path.join(tmpdir, f))]
                if missing:
                    raise ScriptValidationError(
                        f"Missing exports: {', '.join(missing)}",
                        logs="\n".join(logs),
                    )

                logs.append("All required exports found.")
                return {
                    "valid": True,
                    "logs": "\n".join(logs),
                    "execution_time": elapsed,
                    "mode": "subprocess",
                }
            except subprocess.TimeoutExpired:
                raise ScriptValidationError(
                    f"Validation timed out after {VALIDATE_TIMEOUT}s",
                    logs="\n".join(logs),
                )
            except FileNotFoundError as exc:
                raise ScriptValidationError(
                    f"Validation environment missing dependencies: {exc}",
                    logs="\n".join(logs),
                ) from exc
