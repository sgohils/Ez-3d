from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from backend.services.cadquery_sandbox import CadQuerySandbox, SandboxExecutionError


class TestCadQuerySandboxExecute:
    @patch("backend.services.cadquery_sandbox.subprocess.run")
    @patch("backend.services.cadquery_sandbox.os.makedirs")
    @patch("backend.services.cadquery_sandbox.os.path.exists")
    def test_execute_success(
        self, mock_exists: MagicMock, mock_makedirs: MagicMock, mock_run: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        mock_exists.return_value = True

        sandbox = CadQuerySandbox()
        with patch("builtins.open", MagicMock()):
            result = sandbox.execute("print('hello')")

        assert "step_path" in result
        assert "stl_path" in result
        assert "gltf_path" in result
        assert "logs" in result

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error output",
            stderr="traceback here",
        )

        sandbox = CadQuerySandbox()
        with patch("builtins.open", MagicMock()):
            with pytest.raises(SandboxExecutionError) as exc_info:
                sandbox.execute("bad code")
        assert "return code 1" in str(exc_info.value)

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_timeout(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["python"], timeout=120)

        sandbox = CadQuerySandbox()
        with pytest.raises(SandboxExecutionError) as exc_info:
            sandbox.execute("slow code")
        assert "timed out" in str(exc_info.value).lower()

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_with_parameters(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        sandbox = CadQuerySandbox()
        with patch("builtins.open", MagicMock()):
            result = sandbox.execute("x = 1.0", parameters={"x": 42.0})

        assert "logs" in result

    def test_sandbox_initialization(self) -> None:
        sandbox = CadQuerySandbox()
        assert sandbox is not None

    @patch("backend.services.cadquery_sandbox.subprocess.run")
    def test_execute_generates_session_id(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        sandbox = CadQuerySandbox()
        with patch("builtins.open", MagicMock()):
            result = sandbox.execute("print('hello')")

        assert result is not None
        assert "working_dir" in result

    def test_sandbox_execution_error_has_logs(self) -> None:
        error = SandboxExecutionError("test error", logs="some logs")
        assert str(error) == "test error"
        assert error.logs == "some logs"
