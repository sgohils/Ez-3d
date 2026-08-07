from __future__ import annotations

import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError


class TestCadQuerySandbox:
    def teardown_method(self):
        CadQuerySandbox._outputs_dir = os.environ.get("CADGEN_OUTPUT_DIR", "/tmp/cadgen_outputs")
        CadQuerySandbox._sandbox_url = os.environ.get("CADGEN_SANDBOX_URL", "")

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "stdout"
        mock_result.stderr = "stderr"
        mock_run.return_value = mock_result

        sandbox = CadQuerySandbox()
        sandbox._outputs_dir = "/tmp/test_outputs"

        with patch("os.path.exists", side_effect=lambda p: p.endswith((".step", ".stl", ".gltf"))):
            result = sandbox.execute("code here", session_id="test-session")

        assert "step_path" in result
        assert "logs" in result
        assert result["logs"] == "stdoutstderr"

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "error output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        sandbox = CadQuerySandbox()
        sandbox._outputs_dir = "/tmp/test_outputs"

        with pytest.raises(SandboxExecutionError, match="return code 1"):
            sandbox.execute("code here", session_id="test-session")

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=120)

        sandbox = CadQuerySandbox()
        sandbox._outputs_dir = "/tmp/test_outputs"

        with pytest.raises(SandboxExecutionError, match="timed out after 120s"):
            sandbox.execute("code here", session_id="test-session")

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("python not found")

        sandbox = CadQuerySandbox()
        sandbox._outputs_dir = "/tmp/test_outputs"

        with pytest.raises(SandboxExecutionError, match="CadQuery script not found"):
            sandbox.execute("code here", session_id="test-session")

    @patch("backend.services.cadquery_sandbox.json.loads")
    @patch("backend.services.cadquery_sandbox.urllib.request.urlopen")
    def test_execute_remote(self, mock_urlopen, mock_json_loads):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"step_path": "/remote/step", "stl_path": "", "gltf_path": "", "logs": "", "working_dir": "/remote"}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        mock_json_loads.return_value = {
            "step_path": "/remote/step",
            "stl_path": "",
            "gltf_path": "",
            "logs": "remote logs",
            "working_dir": "/remote",
        }

        sandbox = CadQuerySandbox()
        sandbox._sandbox_url = "http://localhost:8000"
        result = sandbox._execute_remote("code", "session-1", {})

        assert result["step_path"] == "/remote/step"
        assert result["logs"] == "remote logs"

    def test_inject_export_options(self):
        sandbox = CadQuerySandbox()
        code = 'cq.exporters.export(result, "output.stl", tolerance=0.05)'
        result = sandbox._inject_export_options(code, {"stl_tolerance": 0.1})
        assert "tolerance=0.1" in result

    def test_substitute_params(self):
        sandbox = CadQuerySandbox()
        code = "x = 10\ny = x + 5"
        result = sandbox._substitute_params(code, {"x": "20"})
        assert "x = 20" in result
        assert "y = x + 5" not in result
