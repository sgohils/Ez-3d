from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.services.export_pipeline import ExportPipeline


class TestExportPipeline:
    def test_export_raises_no_session(self) -> None:
        pipeline = ExportPipeline()
        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = None
            mock_sm.get_last.return_value = None
            with pytest.raises(ValueError, match="No generation session"):
                pipeline.export("session1", "step")

    def test_export_returns_dict_keys(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)\ncq.exporters.export(result, 'output.step')"

        mock_result = {
            "step_path": "/tmp/output.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=True):
                    result = pipeline.export("s1", "step")

        assert result["format"] == "step"
        assert "filename" in result
        assert "content_type" in result

    def test_export_format_step(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)\ncq.exporters.export(result, 'output.step')"

        mock_result = {
            "step_path": "/tmp/output.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=True):
                    result = pipeline.export("s1", "step")

        assert result["filename"] == "model.step"
        assert result["content_type"] == "application/step"

    def test_export_format_stl(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)\ncq.exporters.export(result, 'output.stl')"

        mock_result = {
            "step_path": "/tmp/output.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=True):
                    result = pipeline.export("s1", "stl", tolerance=0.001)

        assert result["filename"] == "model.stl"
        assert result["content_type"] == "application/sla"

    def test_export_format_gltf(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)\ncq.exporters.export(result, 'output.gltf')"

        mock_result = {
            "step_path": "/tmp/output.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=True):
                    result = pipeline.export("s1", "gltf")

        assert result["filename"] == "model.gltf"
        assert result["content_type"] == "model/gltf+json"

    def test_export_file_not_found(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "import cadquery as cq\nresult = cq.Workplane('XY').box(1,1,1)"

        mock_result = {
            "step_path": "/tmp/missing.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=False):
                    with pytest.raises(FileNotFoundError, match="Exported step file not found"):
                        pipeline.export("s1", "step")

    def test_export_with_parameter_overrides(self) -> None:
        pipeline = ExportPipeline()
        mock_session = MagicMock()
        mock_session.session_id = "s1"
        mock_session.code = "length: float = 80.0\nresult = cq.Workplane('XY').box(length, 60, 10)"

        mock_result = {
            "step_path": "/tmp/output.step",
            "stl_path": "/tmp/output.stl",
            "gltf_path": "/tmp/output.gltf",
            "logs": "",
            "working_dir": "/tmp",
        }

        with patch("backend.services.session.SessionManager") as mock_sm:
            mock_sm.get.return_value = mock_session
            mock_sm.get_last.return_value = mock_session
            with patch("backend.services.cadquery_sandbox.CadQuerySandbox") as mock_sandbox_cls:
                mock_sandbox = MagicMock()
                mock_sandbox.execute.return_value = mock_result
                mock_sandbox_cls.return_value = mock_sandbox
                with patch("os.path.exists", return_value=True):
                    result = pipeline.export(
                        "s1", "step", parameter_overrides={"length": 100.0}
                    )

        assert result["format"] == "step"
