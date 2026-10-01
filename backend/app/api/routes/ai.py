import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.redis import redis_client
from app.models.user import User
from app.schemas.ai import EducationChatRequest, EducationChatResponse

router = APIRouter(prefix="/ai", tags=["Educational assistant"])
DISCLAIMER = "For general education only. This is not a diagnosis or a substitute for advice from a qualified healthcare professional."
SYSTEM_INSTRUCTION = (
    "You are EVE's health education assistant. Explain general health and diagnostic-test concepts in plain, calm language. "
    "Do not diagnose, prescribe, recommend changing treatment, or interpret an individual's symptoms or results as a diagnosis. "
    "For urgent symptoms advise contacting local emergency services. Encourage users to discuss personal results with a qualified clinician. "
    "Do not request identifiers or unnecessary sensitive data. Keep responses concise."
)


@router.post("/education", response_model=EducationChatResponse)
async def education_chat(
    request: EducationChatRequest,
    current_user: User = Depends(get_current_user),
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Educational assistant is not configured")
    try:
        rate_key = f"ai-rate:{current_user.id}"
        count = await redis_client.incr(rate_key)
        if count == 1:
            await redis_client.expire(rate_key, 60)
        if count > 12:
            raise HTTPException(status_code=429, detail="Please wait a minute before asking another question")
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=503, detail="Rate limiter is unavailable") from error

    contents = [{"role": message.role, "parts": [{"text": message.text}]} for message in request.messages]
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                endpoint,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                    "contents": contents,
                    "generationConfig": {"temperature": 0.25, "maxOutputTokens": 512},
                },
            )
        response.raise_for_status()
        data = response.json()
        answer = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if not answer:
            raise ValueError("empty response")
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        if status_code == 429:
            raise HTTPException(status_code=503, detail="Educational assistant is busy; try again shortly") from error
        raise HTTPException(status_code=502, detail="Educational assistant could not answer this request") from error
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
        raise HTTPException(status_code=502, detail="Educational assistant response was unavailable") from error
    return EducationChatResponse(answer=answer, model=settings.GEMINI_MODEL, disclaimer=DISCLAIMER)
