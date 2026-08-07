from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from backend.services.export_pipeline import ExportPipeline


@pytest.fixture
def pipeline() -> ExportPipeline:
    return ExportPipeline()


@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock()
    session.session_id = "s1"
    session.code = "import cadquery as cq\nlength = 80.0\nresult = cq.Workplane('XY').box(length, 60, 10)"
    return session


@pytest.fixture
def mock_sandbox_result() -> dict:
    return {
        "step_path": "/tmp/output.step",
        "stl_path": "/tmp/output.stl",
        "gltf_path": "/tmp/output.gltf",
        "logs": "",
        "working_dir": "/tmp",
    }


@pytest.fixture
def mock_sandbox(mock_session):
    with patch("backend.services.session.SessionManager") as mock_sm, \
         patch("backend.services.cadquery_sandbox.subprocess.run") as mock_run, \
         patch("backend.services.cadquery_sandbox.os.makedirs"), \
         patch("builtins.open"):
        mock_sm.get.return_value = mock_session
        mock_sm.get_last.return_value = mock_session
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock_sm, mock_run


def test_export_raises_no_session(pipeline: ExportPipeline) -> None:
    with patch("backend.services.session.SessionManager") as mock_sm:
        mock_sm.get.return_value = None
        mock_sm.get_last.return_value = None
        with pytest.raises(ValueError, match="No generation session"):
            pipeline.export("session1", "step")


def test_export_returns_dict_keys(
    pipeline: ExportPipeline,
    mock_sandbox: tuple,
) -> None:
    mock_sm, mock_run = mock_sandbox
    with patch("backend.services.cadquery_sandbox.os.path.exists", return_value=True):
        result = pipeline.export("s1", "step")

    assert result["format"] == "step"
    assert "filename" in result
    assert "content_type" in result


def test_export_format_step(
    pipeline: ExportPipeline,
    mock_sandbox: tuple,
) -> None:
    mock_sm, mock_run = mock_sandbox
    with patch("backend.services.cadquery_sandbox.os.path.exists", return_value=True):
        result = pipeline.export("s1", "step")

    assert result["filename"] == "model.step"
    assert result["content_type"] == "application/step"


def test_export_format_stl(
    pipeline: ExportPipeline,
    mock_sandbox: tuple,
) -> None:
    mock_sm, mock_run = mock_sandbox
    with patch("backend.services.cadquery_sandbox.os.path.exists", return_value=True):
        result = pipeline.export("s1", "stl", tolerance=0.001)

    assert result["filename"] == "model.stl"
    assert result["content_type"] == "application/sla"


def test_export_format_gltf(
    pipeline: ExportPipeline,
    mock_sandbox: tuple,
) -> None:
    mock_sm, mock_run = mock_sandbox
    with patch("backend.services.cadquery_sandbox.os.path.exists", return_value=True):
        result = pipeline.export("s1", "gltf")

    assert result["filename"] == "model.gltf"
    assert result["content_type"] == "model/gltf+json"


def test_export_file_not_found(
    pipeline: ExportPipeline,
    mock_sandbox: tuple,
) -> None:
    mock_sm, mock_run = mock_sandbox
    with patch("backend.services.cadquery_sandbox.os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Exported step file not found"):
            pipeline.export("s1", "step")


def test_export_with_parameter_overrides(
    pipeline: ExportPipeline,
    mock_session: MagicMock,
    mock_sandbox_result: dict,
) -> None:
    captured_code = None

    def capture_open(file, mode="r", *args, **kwargs):
        if "w" in mode and file.endswith(".py"):
            cm = MagicMock()
            f = MagicMock()

            def write(data):
                nonlocal captured_code
                captured_code = data
                return len(data)

            f.write = write
            cm.__enter__ = MagicMock(return_value=f)
            cm.__exit__ = MagicMock(return_value=False)
            return cm
        return open(file, mode, *args, **kwargs)

    with patch("backend.services.session.SessionManager") as mock_sm:
        mock_sm.get.return_value = mock_session
        mock_sm.get_last.return_value = mock_session
        with patch("backend.services.cadquery_sandbox.subprocess.run") as mock_run, \
             patch("backend.services.cadquery_sandbox.os.path.exists", return_value=True), \
             patch("backend.services.cadquery_sandbox.os.makedirs"), \
             patch("builtins.open", side_effect=capture_open):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = pipeline.export(
                "s1", "step", parameter_overrides={"length": 100.0}
            )

    assert result["format"] == "step"
    assert captured_code is not None
    assert "100.0" in captured_code


def test_export_parameter_overrides_not_passed_to_sandbox(
    pipeline: ExportPipeline,
    mock_session: MagicMock,
    mock_sandbox_result: dict,
) -> None:
    with patch("backend.services.session.SessionManager") as mock_sm:
        mock_sm.get.return_value = mock_session
        mock_sm.get_last.return_value = mock_session
        with patch(
            "backend.services.cadquery_sandbox.CadQuerySandbox"
        ) as mock_sandbox_cls:
            mock_sandbox = MagicMock()
            mock_sandbox.execute.return_value = mock_sandbox_result
            mock_sandbox_cls.return_value = mock_sandbox
            with patch("os.path.exists", return_value=True):
                pipeline.export(
                    "s1", "step", parameter_overrides={"length": 100.0}
                )

    mock_sandbox.execute.assert_called_once()
    call_kwargs = mock_sandbox.execute.call_args
    assert call_kwargs[0][1] is None
