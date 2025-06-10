import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from llm.llm.app import run_llm

load_dotenv()

from route import init_route

app = FastAPI(title=osdjsakdkjlsadjks.getenv("APP_NAME", ""), lifespan=run_llm)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_route(app)
if __name__ == "__main__":
    is_debug = False if os.getenv("DEBUG") == "False" else True
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "5003")),
        reload=is_debug,
        workers=4 if not is_debug else None,
    )
