from __future__ import annotations

import pytest
from backend.services.session import SessionManager, GenerationSession


class TestSessionManager:
    def teardown_method(self):
        SessionManager._sessions.clear()
        SessionManager._last_session = None

    def test_create_session(self):
        session = SessionManager.create("test prompt", "code here")
        assert session.prompt == "test prompt"
        assert session.code == "code here"
        assert session.session_id in SessionManager._sessions

    def test_get_session(self):
        session = SessionManager.create("test prompt", "code here")
        retrieved = SessionManager.get(session.session_id)
        assert retrieved is session

    def test_get_missing_session(self):
        assert SessionManager.get("nonexistent") is None

    def test_get_last_session(self):
        session = SessionManager.create("test prompt", "code here")
        last = SessionManager.get_last()
        assert last is session

    def test_get_last_no_session(self):
        assert SessionManager.get_last() is None

    def test_update_last(self):
        session = SessionManager.create("test prompt", "code here")
        updated = SessionManager.update_last(logs="some logs")
        assert updated.logs == "some logs"

    def test_update_last_no_session(self):
        with pytest.raises(ValueError, match="No generation session exists"):
            SessionManager.update_last(logs="some logs")
