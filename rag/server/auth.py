from functools import wraps

from utils import verify_token, get_error_401


def jwt_required(func):
    @wraps(func)
    async def verify(request):
        try:
            token = request.headers.get("Authorization", "").split("Bearer ")[-1]
            payload = await verify_token(token)
            if not payload:
                raise get_error_401()
            return await func(payload)
        except Exception:
            raise get_error_401()

    return verify
