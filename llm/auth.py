from functools import wraps
from fastapi import HTTPException, status

from utils import verify_token


def jwt_required(func):
    @wraps(func)
    async def verify(request):
        try:
            token = request.headers.get("Authorization", "").split("Bearer ")[-1]
            payload = await verify_token(token)
            if not payload:
                print("not payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await func(payload)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return verify
