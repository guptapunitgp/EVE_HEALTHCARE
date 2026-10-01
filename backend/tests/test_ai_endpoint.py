import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes import ai
from app.schemas.ai import ChatMessage, EducationChatRequest


def test_education_endpoint_reports_missing_provider_configuration(monkeypatch):
    monkeypatch.setattr(ai.settings, "GEMINI_API_KEY", "")
    request = EducationChatRequest(messages=[ChatMessage(role="user", text="What is a CBC?")])
    with pytest.raises(HTTPException) as error:
        asyncio.run(ai.education_chat(request, SimpleNamespace(id="user-test")))
    assert error.value.status_code == 503
