from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(title="CADGen Sandbox Worker", version="0.1.0")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "cad-sandbox"}


class ExecuteRequest(BaseModel):
    code: str
    parameters: dict[str, Any] | None = None
    session_id: str | None = None
    export_options: dict[str, Any] | None = None


class ExecuteResponse(BaseModel):
    step_path: str
    stl_path: str
    gltf_path: str
    logs: str
    working_dir: str


def _run_script(code: str, output_dir: str) -> tuple[str, int]:
    script_path = os.path.join(output_dir, "script.py")
    with open(script_path, "w") as f:
        f.write(code)
    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=output_dir,
    )
    return result.stdout + result.stderr, result.returncode


@app.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest) -> ExecuteResponse:
    session_id = request.session_id or str(uuid.uuid4())
    outputs_dir = os.environ.get("CADGEN_OUTPUT_DIR", "/tmp/cadgen_outputs")
    output_dir = os.path.join(outputs_dir, session_id)
    os.makedirs(output_dir, exist_ok=True)

    code = request.code
    if request.export_options:
        tolerance = request.export_options.get("stl_tolerance", 0.01)
        import re

        stl_pattern = r'cq\.exporters\.export\(result,\s*["\']output\.stl["\'](?:,\s*tolerance\s*=\s*[\d.]+)?\)'
        stl_replacement = f'cq.exporters.export(result, "output.stl", tolerance={tolerance})'
        code = re.sub(stl_pattern, stl_replacement, code)

    try:
        logs, returncode = _run_script(code, output_dir)
        if returncode != 0:
            logger.error("Sandbox execution failed: %s", logs)
            return ExecuteResponse(
                step_path="",
                stl_path="",
                gltf_path="",
                logs=logs,
                working_dir=output_dir,
            )
    except subprocess.TimeoutExpired:
        logger.error("Sandbox execution timed out")
        return ExecuteResponse(
            step_path="",
            stl_path="",
            gltf_path="",
            logs="Execution timed out after 120s",
            working_dir=output_dir,
        )
    except Exception as exc:
        logger.error("Sandbox execution error: %s", exc)
        return ExecuteResponse(
            step_path="",
            stl_path="",
            gltf_path="",
            logs=str(exc),
            working_dir=output_dir,
        )

    step_path = os.path.join(output_dir, "output.step")
    stl_path = os.path.join(output_dir, "output.stl")
    gltf_path = os.path.join(output_dir, "output.gltf")

    return ExecuteResponse(
        step_path=step_path if os.path.exists(step_path) else "",
        stl_path=stl_path if os.path.exists(stl_path) else "",
        gltf_path=gltf_path if os.path.exists(gltf_path) else "",
        logs=logs,
        working_dir=output_dir,
    )
