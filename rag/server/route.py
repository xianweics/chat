from fastapi import Request

from auth import jwt_required
from utils import generate, GenerateRequest, generate_path


def init_route(app):
    @app.get(generate_path("health"))
    async def protected_health(request: Request):
        @jwt_required
        async def health(user_info):
            return {"status": "healthy", "username": user_info.get("username")}

        return await health(request)

    @app.post(generate_path("generate"))
    async def protected_generate(request: Request, body: GenerateRequest):
        @jwt_required
        async def generate_text(user_info):
            return await generate(body)

        return await generate_text(request)
