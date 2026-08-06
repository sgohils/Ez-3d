from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    code: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    parameter_schemas: list[dict[str, Any]] = field(default_factory=list)
    step_url: str = ""
    stl_url: str = ""
    gltf_url: str = ""
    logs: str = ""


class SessionManager:
    _sessions: dict[str, GenerationSession] = {}
    _last_session: GenerationSession | None = None

    @classmethod
    def create(cls, prompt: str, code: str) -> GenerationSession:
        session = GenerationSession(prompt=prompt, code=code)
        cls._sessions[session.session_id] = session
        cls._last_session = session
        return session

    @classmethod
    def get_last(cls) -> GenerationSession | None:
        return cls._last_session

    @classmethod
    def get(cls, session_id: str) -> GenerationSession | None:
        return cls._sessions.get(session_id)

    @classmethod
    def delete(cls, session_id: str) -> None:
        cls._sessions.pop(session_id, None)
        if cls._last_session and cls._last_session.session_id == session_id:
            cls._last_session = None

    @classmethod
    def update_last(cls, **kwargs: Any) -> GenerationSession:
        session = cls._last_session
        if session is None:
            raise ValueError("No generation session exists. Call /generate first.")
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        return session