from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.services.export_pipeline import ExportPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/")
async def export_model(
    export_format: str = Query(..., pattern="^(step|stl|gltf)$"),
    session_id: str | None = Query(None),
    tolerance: float = Query(0.01, ge=1e-6, le=1.0),
) -> StreamingResponse:
    try:
        pipeline = ExportPipeline()
        overrides: dict[str, Any] = {}
        if session_id:
            from backend.services.session import SessionManager
            session = SessionManager.get(session_id)
            if session and session.parameters:
                overrides = session.parameters

        result = pipeline.export(
            session_id=session_id or "",
            format=export_format,
            parameter_overrides=overrides if overrides else None,
            tolerance=tolerance,
        )

        file_path = result["file_path"]
        filename = result["filename"]
        content_type = result["content_type"]

        def file_iterator() -> Any:
            with open(file_path, "rb") as f:
                chunk_size = 65536
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        return StreamingResponse(
            file_iterator(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            },
        )
    except FileNotFoundError as exc:
        logger.error("Export file not found: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Export file not found",
                "detail": str(exc),
                "logs": "",
            },
        )
    except ValueError as exc:
        logger.error("Export failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Export failed",
                "detail": str(exc),
                "logs": "",
            },
        )
    except Exception as exc:
        logger.error("Export failed unexpectedly: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Export failed unexpectedly",
                "detail": str(exc),
                "logs": "",
            },
        )