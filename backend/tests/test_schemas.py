from backend.models.schemas import GenerateResponse, RecompileResponse


def test_generate_response_has_message_field():
    data = {
        "step_url": "http://example.com/output.step",
        "stl_url": "http://example.com/output.sttl",
        "gltf_url": "http://example.com/output.gltf",
        "parameters": [],
        "code": "result = cq.Workplane('XY').box(1, 1, 1)",
        "logs": "",
        "message": "Generated model: test prompt",
    }
    response = GenerateResponse(**data)
    assert response.message == "Generated model: test prompt"


def test_generate_response_has_revision_id_field():
    data = {
        "step_url": "http://example.com/output.step",
        "stl_url": "http://example.com/output.sttl",
        "gltf_url": "http://example.com/output.gltf",
        "parameters": [],
        "code": "result = cq.Workplane('XY').box(1, 1, 1)",
        "logs": "",
        "revision_id": "abc-123",
    }
    response = GenerateResponse(**data)
    assert response.revision_id == "abc-123"
    assert response.model_dump()["revisionId"] == "abc-123"


def test_generate_response_message_defaults_to_none():
    data = {
        "step_url": "http://example.com/output.step",
        "stl_url": "http://example.com/output.sttl",
        "gltf_url": "http://example.com/output.gltf",
        "parameters": [],
        "code": "result = cq.Workplane('XY').box(1, 1, 1)",
        "logs": "",
    }
    response = GenerateResponse(**data)
    assert response.message is None


def test_generate_response_revision_id_defaults_to_none():
    data = {
        "step_url": "http://example.com/output.step",
        "stl_url": "http://example.com/output.sttl",
        "gltf_url": "http://example.com/output.gltf",
        "parameters": [],
        "code": "result = cq.Workplane('XY').box(1, 1, 1)",
        "logs": "",
    }
    response = GenerateResponse(**data)
    assert response.revision_id is None
