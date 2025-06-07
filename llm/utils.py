from fastapi import HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from typing import Optional

from starlette import status
from config import settings


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="The input prompt text")
    temperature: Optional[float] = Field(
        0.7, description="Temperature for text generation"
    )


async def generate(body):
    try:
        response = {"text": f"Generated response for prompt: {body.prompt}"}
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def verify_token(token):
    try:
        payload = jwt.decode(
            token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


generate_path = lambda name: f"{settings.API_STR}/{name}"
