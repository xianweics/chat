from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from config import settings
from route import init_route

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_route(app)
