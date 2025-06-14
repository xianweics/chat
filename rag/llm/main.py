from dotenv import load_dotenv

load_dotenv()

import json
from langgraph.graph.state import CompiledStateGraph
import re
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field

from workflow import create_graph
from rag.logger import load_logger

log = load_logger()
from utils.db import run_db
from utils.llms import get_llm
from utils.tools import get_tools
from rag.llm.workflow_config import WorkFlow


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    choices: List[ChatCompletionResponseChoice]
    system_fingerprint: Optional[str] = None


def format_response(response):
    """对输入的文本进行段落分隔、添加适当的换行符，以及在代码块中增加标记，以便生成更具可读性的输出。

    Args:
        response: 输入的文本。

    Returns:
        具有清晰段落分隔的文本。
    """
    # 使用正则表达式 \n{2, }将输入的response按照两个或更多的连续换行符进行分割。这样可以将文本分割成多个段落，每个段落由连续的非空行组成
    paragraphs = re.split(r"\n{2,}", response)
    # 空列表，用于存储格式化后的段落
    formatted_paragraphs = []
    # 遍历每个段落进行处理
    for para in paragraphs:
        # 检查段落中是否包含代码块标记
        if "```" in para:
            # 将段落按照```分割成多个部分，代码块和普通文本交替出现
            parts: list = para.split("```")
            for i, part in enumerate(parts):
                # 检查当前部分的索引是否为奇数，奇数部分代表代码块
                if i % 2 == 1:  # 这是代码块
                    # 将代码块部分用换行符和```包围，并去除多余的空白字符
                    parts[i] = f"\n```\n{part.strip()}\n```\n"
            # 将分割后的部分重新组合成一个字符串
            para = "".join(parts)
        else:
            # 否则，将句子中的句点后面的空格替换为换行符，以便句子之间有明确的分隔
            para = para.replace(". ", ".\n")
        # 将格式化后的段落添加到formatted_paragraphs列表
        # strip()方法用于移除字符串开头和结尾的空白字符（包括空格、制表符 \t、换行符 \n等）
        formatted_paragraphs.append(para.strip())
    # 将所有格式化后的段落用两个换行符连接起来，以形成一个具有清晰段落分隔的文本
    return "\n\n".join(formatted_paragraphs)


graph: CompiledStateGraph


@asynccontextmanager
async def lifespan(app):
    global graph

    llm_chat, llm_embedding = get_llm()
    tools = get_tools(llm_embedding)
    db_connection_pool = run_db()
    graph = create_graph(db_connection_pool, llm_chat, tools)

    yield
    if db_connection_pool and not db_connection_pool.closed:
        db_connection_pool.close()
        print("Database connection pool closed")
    print("The service has been shut down")


app = FastAPI(lifespan=lifespan)


async def handle_non_stream_response(user_input, config):
    content = None
    try:
        # 启动 graph.stream 处理用户输入，生成事件流
        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}], "rewrite_count": 0},
            config,
        )
        # 遍历事件流中的每个事件
        for event in events:
            # 遍历事件中的所有值
            for value in event.values():
                # 检查事件值是否包含有效消息列表
                if "messages" not in value or not isinstance(value["messages"], list):
                    # 记录警告日志，跳过无效消息
                    log.warning("No valid messages in response")
                    continue

                # 获取消息列表中的最后一条消息
                last_message = value["messages"][-1]

                # 检查消息是否包含工具调用
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    # 遍历所有工具调用
                    for tool_call in last_message.tool_calls:
                        # 验证工具调用是否为字典且包含名称
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            # 记录工具调用日志
                            print(f"Calling tool: {tool_call['name']}")
                    # 跳过本次循环，继续处理下一事件
                    continue

                # 检查消息是否包含内容
                if hasattr(last_message, "content"):
                    content = last_message.content
                else:
                    print("Message has no content, skipping")
    except Exception as e:
        log.error(f"Error processing response: {e}")

    # 格式化响应内容，若无内容则返回默认值
    formatted_response = (
        str(format_response(content)) if content else "No response generated"
    )
    # 记录格式化后的响应日志
    print(f"Results for Formatting: {formatted_response}")

    # 构造返回给客户端的响应对象
    try:
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content=formatted_response),
                    finish_reason="stop",
                )
            ]
        )
    except Exception as resp_error:
        # 捕获并记录构造响应对象时的异常
        log.error(f"Error creating response object: {resp_error}")
        # 构造错误响应对象
        response = ChatCompletionResponse(
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(
                        role="assistant", content="Error generating response"
                    ),
                    finish_reason="error",
                )
            ]
        )

    # 记录发送给客户端的响应内容日志
    print(f"Send response content: \n{response}")
    # 返回 JSON 格式的响应对象
    return JSONResponse(content=response.model_dump())


class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = True
    user_id: str
    thread_id: str


def generate_stream(user_input, config):
    chunk_id = str(uuid.uuid4())
    try:
        stream_data = graph.stream(
            {
                "messages": [{"role": "user", "content": user_input}],
                "rewrite_count": 0,
                "node_error": False,
            },
            config,
            stream_mode="messages",
        )
        breakpoint()
        for message, metadata in stream_data:
            node_name = metadata.get("langgraph_node") if metadata else None
            if node_name in [WorkFlow.GENERATE, WorkFlow.AGENT]:
                chunk = getattr(message, "content")
                if message.model_extra.get("workflow_error"):
                    raise
                if chunk:
                    print(f"Streaming chunk from {node_name}: {chunk}")
                    yield f"data: {json.dumps({'id': chunk_id, 'chunk': chunk, 'finish': False, 'error': False})}\n\n"
        yield f"data: {json.dumps({'id': chunk_id, 'chunk': '', 'finish': True, 'error': False})}\n\n"
    except Exception as stream_error:
        log.error(f"Stream generation error: {stream_error}")
        yield f"data: {json.dumps({'id': chunk_id, 'chunk': '', 'finish': True, 'error': True})}\n\n"


@app.post("/chat")
async def chat_completions(request: Request, body: ChatCompletionRequest):
    messages = body.messages
    user_id = body.user_id
    try:
        if not messages or not user_id or not messages[-1].content:
            log.error("Invalid request")
            raise HTTPException(status_code=400, detail="Invalid request")
        user_input = messages[-1].content
        print(f"The user's user_input is: {user_input}")

        config = {"configurable": {"thread_id": body.thread_id, "user_id": user_id}}

        return (
            StreamingResponse(
                generate_stream(user_input, config),
                media_type="text/event-stream",
            )
            if body.stream
            else await handle_non_stream_response(user_input, config)
        )

    except Exception as e:
        log.error(f"Error handling chat completion:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8012)
