import os

from dotenv import load_dotenv

load_dotenv()
from rag.logger import load_logger

log = load_logger()

from langchain_core.messages import HumanMessage
from langgraph.constants import END
import json
from langgraph.graph.state import CompiledStateGraph
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import uvicorn
import uuid
from typing import Optional
from pydantic import BaseModel

from workflow import create_graph
from utils.db import run_db
from utils.llms import get_llm
from utils.tools import get_tools
from rag.workflow_config import WorkFlow


class Message(BaseModel):
    role: str
    content: str


graph: CompiledStateGraph


@asynccontextmanager
async def lifespan(_):
    global graph

    llm_chat, llm_embedding = get_llm()
    tools = get_tools(llm_embedding)
    db_pool = run_db()
    graph = create_graph(db_pool, llm_chat, tools)

    yield
    if db_pool and not db_pool.closed:
        db_pool.close()
        log.info("Database connection pool closed")
    log.info("The service has been shut down")


app = FastAPI(lifespan=lifespan)


async def non_stream_response(user_input, config):
    try:
        result = graph.invoke(
            {
                "messages": [HumanMessage(user_input)],
                "rewrite_count": 0,
                "error": False,
            },
            config,
        )
        error = result["error"]
        next_nodes = result["next_nodes"][0] if len(result["next_nodes"]) else None
        if error:
            raise
        last_message = result["messages"][-1]
        if next_nodes == END and not last_message.tool_calls:
            return {
                "id": str(uuid.uuid4()),
                "content": last_message.content,
                "finish": True,
                "error": False,
            }
        return {
            "id": str(uuid.uuid4()),
            "content": "No response",
            "finish": True,
            "error": False,
        }
    except Exception as e:
        log.error(f"Non-stream generation error: {e}")
        return {
            "id": str(uuid.uuid4()),
            "content": "System error",
            "finish": True,
            "error": True,
        }


def stream_response(user_input, config):
    chunk_id = str(uuid.uuid4())
    try:
        stream_data = graph.stream(
            {
                "messages": [HumanMessage(user_input)],
                "rewrite_count": 0,
                "error": False,
            },
            config,
            stream_mode="messages",
        )
        for message, metadata in stream_data:
            node_name = metadata.get("langgraph_node") if metadata else None
            chunk = getattr(message, "content", "").strip()
            if chunk and node_name in [WorkFlow.GENERATE, WorkFlow.AGENT]:
                log.info(f"Streaming chunk from {node_name}: {chunk}")
                yield f"data: {json.dumps({'id': chunk_id, 'content': chunk, 'finish': False, 'error': False})}\n\n"
        yield f"data: {json.dumps({'id': chunk_id, 'content': '', 'finish': True, 'error': False})}\n\n"
    except Exception as e:
        log.error(f"Stream generation error: {e}")
        yield f"data: {json.dumps({'id': chunk_id, 'content': 'System error', 'finish': True, 'error': True})}\n\n"


class CreateChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False
    user_id: str
    thread_id: str


class FetchChatRequest(BaseModel):
    user_id: str
    thread_id: str


@app.post("/chat")
async def create_chat(_: Request, body: CreateChatRequest):
    messages = body.messages
    user_id = body.user_id
    try:
        if not messages or not user_id or not messages[-1].content:
            log.error("Invalid request")
            raise HTTPException(status_code=400, detail="Invalid request")
        user_input = messages[-1].content
        log.info(f"The user's user_input is: {user_input}")

        config = {"configurable": {"thread_id": body.thread_id, "user_id": user_id}}

        return (
            StreamingResponse(
                stream_response(user_input, config),
                media_type="text/event-stream",
            )
            if body.stream
            else await non_stream_response(user_input, config)
        )

    except Exception as e:
        log.error(f"Error handling chat completion:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat")
async def fetch_chat(_: Request, body: FetchChatRequest):
    config = {"configurable": {"thread_id": body.thread_id, "user_id": body.user_id}}


if __name__ == "__main__":
    is_debug = False if os.getenv("DEBUG") == "False" else True
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        reload=is_debug,
        # workers=4 if not is_debug else None,
    )
