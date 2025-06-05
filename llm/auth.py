from functools import wraps
from fastapi import HTTPException, status, Request
from jose import JWTError, jwt

from config import settings

async def verify_token(token):
    try:
        payload = jwt.decode(
            token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def jwt_required(func):
    @wraps(func)
    async def decorated(*args, **kwargs):
        token = kwargs.get('request').headers.get("Authorization", "").split("Bearer ")[-1]
        payload = await verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await func(payload, *args, **kwargs)
    return decorated