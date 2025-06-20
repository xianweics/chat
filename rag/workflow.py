import logging
import sys
from functools import lru_cache
from typing import Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage
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


class ToolCallsResponse(TypedDict):
    messages: list[ToolMessage]
    next_steps: list[str]


REWRITE_TIMES = 2


def tool_calls(state: WorkflowState, tools: list[Tool]) -> ToolCallsResponse:
    print(f"{WorkFlow.CALL_TOOLS}: start")
    messages = []
    next_steps = []
    for tool_call in state["messages"][-1].tool_calls:
        name = tool_call["name"]
        ts = list(filter(lambda tool: tool.get_name() == name, tools))
        if len(ts) > 0:
            messages.append(
                ToolMessage(
                    str(ts[0].invoke(tool_call["args"])),
                    tool_call_id=tool_call["id"],
                )
            )
            nn = TOOL_TO_NEXT_NODES[name]
            if nn not in next_steps:
                next_steps.append(nn)
    print(f"{WorkFlow.CALL_TOOLS} response: {str(messages[0])}")
    return {
        "messages": messages,
        "next_steps": next_steps,
    }


@lru_cache(maxsize=128)
def load_prompt_template(template_file: str) -> PromptTemplate:
    return PromptTemplate.from_file(template_file, encoding="utf-8")


def create_chain(
    llm_chat: BaseChatModel, template_file: str, structured_output: type | None = None
) -> Runnable:
    try:
        prompt_template = load_prompt_template(template_file)
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate.from_template(prompt_template.template)]
        )
        return prompt | (
            llm_chat.with_structured_output(structured_output)
            if structured_output
            else llm_chat
        )
    except Exception as e:
        raise Exception(f"Load error: {template_file}: {str(e)}")


def agent(
    state: WorkflowState,
    llm_chat: Any,
) -> dict[str, Any]:
    print(f"{WorkFlow.AGENT}: start")
    try:
        chain = create_chain(
            llm_chat,
            PROMPT_TEMPLATE_AGENT_PATH,
        )

        response = chain.invoke(
            {
                "question": get_latest_question(state),
                "messages": filter_messages(state["messages"]),
            }
        )
        print(f"{WorkFlow.AGENT} response: {str(response)}")
        return {
            "messages": [response],
            "next_steps": [WorkFlow.CALL_TOOLS if response.tool_calls else END],
        }
    except Exception as e:
        raise Exception(f"{WorkFlow.AGENT} error: {str(e)}")


def grade_documents(state: WorkflowState, llm_chat: BaseChatModel) -> dict[str, Any]:
    print(f"{WorkFlow.GRADE_DOCS}: start")
    rewrite_count = state.get("rewrite_count")
    try:
        chain = create_chain(
            llm_chat,
            PROMPT_TEMPLATE_GRADE_PATH,
            DocumentRelevanceScore,
        )
        is_relevance = (
            chain.invoke(
                {
                    "question": get_latest_question(state),
                    "context": state["messages"][-1].content,
                }
            )
        ).is_relevance
        print(f"{WorkFlow.GRADE_DOCS} response: {is_relevance}")

        return (
            {
                "next_steps": [WorkFlow.GENERATE],
            }
            if is_relevance or rewrite_count >= REWRITE_TIMES
            else {
                "next_steps": [WorkFlow.REWRITE],
            }
        )
    except Exception as e:
        if rewrite_count >= REWRITE_TIMES:
            raise Exception(f"{WorkFlow.GRADE_DOCS} error: {str(e)}")
        else:
            return {
                "next_steps": [WorkFlow.REWRITE],
            }


def rewrite(state: WorkflowState, llm_chat: BaseChatModel) -> dict[str, Any]:
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
        raise Exception(f"{WorkFlow.REWRITE} error: {str(e)}")


def generate(state: WorkflowState, llm_chat: BaseChatModel) -> dict[str, Any]:
    print(f"{WorkFlow.GENERATE}: start")
    try:
        chain = create_chain(llm_chat, PROMPT_TEMPLATE_GENERATE_PATH)
        response = chain.invoke(
            {
                "context": state["messages"][-1].content,
                "question": get_latest_question(state),
            }
        )
        print(f"{WorkFlow.GENERATE} response: {str(response)}")
        return {
            "messages": [response],
            "next_steps": [END],
        }
    except Exception as e:
        raise Exception(f"{WorkFlow.GENERATE} error: {str(e)}")


def create_graph(llm_chat: BaseChatModel, tools: list[Tool]) -> CompiledStateGraph:
    try:
        workflow = StateGraph(WorkflowState)
        llm_chat.bind_tools(tools)
        workflow.add_node(
            WorkFlow.AGENT,
            lambda state: agent(state, llm_chat.bind_tools(tools)),
        )
        workflow.add_node(
            WorkFlow.CALL_TOOLS,
            lambda state: tool_calls(state, tools),
        )
        workflow.add_node(
            WorkFlow.REWRITE,
            lambda state: rewrite(state, llm_chat),
        )
        workflow.add_node(
            WorkFlow.GENERATE,
            lambda state: generate(state, llm_chat),
        )
        workflow.add_node(
            WorkFlow.GRADE_DOCS,
            lambda state: grade_documents(state, llm_chat),
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
