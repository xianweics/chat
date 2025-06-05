from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from auth import jwt_required
from config import settings

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(f"{settings.API_STR}/generate")
async def generate_text(request: Request, body: GenerateRequest):
    """
    生成文本的端点
    这里应该实现实际的LLM生成逻辑
    
    参数:
    - prompt: 输入提示文本
    - max_tokens: 生成的最大token数量（可选，默认1024）
    - temperature: 生成文本的随机性（可选，默认0.7）
    """
    @jwt_required
    async def protected_generate(user_info, request: Request, body: GenerateRequest):
        print(user_info)
        print(body)
        try:
            # 这里添加实际的LLM处理逻辑
            response = {
                "text": f"Generated response for prompt: {body.prompt}",
                "tokens_used": body.max_tokens
            }
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    return await protected_generate(request=request, body=body)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}
