from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request

from backend.models.schemas import GenerateRequest, GenerateResponse, ParameterSchema
from backend.services.llm_pipeline import LLMPipeline, extract_parameters
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from backend.services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/", response_model=GenerateResponse)
async def generate(request: GenerateRequest, http_request: Request) -> GenerateResponse:
    try:
        llm = LLMPipeline()
        code = llm.generate_code(request.prompt, request.parameters)

        param_schemas = extract_parameters(code)
        if not param_schemas and request.parameters:
            for name, value in request.parameters.items():
                param_schemas.append(ParameterSchema(
                    name=name,
                    value=float(value),
                    min=0.1,
                    max=100.0,
                    step=0.1,
                ))

        sandbox = CadQuerySandbox()
        session = SessionManager.create(
            prompt=request.prompt,
            code=code,
        )
        session.parameters = request.parameters or {}
        session.parameter_schemas = param_schemas

        result = sandbox.execute(code, request.parameters or {}, session_id=session.session_id)

        base_url = str(http_request.base_url).rstrip("/")
        session.step_url = f"{base_url}/outputs/{session.session_id}/output.step" if result.get("step_path") and os.path.exists(result.get("step_path", "")) else ""
        session.stl_url = f"{base_url}/outputs/{session.session_id}/output.stl" if result.get("stl_path") and os.path.exists(result.get("stl_path", "")) else ""
        session.gltf_url = f"{base_url}/outputs/{session.session_id}/output.gltf" if result.get("gltf_path") and os.path.exists(result.get("gltf_path", "")) else ""
        session.logs = result.get("logs", "")

        return GenerateResponse(
            step_url=session.step_url,
            stl_url=session.stl_url,
            gltf_url=session.gltf_url,
            parameters=param_schemas,
            code=code,
            logs=result.get("logs", ""),
            message=f"Generated model: {request.prompt}",
            revision_id=session.session_id,
        )
    except SandboxExecutionError as exc:
        logger.error("Sandbox execution failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CadQuery execution failed",
                "detail": str(exc),
                "logs": exc.logs,
            },
        )
    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Generation failed",
                "detail": str(exc),
                "logs": "",
            },
        )