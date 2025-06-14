from dotenv import load_dotenv

load_dotenv()

from rag.logger import load_logger

load_logger()

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag.llm.main import lifespan
from route import init_route

app = FastAPI(title=os.getenv("APP_NAME", ""), lifespan=lifespan)

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
        "main:app",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", 5003)),
        reload=is_debug,
        workers=4 if not is_debug else None,
    )
