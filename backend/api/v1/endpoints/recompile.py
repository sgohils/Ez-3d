from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request

from models.schemas import RecompileRequest, RecompileResponse, ParameterSchema
from services.llm_pipeline import substitute_parameters
from services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recompile", tags=["recompile"])


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
        result = sandbox.execute(code, request.parameters, session_id=session.session_id)

        session.code = code
        session.parameters = request.parameters
        session.parameter_schemas = [p.model_dump() for p in param_schemas]

        base_url = str(http_request.base_url).rstrip("/")
        session.step_url = f"{base_url}/outputs/{session.session_id}/output.step" if result.get("step_path") and os.path.exists(result.get("step_path", "")) else ""
        session.stl_url = f"{base_url}/outputs/{session.session_id}/output.stl" if result.get("stl_path") and os.path.exists(result.get("stl_path", "")) else ""
        session.gltf_url = f"{base_url}/outputs/{session.session_id}/output.gltf" if result.get("gltf_path") and os.path.exists(result.get("gltf_path", "")) else ""
        session.logs = result.get("logs", "")

        return RecompileResponse(
            step_url=session.step_url,
            stl_url=session.stl_url,
            gltf_url=session.gltf_url,
            parameters=param_schemas,
            code=code,
            logs=result.get("logs", ""),
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