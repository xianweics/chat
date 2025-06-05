import uvicorn

from config import settings

if __name__ == "__main__":
    uvicorn.run(
        settings.APP_NAME +":app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True, 
        workers=4
    )