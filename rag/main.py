from dotenv import load_dotenv

load_dotenv()

from logger import load_logger

log = load_logger()

from uuid import UUID
import os
from langgraph.graph.state import CompiledStateGraph
from langgraph.constants import END
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
from typing import Optional, Any, AsyncGenerator
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from workflow import create_graph
from utils.db import run_db, ConnectionPoolManager
from utils.llms import get_llm
from utils.tools import get_tools
from workflow_config import WorkFlow
from rag.utils.config import AIMessageRole
from rag.utils.utils import filter_messages


class Response(BaseModel):
    code: int
    message: str
    success: bool = False


class CreateChatRequest(BaseModel):
    content: str
    stream: Optional[bool] = False
    session_id: UUID


@asynccontextmanager
async def lifespan(fapp: FastAPI):
    llm_chat, llm_embedding = get_llm()
    tools = get_tools(llm_embedding)
    db_pool = await run_db()
    fapp.state.db_pool = db_pool
    fapp.state.graph = create_graph(llm_chat, tools)
    yield
    if db_pool:
        await db_pool.close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    log.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content=Response(
            code=exc.status_code, message=exc.detail, success=False
        ).model_dump(),
    )


SYSTEM_ERROR_MESSAGE = "System error"
SYSTEM_SUCCESS_MESSAGE = "Success"

SYSTEM_ERROR_CONTENT = Response(
    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message=SYSTEM_ERROR_MESSAGE,
    success=False,
).model_dump()

SYSTEM_SUCCESS_CONTENT = Response(
    code=status.HTTP_200_OK,
    message=SYSTEM_SUCCESS_MESSAGE,
    success=True,
).model_dump()


@app.exception_handler(Exception)
async def exception_handler(_: Request, exc: Exception) -> JSONResponse:
    log.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=SYSTEM_ERROR_CONTENT,
    )


async def get_db_pool(request: Request) -> ConnectionPoolManager:
    return request.app.state.db_pool


async def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


def generate_invoke_payload(
    payload: CreateChatRequest, histories: list[BaseMessage]
) -> dict[str, Any]:
    return {
        "messages": histories + [HumanMessage(payload.content)],
        "rewrite_count": 0,
        "error": False,
        "session_id": payload.session_id,
    }


async def get_histories(
    db_pool: ConnectionPoolManager, chat_id: UUID
) -> list[BaseMessage]:
    db_history = await db_pool.get_chats(chat_id, 30, "desc") or []
    history = []
    for item in db_history:
        item.role == AIMessageRole.USER and history.append(HumanMessage(item.content))
        item.role == AIMessageRole.AI and history.append(AIMessage(item.content))
    return filter_messages(history)


async def non_stream_response(
    payload: CreateChatRequest,
    graph: CompiledStateGraph,
    db_pool: ConnectionPoolManager,
    histories: list[BaseMessage],
) -> dict[str, Any]:
    try:
        result = await graph.ainvoke(
            generate_invoke_payload(payload, histories),
        )
        next_steps = result.get("next_steps", [])
        next_steps = next_steps[0] if len(next_steps) else None
        last_message = result["messages"][-1]
        if next_steps == END and not last_message.tool_calls:
            content = last_message.content
            await db_pool.save_chat(
                session_id=payload.session_id,
                role=AIMessageRole.AI,
                content=content,
            )
            return {
                **SYSTEM_SUCCESS_CONTENT,
                "data": {
                    "content": content,
                    "finish": True,
                },
            }
        else:
            content = "No response"
            await db_pool.save_chat(
                session_id=payload.session_id,
                role=AIMessageRole.AI,
                content=content,
            )
            return {
                **SYSTEM_SUCCESS_CONTENT,
                "data": {
                    "content": content,
                    "finish": True,
                },
            }
    except Exception as e:
        raise e


async def stream_response(
    payload: CreateChatRequest,
    graph: CompiledStateGraph,
    histories: list[BaseMessage],
) -> AsyncGenerator[str, Any]:
    try:
        stream_data = graph.astream(
            generate_invoke_payload(payload, histories),
            stream_mode="messages",
        )
        async for message, metadata in stream_data:
            node_name = metadata.get("langgraph_node") if metadata else None
            chunk = getattr(message, "content", "").strip()
            if chunk and node_name in [WorkFlow.GENERATE, WorkFlow.AGENT]:
                log.info(f"Streaming chunk from {node_name}: {chunk}")
                yield f"data: {json.dumps({**SYSTEM_SUCCESS_CONTENT, 'data': {'content': chunk, 'finish': False}})}\n\n"
        yield f"data: {json.dumps({**SYSTEM_SUCCESS_CONTENT, 'data': {'content': '', 'finish': True}})}\n\n"

    except Exception as e:
        raise e


@app.post("/chat")
async def create_chat(
    _: Request,
    body: CreateChatRequest,
    graph=Depends(get_graph),
    db_pool=Depends(get_db_pool),
):
    content = body.content
    session_id = body.session_id
    try:
        if not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty",
            )
        log.info(f"The user's user_input is: {content}")
        histories = await get_histories(db_pool, session_id)
        await db_pool.save_chat(
            session_id=session_id,
            role=AIMessageRole.USER,
            content=content.strip(),
        )
        return (
            StreamingResponse(
                stream_response(body, graph, histories),
                media_type="text/event-stream",
            )
            if body.stream
            else await non_stream_response(body, graph, db_pool, histories)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise e


@app.get("/chat")
async def fetch_chat(
    _: Request,
    # id: str,
    # db_pool=Depends(get_db_pool),
):
    pass


if __name__ == "__main__":
    is_debug = False if os.getenv("DEBUG") == "False" else True
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        # reload=is_debug,
        # workers=4 if not is_debug else None,
    )
