from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import GenerateRequest, GenerateResponse, ParameterSchema
from backend.services.llm_pipeline import LLMPipeline, extract_parameters
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from backend.services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
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
        result = sandbox.execute(code, request.parameters or {})

        session = SessionManager.create(
            prompt=request.prompt,
            code=code,
        )
        session.parameters = request.parameters or {}
        session.parameter_schemas = param_schemas
        session.step_url = result.get("step_path", "")
        session.stl_url = result.get("stl_path", "")
        session.gltf_url = result.get("gltf_path", "")
        session.logs = result.get("logs", "")

        return GenerateResponse(
            step_url=session.step_url,
            stl_url=session.stl_url,
            gltf_url=session.gltf_url,
            parameters=param_schemas,
            code=code,
            logs=result.get("logs", ""),
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