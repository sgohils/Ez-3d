from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class ExportPipeline:
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def export(
        self,
        session_id: str,
        format: str,
        parameter_overrides: dict[str, Any] | None = None,
        tolerance: float = 0.01,
    ) -> dict[str, Any]:
        self._logger.info("Exporting session %s as %s", session_id, format)

        from backend.services.session import SessionManager

        session = SessionManager.get(session_id)
        if session is None:
            session = SessionManager.get_last()
        if session is None:
            raise ValueError("No generation session found. Call /generate first.")

        code = session.code
        if parameter_overrides:
            from backend.services.llm_pipeline import substitute_parameters
            code = substitute_parameters(code, parameter_overrides)

        from backend.services.cadquery_sandbox import CadQuerySandbox
        sandbox = CadQuerySandbox()
        export_options: dict[str, Any] = {}
        if format == "stl":
            export_options["stl_tolerance"] = tolerance

        result = sandbox.execute(
            code,
            parameter_overrides,
            session_id=session_id or session.session_id,
            export_options=export_options,
        )

        ext_map = {
            "step": (".step", "application/step"),
            "stl": (".stl", "application/sla"),
            "gltf": (".gltf", "model/gltf+json"),
        }
        ext, content_type = ext_map.get(format, (f".{format}", "application/octet-stream"))
        filename = f"model{ext}"

        source_path = result.get(f"{format}_path", "")
        if not source_path or not os.path.exists(source_path):
            raise FileNotFoundError(
                f"Exported {format} file not found at {source_path}"
            )

        return {
            "format": format,
            "filename": filename,
            "content_type": content_type,
            "file_path": source_path,
            "logs": result.get("logs", ""),
        }
