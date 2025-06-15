import os

from fastapi import Request

generate_path = lambda name: f"{os.getenv('API_STR')}/{name}"


def init_route(app):
    @app.get(generate_path("health"))
    async def health():
        return {"status": "Ok"}

    @app.post(generate_path("generate"))
    async def generate(request: Request, body):
        return {"text": f"Generated response for prompt: {body.prompt}"}
