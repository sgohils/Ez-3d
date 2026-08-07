from __future__ import annotations

import uuid

import pytest

from backend.services.session import GenerationSession, SessionManager


class TestGenerationSession:
    def test_default_session_id_is_uuid(self) -> None:
        session = GenerationSession()
        assert isinstance(session.session_id, str)
        assert len(session.session_id) > 0

    def test_default_values(self) -> None:
        session = GenerationSession()
        assert session.prompt == ""
        assert session.code == ""
        assert session.parameters == {}
        assert session.parameter_schemas == []
        assert session.step_url == ""
        assert session.stl_url == ""
        assert session.gltf_url == ""
        assert session.logs == ""

    def test_custom_values(self) -> None:
        session = GenerationSession(
            prompt="make a box",
            code="import cadquery as cq",
            step_url="/step",
        )
        assert session.prompt == "make a box"
        assert session.code == "import cadquery as cq"
        assert session.step_url == "/step"


class TestSessionManager:
    def setup_method(self) -> None:
        SessionManager._sessions = {}
        SessionManager._last_session = None

    def test_create_session(self) -> None:
        session = SessionManager.create("prompt", "code")
        assert session.prompt == "prompt"
        assert session.code == "code"
        assert isinstance(session.session_id, str)

    def test_create_stores_session(self) -> None:
        session = SessionManager.create("prompt", "code")
        retrieved = SessionManager.get(session.session_id)
        assert retrieved is session

    def test_get_nonexistent_returns_none(self) -> None:
        result = SessionManager.get("nonexistent-id")
        assert result is None

    def test_get_last_after_create(self) -> None:
        session = SessionManager.create("prompt", "code")
        last = SessionManager.get_last()
        assert last is session

    def test_get_last_initially_none(self) -> None:
        assert SessionManager.get_last() is None

    def test_update_last(self) -> None:
        session = SessionManager.create("prompt", "code")
        updated = SessionManager.update_last(code="new code", logs="some logs")
        assert updated.code == "new code"
        assert updated.logs == "some logs"

    def test_update_last_no_session_raises(self) -> None:
        with pytest.raises(ValueError, match="No generation session"):
            SessionManager.update_last(code="new code")

    def test_multiple_sessions(self) -> None:
        s1 = SessionManager.create("prompt1", "code1")
        s2 = SessionManager.create("prompt2", "code2")
        assert SessionManager.get(s1.session_id) is s1
        assert SessionManager.get(s2.session_id) is s2
        assert SessionManager.get_last() is s2

    def test_create_generates_unique_ids(self) -> None:
        s1 = SessionManager.create("p", "c")
        s2 = SessionManager.create("p", "c")
        assert s1.session_id != s2.session_id
