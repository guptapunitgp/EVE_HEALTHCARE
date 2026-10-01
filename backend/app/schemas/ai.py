from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(min_length=1, max_length=2000)


class EducationChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=12)


class EducationChatResponse(BaseModel):
    answer: str
    model: str
    disclaimer: str
