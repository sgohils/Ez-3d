from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request

from backend.models.schemas import GenerateRequest, GenerateResponse, ParameterSchema
from backend.services.llm_pipeline import LLMPipeline, MAX_REPAIR_RETRIES, extract_parameters, intercept_oc_errors
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError
from backend.services.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generate"])


def _build_param_schemas(code: str, request_parameters: dict | None) -> list[ParameterSchema]:
    param_schemas = extract_parameters(code)
    if not param_schemas and request_parameters:
        for name, value in request_parameters.items():
            param_schemas.append(ParameterSchema(
                name=name,
                value=float(value),
                min=0.1,
                max=100.0,
                step=0.1,
            ))
    return param_schemas


def _set_session_urls(session, result: dict, base_url: str, session_id: str) -> None:
    session.step_url = (
        f"{base_url}/outputs/{session_id}/output.step"
        if result.get("step_path") and os.path.exists(result.get("step_path", ""))
        else ""
    )
    session.stl_url = (
        f"{base_url}/outputs/{session_id}/output.stl"
        if result.get("stl_path") and os.path.exists(result.get("stl_path", ""))
        else ""
    )
    session.gltf_url = (
        f"{base_url}/outputs/{session_id}/output.gltf"
        if result.get("gltf_path") and os.path.exists(result.get("gltf_path", ""))
        else ""
    )
    session.logs = result.get("logs", "")


@router.post("/", response_model=GenerateResponse)
async def generate(request: GenerateRequest, http_request: Request) -> GenerateResponse:
    llm = LLMPipeline()
    sandbox = CadQuerySandbox()
    parameters = request.parameters or {}
    base_url = str(http_request.base_url).rstrip("/")

    code = llm.generate_code(request.prompt, parameters)
    param_schemas = _build_param_schemas(code, parameters)

    session = SessionManager.create(
        prompt=request.prompt,
        code=code,
    )
    session.parameters = parameters
    session.parameter_schemas = [
        {"name": s.name, "value": s.value, "min": s.min, "max": s.max, "step": s.step}
        for s in param_schemas
    ]
    session.max_retries = MAX_REPAIR_RETRIES

    error_type: str | None = None
    repair_hints: list[str] | None = None

    for attempt in range(MAX_REPAIR_RETRIES + 1):
        session.retry_count = attempt
        try:
            result = sandbox.execute(code, parameters, session_id=session.session_id)

            _set_session_urls(session, result, base_url, session.session_id)

            return GenerateResponse(
                step_url=session.step_url,
                stl_url=session.stl_url,
                gltf_url=session.gltf_url,
                parameters=param_schemas,
                code=code,
                logs=result.get("logs", ""),
                message=f"Generated model: {request.prompt}",
                revision_id=session.session_id,
                retry_count=attempt,
                max_retries=MAX_REPAIR_RETRIES,
                error_type=error_type,
                repair_hints=repair_hints,
            )
        except SandboxExecutionError as exc:
            error_logs = exc.logs or str(exc)
            error_type = _classify_error(error_logs)
            repair_hints = intercept_oc_errors(error_logs)

            logger.warning(
                "Sandbox execution failed on attempt %d/%d: %s",
                attempt + 1,
                MAX_REPAIR_RETRIES + 1,
                exc,
                exc_info=True,
            )

            if attempt < MAX_REPAIR_RETRIES:
                logger.info("Attempting LLM auto-repair (attempt %d)...", attempt + 1)
                try:
                    code = llm.repair_code(
                        code=code,
                        error_logs=error_logs,
                        prompt=request.prompt,
                        hints=repair_hints,
                    )
                    param_schemas = _build_param_schemas(code, parameters)
                    session.code = code
                    session.parameter_schemas = [
                        {"name": s.name, "value": s.value, "min": s.min, "max": s.max, "step": s.step}
                        for s in param_schemas
                    ]
                except Exception as repair_exc:
                    logger.error("LLM auto-repair failed: %s", repair_exc, exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "CadQuery execution failed and auto-repair failed",
                            "detail": str(repair_exc),
                            "logs": error_logs,
                            "retry_count": attempt,
                            "max_retries": MAX_REPAIR_RETRIES,
                            "error_type": error_type,
                            "repair_hints": repair_hints,
                        },
                    )
            else:
                logger.error(
                    "All %d repair attempts exhausted. Returning error to user.",
                    MAX_REPAIR_RETRIES,
                )
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "CadQuery execution failed after maximum repair attempts",
                        "detail": str(exc),
                        "logs": error_logs,
                        "retry_count": attempt,
                        "max_retries": MAX_REPAIR_RETRIES,
                        "error_type": error_type,
                        "repair_hints": repair_hints,
                    },
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Generation failed: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Generation failed",
                    "detail": str(exc),
                    "logs": "",
                    "retry_count": 0,
                    "max_retries": MAX_REPAIR_RETRIES,
                },
            )


def _classify_error(error_logs: str) -> str:
    lower = error_logs.lower()
    if "standard_constructionerror" in lower or "fillet radius" in lower:
        return "OpenCascadeError.FilletRadiusTooLarge"
    if "nonmanifold" in lower or "non-manifold" in lower:
        return "GeometryError.NonManifold"
    if "timeout" in lower:
        return "ExecutionError.Timeout"
    return "Unknown"
