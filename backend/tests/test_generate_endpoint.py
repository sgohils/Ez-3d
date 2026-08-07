from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_generate_endpoint_returns_message_and_revision_id():
    mock_session = MagicMock()
    mock_session.session_id = "test-session-123"
    mock_session.step_url = "http://localhost:8000/outputs/test-session-123/output.step"
    mock_session.stl_url = "http://localhost:8000/outputs/test-session-123/output.stl"
    mock_session.gltf_url = "http://localhost:8000/outputs/test-session-123/output.gltf"
    mock_session.logs = ""

    mock_sandbox = MagicMock()
    mock_sandbox.execute.return_value = {
        "step_path": "/tmp/output.step",
        "stl_path": "/tmp/output.stl",
        "gltf_path": "/tmp/output.gltf",
        "logs": "",
    }

    mock_llm = MagicMock()
    mock_llm.generate_code.return_value = "result = cq.Workplane('XY').box(1, 1, 1)"

    with (
        patch("backend.api.v1.endpoints.generate.LLMPipeline", return_value=mock_llm),
        patch("backend.api.v1.endpoints.generate.CadQuerySandbox", return_value=mock_sandbox),
        patch("backend.api.v1.endpoints.generate.SessionManager.create", return_value=mock_session),
        patch("backend.api.v1.endpoints.generate.extract_parameters", return_value=[]),
        patch("os.path.exists", return_value=True),
    ):
        response = client.post(
            "/api/v1/generate/",
            json={"prompt": "a simple box", "parameters": None},
        )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Generated model: a simple box"
    assert "revisionId" in data
    assert data["revisionId"] == "test-session-123"
