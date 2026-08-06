from __future__ import annotations

import logging
import os
from typing import Callable

from fastapi import APIRouter, HTTPException, Request

from backend.models.schemas import RecompileRequest, RecompileResponse, ParameterSchema
from backend.services.llm_pipeline import LLMPipeline, substitute_parameters
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from backend.services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recompile", tags=["recompile"])


def _make_on_error_callback(llm: LLMPipeline) -> Callable[[str, str], str]:
    def on_error(error_logs: str, code: str) -> str:
        return llm.repair_code(error_logs, code)
    return on_error


@router.post("/", response_model=RecompileResponse)
async def recompile(request: RecompileRequest, http_request: Request) -> RecompileResponse:
    try:
        session = SessionManager.get_last()
        if session is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "No previous generation found",
                    "detail": "Call /generate first before recompiling.",
                    "logs": "",
                },
            )

        llm = LLMPipeline()
        code = substitute_parameters(session.code, request.parameters)

        param_schemas: list[ParameterSchema] = []
        for name, value in request.parameters.items():
            param_schemas.append(ParameterSchema(
                name=name,
                value=float(value),
                min=0.1,
                max=100.0,
                step=0.1,
            ))

        sandbox = CadQuerySandbox()
        on_error = _make_on_error_callback(llm)
        result = sandbox.execute(
            code,
            request.parameters,
            session_id=session.session_id,
            on_error=on_error,
            max_retries=3,
        )

        session.code = code
        session.parameters = request.parameters
        session.parameter_schemas = [p.model_dump() for p in param_schemas]

        base_url = str(http_request.base_url).rstrip("/")
        session.step_url = f"{base_url}/outputs/{session.session_id}/output.step" if result.get("step_path") and os.path.exists(result.get("step_path", "")) else ""
        session.stl_url = f"{base_url}/outputs/{session.session_id}/output.stl" if result.get("stl_path") and os.path.exists(result.get("stl_path", "")) else ""
        session.gltf_url = f"{base_url}/outputs/{session.session_id}/output.gltf" if result.get("gltf_path") and os.path.exists(result.get("gltf_path", "")) else ""
        session.logs = result.get("logs", "")

        retry_count = result.get("retry_count", 0)
        if retry_count > 0:
            session.logs = f"[Auto-fix retries: {retry_count}]\n{session.logs}"

        return RecompileResponse(
            step_url=session.step_url,
            stl_url=session.stl_url,
            gltf_url=session.gltf_url,
            parameters=param_schemas,
            code=code,
            logs=session.logs,
        )
    except SandboxExecutionError as exc:
        logger.error("Recompilation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CadQuery recompilation failed",
                "detail": str(exc),
                "logs": exc.logs,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Recompilation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Recompilation failed",
                "detail": str(exc),
                "logs": "",
            },
        )