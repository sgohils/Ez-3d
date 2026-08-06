from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    parameters: Optional[dict[str, Any]] = None


class ParameterSchema(BaseModel):
    name: str
    value: float
    min: float
    max: float
    step: float


class GenerateResponse(BaseModel):
    step_url: str
    stl_url: str
    gltf_url: str
    parameters: list[ParameterSchema]
    code: str
    logs: str
    revision_id: str


class RecompileRequest(BaseModel):
    parameters: dict[str, Any] = Field(..., min_length=1)


class RecompileResponse(BaseModel):
    step_url: str
    stl_url: str
    gltf_url: str
    parameters: list[ParameterSchema]
    code: str
    logs: str
    revision_id: str


class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(step|stl|gltf)$")


class ExportResponse(BaseModel):
    format: str
    filename: str
    content_type: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    logs: Optional[str] = None