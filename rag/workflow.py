import asyncio
import logging
import sys
import threading
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import Runnable
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from utils.db import ConnectionPoolManager
from utils.utils import (
    save_graph_visualization,
    filter_messages,
    get_latest_question,
)
from workflow_config import (
    WorkFlow,
    TOOL_TO_NEXT_NODES,
    PROMPT_TEMPLATE_AGENT_PATH,
    PROMPT_TEMPLATE_GRADE_PATH,
    PROMPT_TEMPLATE_REWRITE_PATH,
    PROMPT_TEMPLATE_GENERATE_PATH,
    WorkflowState,
)

log = logging.getLogger(__name__)


class DocumentRelevanceScore(BaseModel):
    is_relevance: bool


async def tool_calls(state: WorkflowState, tools: list[Tool]) -> dict[str, Any]:
    print(f"{WorkFlow.CALL_TOOLS}: start")
    messages = []
    next_steps = []
    for tool_call in state["messages"][-1].tool_calls:
        name = tool_call["name"]
        ts = list(filter(lambda tool: tool.get_name() == name, tools))
        if len(ts) > 0:
            messages.append(
                ToolMessage(
                    str(await ts[0].ainvoke(tool_call["args"])),
                    tool_call_id=tool_call["id"],
                )
            )
            nn = TOOL_TO_NEXT_NODES[name]
            if nn not in next_steps:
                next_steps.append(nn)
    print(f"{WorkFlow.CALL_TOOLS} response: {messages[0]}")
    return {
        "messages": messages,
        "next_steps": next_steps,
    }


def create_chain(
    llm_chat: BaseChatModel, template_file: str, structured_output=None
) -> Runnable:
    if not hasattr(create_chain, "prompt_cache"):
        create_chain.prompt_cache = {}
        create_chain.lock = threading.Lock()

    try:
        prompt_template = None
        if template_file in create_chain.prompt_cache:
            prompt_template = create_chain.prompt_cache[template_file]
            print(f"Using cached prompt template: {template_file}")
        else:
            with create_chain.lock:
                print(f"Loading and caching prompt template: {template_file}")
                prompt_template = create_chain.prompt_cache[template_file] = (
                    PromptTemplate.from_file(template_file, encoding="utf-8")
                )

        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(prompt_template.template)]
        )
        return prompt | (
            llm_chat.with_structured_output(structured_output)
            if structured_output
            else llm_chat
        )
    except Exception:
        log.error(f"Load error: {template_file}")
        raise


async def agent(
    state: WorkflowState, llm_chat: Any, db_pool: ConnectionPoolManager
) -> dict[str, Any]:
    print(f"{WorkFlow.AGENT}: start")
    db_history = await db_pool.get_chats(
        user_id=state.get("user_id"), id=state.get("id"), return_items=("user", "ai")
    )
    if db_history:
        history = []
        for item in db_history:
            history.append(HumanMessage(item["user"])) if item["user"] else None
            history.append(AIMessage(item["ai"])) if item["ai"] else None
    else:
        history = state["messages"]
    try:
        chain = create_chain(
            llm_chat,
            PROMPT_TEMPLATE_AGENT_PATH,
        )

        response = chain.invoke(
            {
                "question": get_latest_question(state),
                "messages": filter_messages(history),
            }
        )
        print(f"{WorkFlow.AGENT} response: {response}")
        return {
            "messages": [response],
            "next_steps": [WorkFlow.CALL_TOOLS if response.tool_calls else END],
        }
    except Exception as e:
        log.error(f"{WorkFlow.AGENT} error: {e}")
        return {"next_steps": [END], "error": True}


async def grade_documents(
    state: WorkflowState, llm_chat: BaseChatModel
) -> dict[str, Any]:
    print(f"{WorkFlow.GRADE_DOCS}: start")
    rewrite_count = state.get("rewrite_count")
    try:
        chain = create_chain(
            llm_chat,
            PROMPT_TEMPLATE_GRADE_PATH,
            DocumentRelevanceScore,
        )
        is_relevance = (
            await chain.ainvoke(
                {
                    "question": get_latest_question(state),
                    "context": state["messages"][-1].content,
                }
            )
        ).is_relevance
        return (
            {
                "next_steps": [WorkFlow.GENERATE],
            }
            if is_relevance or rewrite_count >= 3
            else {
                "next_steps": [WorkFlow.REWRITE],
            }
        )
    except Exception as e:
        log.error(f"{WorkFlow.GRADE_DOCS} error: {e}")
        if rewrite_count >= 3:
            return {"next_steps": [END], "error": True}
        else:
            return {
                "next_steps": [WorkFlow.REWRITE],
            }


