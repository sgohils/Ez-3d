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

        from services.session import SessionManager

        session = SessionManager.get(session_id)
        if session is None:
            session = SessionManager.get_last()
        if session is None:
            raise ValueError("No generation session found. Call /generate first.")

        code = session.code
        if parameter_overrides:
            from services.llm_pipeline import substitute_parameters
            code = substitute_parameters(code, parameter_overrides)

        from services.cadquery_sandbox import CadQuerySandbox
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
            "scad": (".scad", "text/plain"),
            "f3d": (".f3d", "application/octet-stream"),
        }
        ext, content_type = ext_map.get(format, (f".{format}", "application/octet-stream"))
        filename = f"model{ext}"

        source_path = result.get(f"{format}_path", "")
        if format == "f3d" and (not source_path or not os.path.exists(source_path)):
            step_path = result.get("step_path", "")
            source_path = self._convert_step_to_f3d(step_path, session_id)

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

    def _convert_step_to_f3d(self, step_path: str, session_id: str) -> str:
        import shutil
        import subprocess

        freecad_bin = shutil.which("freecadcmd") or shutil.which("freecad")
        if not freecad_bin:
            raise FileNotFoundError(
                "F3D export requires FreeCAD (freecadcmd or freecad) to be installed. "
                "Install FreeCAD or use an alternative format (STEP, STL, GLTF, SCAD)."
            )

        f3d_path = step_path.replace(".step", ".f3d")
        conversion_script = (
            "import FreeCAD, Import, Mesh, Part, BRep; "
            "doc = FreeCAD.newDocument(); "
            f"shape = Import.read('{step_path}'); "
            "Part.show(shape); "
            f"doc.saveAs('{f3d_path}'); "
            "FreeCAD.closeDocument(doc.Name)"
        )
        try:
            result = subprocess.run(
                [freecad_bin, "-c", conversion_script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"FreeCAD conversion failed: {result.stderr}"
                )
        except FileNotFoundError:
            raise FileNotFoundError(
                "FreeCAD binary not found. Install FreeCAD to enable F3D export."
            )

        if not os.path.exists(f3d_path):
            raise FileNotFoundError(
                f"F3D file was not created at {f3d_path} after conversion"
            )

        return f3d_path