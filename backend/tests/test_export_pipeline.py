from __future__ import annotations

import os
import pytest
from unittest.mock import patch, MagicMock
from backend.services.export_pipeline import ExportPipeline
from backend.services.session import SessionManager, GenerationSession


class TestExportPipeline:
    def teardown_method(self):
        SessionManager._sessions.clear()
        SessionManager._last_session = None

    @patch("backend.services.export_pipeline.SessionManager")
    def test_export_no_session(self, mock_session_manager):
        mock_session_manager.get.return_value = None
        mock_session_manager.get_last.return_value = None
        pipeline = ExportPipeline()
        with pytest.raises(ValueError, match="No generation session found"):
            pipeline.export("nonexistent", "step")

    @patch("backend.services.export_pipeline.SessionManager")
    @patch("backend.services.export_pipeline.CadQuerySandbox")
    def test_export_step_success(self, mock_sandbox_cls, mock_session_manager):
        session = GenerationSession(prompt="test", code="code")
        session.step_url = ""
        mock_session_manager.get.return_value = session
        mock_session_manager.get_last.return_value = session

        sandbox = MagicMock()
        sandbox.execute.return_value = {
            "step_path": "/tmp/output.step",
            "stl_path": "",
            "gltf_path": "",
            "logs": "",
            "working_dir": "/tmp",
        }
        mock_sandbox_cls.return_value = sandbox

        with patch("os.path.exists", return_value=True):
            result = ExportPipeline().export("session-1", "step")

        assert result["format"] == "step"
        assert result["filename"] == "model.step"
        assert result["content_type"] == "application/step"

    @patch("backend.services.export_pipeline.SessionManager")
    @patch("backend.services.export_pipeline.CadQuerySandbox")
    def test_export_with_parameter_overrides(self, mock_sandbox_cls, mock_session_manager):
        session = GenerationSession(prompt="test", code="code", parameters={"x": "10"})
        mock_session_manager.get.return_value = session
        mock_session_manager.get_last.return_value = session

        sandbox = MagicMock()
        sandbox.execute.return_value = {
            "step_path": "/tmp/output.step",
            "stl_path": "",
            "gltf_path": "",
            "logs": "",
            "working_dir": "/tmp",
        }
        mock_sandbox_cls.return_value = sandbox

        with patch("os.path.exists", return_value=True):
            result = ExportPipeline().export("session-1", "step", parameter_overrides={"x": "20"})

        assert result["format"] == "step"

    @patch("backend.services.export_pipeline.SessionManager")
    @patch("backend.services.export_pipeline.CadQuerySandbox")
    def test_export_file_not_found(self, mock_sandbox_cls, mock_session_manager):
        session = GenerationSession(prompt="test", code="code")
        mock_session_manager.get.return_value = session
        mock_session_manager.get_last.return_value = session

        sandbox = MagicMock()
        sandbox.execute.return_value = {
            "step_path": "/tmp/missing.step",
            "stl_path": "",
            "gltf_path": "",
            "logs": "",
            "working_dir": "/tmp",
        }
        mock_sandbox_cls.return_value = sandbox

        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Exported step file not found"):
                ExportPipeline().export("session-1", "step")
