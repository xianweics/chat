import os

from dotenv import load_dotenv

load_dotenv()
from logger import load_logger

log = load_logger()
from langgraph.constants import END
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
import uvicorn
from typing import Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from workflow import create_graph
from utils.db import run_db
from utils.llms import get_llm
from utils.tools import get_tools
from workflow_config import WorkFlow


class Message(BaseModel):
    role: str
    content: str


@asynccontextmanager
async def lifespan(app):
    llm_chat, llm_embedding = get_llm()
    tools = get_tools(llm_embedding)
    db_pool = await run_db()
    app.state.db_pool = db_pool
    app.state.graph = await create_graph(db_pool, llm_chat, tools)

    yield
    if db_pool:
        await db_pool.close()


app = FastAPI(lifespan=lifespan)


async def get_db_pool(request: Request):
    return request.app.state.db_pool


async def get_graph(request: Request):
    return request.app.state.graph


def generate_configurable(thread_id, user_id):
    return {"configurable": {"thread_id": thread_id, "user_id": user_id}}


def generate_invoke_payload(payload):
    content = payload.content
    user_id = payload.user_id
    thread_id = payload.thread_id
    history_id = payload.history_id
    return (
        {
            "messages": [HumanMessage(content)],
            "rewrite_count": 0,
            "error": False,
            "history_id": history_id,
            "user_id": user_id,
            "thread_id": thread_id,
        },
        generate_configurable(thread_id, user_id),
    )


async def non_stream_response(payload, graph):
    try:
        result = await graph.ainvoke(*generate_invoke_payload(payload))
        next_steps = result.get("next_steps", [])
        next_steps = next_steps[0] if len(next_steps) else None
        if result.get("error"):
            raise HTTPException(status_code=500, detail="System error")
        last_message = result["messages"][-1]
        if next_steps == END and not last_message.tool_calls:
            return {
                "content": last_message.content,
                "finish": True,
                "error": False,
            }
        return {
            "content": "No response",
            "finish": True,
            "error": False,
        }
    except Exception as e:
        log.error(f"Non-stream generation error: {e}")
        return {
            "content": "System error",
            "finish": True,
            "error": True,
        }


async def stream_response(payload, graph):
    try:
        stream_data = await graph.astream(
            *generate_invoke_payload(payload),
            stream_mode="messages",
        )
        for message, metadata in stream_data:
            node_name = metadata.get("langgraph_node") if metadata else None
            chunk = getattr(message, "content", "").strip()
            if chunk and node_name in [WorkFlow.GENERATE, WorkFlow.AGENT]:
                log.info(f"Streaming chunk from {node_name}: {chunk}")
                yield f"data: {json.dumps({'content': chunk, 'finish': False, 'error': False})}\n\n"
        yield f"data: {json.dumps({'content': '', 'finish': True, 'error': False})}\n\n"
    except Exception as e:
        log.error(f"Stream generation error: {e}")
        yield f"data: {json.dumps({ 'content': 'System error', 'finish': True, 'error': True})}\n\n"


class CreateChatRequest(BaseModel):
    content: str
    stream: Optional[bool] = False
    user_id: str
    thread_id: str
    history_id: Optional[str] = None


class FetchChatRequest(BaseModel):
    user_id: str
    thread_id: str


@app.post("/chat")
async def create_chat(_: Request, body: CreateChatRequest, graph=Depends(get_graph)):
    content = body.content
    user_id = body.user_id
    thread_id = body.thread_id
    try:
        if not content or not user_id or not thread_id or not content:
            log.error("Invalid request")
            raise HTTPException(status_code=400, detail="Invalid request")
        log.info(f"The user's user_input is: {content}")

        return (
            StreamingResponse(
                stream_response(body, graph),
                media_type="text/event-stream",
            )
            if body.stream
            else await non_stream_response(body, graph)
        )

    except Exception as e:
        log.error(f"Error handling chat completion:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat")
async def fetch_chat(
    _: Request,
    thread_id: str,
    user_id: str,
    db_pool=Depends(get_db_pool),
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
