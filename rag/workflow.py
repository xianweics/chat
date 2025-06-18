import logging
import sys
import threading
import asyncio
from typing import Annotated, Sequence
from uuid import UUID

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing_extensions import TypedDict
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
)

log = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: UUID
    thread_id: UUID
    history_id: UUID
    cur_step: str
    final_answer: str
    next_steps: list
    error: bool
    rewrite_count: int


class DocumentRelevanceScore(BaseModel):
    is_relevance: bool


async def tool_calls(state, tools):
    log.info(f"{WorkFlow.CALL_TOOLS}: start")
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
    log.info(f"{WorkFlow.CALL_TOOLS} response: {messages[0]}")
    return {
        "messages": messages,
        "next_steps": next_steps,
    }


def create_chain(llm_chat, template_file, structured_output=None):
    if not hasattr(create_chain, "prompt_cache"):
        create_chain.prompt_cache = {}
        create_chain.lock = threading.Lock()

    try:
        prompt_template = None
        if template_file in create_chain.prompt_cache:
            prompt_template = create_chain.prompt_cache[template_file]
            log.info(f"Using cached prompt template: {template_file}")
        else:
            with create_chain.lock:
                log.info(f"Loading and caching prompt template: {template_file}")
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


async def agent(state, llm_chat, db_pool):
    log.info(f"{WorkFlow.AGENT}: start")
    history = await db_pool.get_history(state.get("history_id")) or state["messages"]
    try:
        chain = create_chain(
            llm_chat,
            PROMPT_TEMPLATE_AGENT_PATH,
        )

        response = chain.invoke(
            {
                "question": get_latest_question(state).content,
                "messages": [msg.content for msg in filter_messages(history)],
            }
        )
        log.info(f"{WorkFlow.AGENT} response: {response}")
        return {
            "messages": [response],
            "next_steps": [WorkFlow.CALL_TOOLS if response.tool_calls else END],
        }
    except Exception as e:
        log.error(f"{WorkFlow.AGENT} error: {e}")
        return {"next_steps": [END], "error": True}


async def grade_documents(state, llm_chat):
    log.info(f"{WorkFlow.GRADE_DOCS}: start")
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


async def rewrite(state, llm_chat):
    log.info(f"{WorkFlow.REWRITE}: start")
    try:
        question = get_latest_question(state)
        chain = create_chain(llm_chat, PROMPT_TEMPLATE_REWRITE_PATH)
        response = chain.invoke({"question": question})
        log.info(f"{WorkFlow.REWRITE} question: {response}")
        rewrite_count = state.get("rewrite_count") + 1
        log.info(f"{WorkFlow.REWRITE} count: {rewrite_count}")
        return {
            "messages": [response],
            "rewrite_count": rewrite_count,
            "next_steps": [WorkFlow.AGENT],
        }
    except Exception as e:
        log.error(f"{WorkFlow.REWRITE} error: {e}")
        return {"messages": [], "next_steps": [END], "error": True}


async def generate(state, llm_chat):
    log.info(f"{WorkFlow.GENERATE}: start")
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


async def create_graph(db_pool, llm_chat, tools):
    try:
        workflow = StateGraph(WorkflowState)
        loop = asyncio.get_event_loop()
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
