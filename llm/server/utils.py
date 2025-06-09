import os
from fastapi import HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from typing import Optional

from starlette import status

get_error_401 = lambda: HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
get_error_500 = lambda e: HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
)


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
        raise get_error_500(e)


async def verify_token(token):
    try:
        with open("../../public.pem", "rb") as f:
            public_key = f.read()
        payload = jwt.decode(
            token, public_key, algorithms=[os.getenv("ALGORITHM", "RS256")]
        )
        return payload
    except JWTError:
        return None


generate_path = lambda name: f"{os.getenv('API_STR', '/llm')}/{name}"