async def rewrite(state: WorkflowState, llm_chat: BaseChatModel) -> dict[str, Any]:
    print(f"{WorkFlow.REWRITE}: start")
    try:
        question = get_latest_question(state)
        chain = create_chain(llm_chat, PROMPT_TEMPLATE_REWRITE_PATH)
        response = chain.invoke({"question": question})
        print(f"{WorkFlow.REWRITE} question: {response}")
        rewrite_count = state.get("rewrite_count") + 1
        print(f"{WorkFlow.REWRITE} count: {rewrite_count}")
        return {
            "messages": [response],
            "rewrite_count": rewrite_count,
            "next_steps": [WorkFlow.AGENT],
        }
    except Exception as e:
        log.error(f"{WorkFlow.REWRITE} error: {e}")
        return {"messages": [], "next_steps": [END], "error": True}


async def generate(state: WorkflowState, llm_chat: BaseChatModel) -> dict[str, Any]:
    print(f"{WorkFlow.GENERATE}: start")
    try:
        chain = create_chain(llm_chat, PROMPT_TEMPLATE_GENERATE_PATH)
        response = await chain.ainvoke(
            {
                "context": state["messages"][-1].content,
                "question": get_latest_question(state),
            }
        )
        return {
            "messages": [response],
            "next_steps": [END],
        }
    except Exception as e:
        log.error(f"{WorkFlow.GENERATE} error: {e}")
        return {"messages": [], "next_steps": [END], "error": True}


async def create_graph(
    db_pool: ConnectionPoolManager, llm_chat: BaseChatModel, tools: list[Tool]
) -> CompiledStateGraph:
    try:
        workflow = StateGraph(WorkflowState)
        loop = asyncio.get_event_loop()
        llm_chat.bind_tools(tools)
        workflow.add_node(
            WorkFlow.AGENT,
            lambda state: asyncio.run_coroutine_threadsafe(
                agent(state, llm_chat.bind_tools(tools), db_pool), loop
            ).result(),
        )
        workflow.add_node(
            WorkFlow.CALL_TOOLS,
            lambda state: asyncio.run_coroutine_threadsafe(
                tool_calls(state, tools), loop
            ).result(),
        )
        workflow.add_node(
            WorkFlow.REWRITE,
            lambda state: asyncio.run_coroutine_threadsafe(
                rewrite(state, llm_chat), loop
            ).result(),
        )
        workflow.add_node(
            WorkFlow.GENERATE,
            lambda state: asyncio.run_coroutine_threadsafe(
                generate(state, llm_chat), loop
            ).result(),
        )
        workflow.add_node(
            WorkFlow.GRADE_DOCS,
            lambda state: asyncio.run_coroutine_threadsafe(
                grade_documents(state, llm_chat), loop
            ).result(),
        )
        workflow.add_edge(START, WorkFlow.AGENT)
        workflow.add_conditional_edges(
            WorkFlow.AGENT,
            lambda state: state.get("next_steps"),
            {WorkFlow.CALL_TOOLS: WorkFlow.CALL_TOOLS, END: END},
        )
        workflow.add_conditional_edges(
            WorkFlow.CALL_TOOLS,
            lambda state: state.get("next_steps"),
            {
                WorkFlow.GRADE_DOCS: WorkFlow.GRADE_DOCS,
                WorkFlow.GENERATE: WorkFlow.GENERATE,
            },
        )
        workflow.add_conditional_edges(
            WorkFlow.GRADE_DOCS,
            lambda state: state.get("next_steps"),
            {
                WorkFlow.REWRITE: WorkFlow.REWRITE,
                WorkFlow.GENERATE: WorkFlow.GENERATE,
            },
        )
        workflow.add_conditional_edges(
            WorkFlow.REWRITE,
            lambda state: state.get("next_steps"),
            {
                WorkFlow.AGENT: WorkFlow.AGENT,
                END: END,
            },
        )
        workflow.add_edge(WorkFlow.GENERATE, END)

    except Exception as e:
        log.error(f"Failed to create workflow: {e}")
        sys.exit(-1)

    graph = workflow.compile()
    save_graph_visualization(graph)

    return graph
