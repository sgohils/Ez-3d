from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import RecompileRequest, RecompileResponse, ParameterSchema
from backend.services.llm_pipeline import substitute_parameters
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from backend.services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recompile", tags=["recompile"])


@router.post("/", response_model=RecompileResponse)
async def recompile(request: RecompileRequest) -> RecompileResponse:
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
        result = sandbox.execute(code, request.parameters)

        session.code = code
        session.parameters = request.parameters
        session.parameter_schemas = [p.model_dump() for p in param_schemas]
        session.step_url = result.get("step_path", "")
        session.stl_url = result.get("stl_path", "")
        session.gltf_url = result.get("gltf_path", "")
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