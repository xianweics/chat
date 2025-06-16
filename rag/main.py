import os

from dotenv import load_dotenv

load_dotenv()
from logger import load_logger

log = load_logger()
from langgraph.constants import END
import json
from langgraph.graph.state import CompiledStateGraph
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
import uvicorn
import uuid
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


graph: CompiledStateGraph


@asynccontextmanager
async def lifespan(app):
    global graph

    llm_chat, llm_embedding = get_llm()
    tools = get_tools(llm_embedding)
    db_pool = run_db()
    app.state.db_pool = db_pool
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
        error = result.get("error")
        next_nodes = result.get("next_nodes", [])
        next_nodes = next_nodes[0] if len(next_nodes) else None
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
    content: str
    stream: Optional[bool] = False
    user_id: str
    thread_id: str


class FetchChatRequest(BaseModel):
    user_id: str
    thread_id: str


@app.post("/chat")
async def create_chat(_: Request, body: CreateChatRequest):
    content = body.content
    user_id = body.user_id
    thread_id = body.thread_id
    try:
        if not content or not user_id or not content:
            log.error("Invalid request")
            raise HTTPException(status_code=400, detail="Invalid request")
        log.info(f"The user's user_input is: {content}")

        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

        return (
            StreamingResponse(
                stream_response(content, config),
                media_type="text/event-stream",
            )
            if body.stream
            else await non_stream_response(content, config)
        )

    except Exception as e:
        log.error(f"Error handling chat completion:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_db_pool(request: Request):
    return request.app.state.db_pool


def extract_message_contents(data):
    result = []

    for item in data:
        for _, write_data in item.get("metadata", dict).get("writes", {}).items():
            breakpoint()
            for message in write_data.get("messages", list):
                result.append(
                    {
                        "type": message["kwargs"]["type"],
                        "content": message["kwargs"]["content"],
                    }
                )
    return result


@app.get("/chat")
async def fetch_chat(
    _: Request,
    thread_id: str,
    user_id: str,
    db_pool: any = Depends(get_db_pool),
):
    try:
        with db_pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT thread_id, metadata FROM checkpoints WHERE thread_id = %s",
                    (thread_id,),
                )
                all_data = cur.fetchall()
                if len(all_data) == 0:
                    return []
                columns = [desc[0] for desc in cur.description]
                return extract_message_contents(
                    data
                    for data in [dict(zip(columns, row)) for row in all_data]
                    if data.get("metadata").get("user_id") == user_id
                )
    except Exception as e:
        log.error(f"Error fetching chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    is_debug = False if os.getenv("DEBUG") == "False" else True
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST"),
        port=int(os.getenv("PORT")),
        # reload=is_debug,
        # workers=4 if not is_debug else None,
    )
