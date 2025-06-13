import logging
import os
import sys
import threading
from typing import Literal, Annotated, Sequence

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing_extensions import TypedDict

from utils.utils import (
    save_graph_visualization,
    filter_messages,
    get_latest_question,
)
from workflow_config import WorkFlow, TOOL_TO_NEXT_NODES

logger = logging.getLogger(__name__)


class MessagesState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    relevance_score: str
    rewrite_count: int
    next_nodes: list
    node_error: bool


class DocumentRelevanceScore(BaseModel):
    binary_score: Literal["yes", "no"]


def tool_calls(state, tools):
    tcs = state["messages"][-1].tool_calls
    messages = []
    next_nodes = []
    for tool_call in tcs:
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
            if nn not in next_nodes:
                next_nodes.append(nn)
    print(f"{WorkFlow.CALL_TOOLS} response: {messages[0]}")
    return {
        "messages": messages,
        "node_error": False,
        "next_nodes": next_nodes,
    }


def create_chain(llm_chat, template_file, structured_output=None):
    if not hasattr(create_chain, "prompt_cache"):
        create_chain.prompt_cache = {}
        create_chain.lock = threading.Lock()

    try:
        prompt_template = None
        if template_file in create_chain.prompt_cache:
            prompt_template = create_chain.prompt_cache[template_file]
            print(f"Using cached prompt template for {template_file}")
        else:
            with create_chain.lock:
                print(f"Loading and caching prompt template from {template_file}")
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
        logger.error(f"Fail to load {template_file}")
        raise


def agent(state, llm_chat, tools):
    try:
        llm_chat_with_tool = llm_chat.bind_tools(tools)
        agent_chain = create_chain(
            llm_chat_with_tool,
            os.getenv("PROMPT_TEMPLATE_TXT_AGENT"),
        )
        response = agent_chain.invoke(
            {
                "question": state["messages"][-1],
                "messages": filter_messages(state),
            }
        )
        print(f"{WorkFlow.AGENT} response: {response}")
        return {
            "messages": [response],
            "node_error": False,
            "next_nodes": [WorkFlow.CALL_TOOLS if response.tool_calls else END],
        }
    except Exception as e:
        logger.error(f"Error in agent processing: {e}")
        return {
            "messages": [SystemMessage(f"{WorkFlow.AGENT} error")],
            "node_error": True,
            "next_nodes": [END],
        }


def grade_documents(state, llm_chat):
    print("Grading documents for relevance")
    breakpoint()
    if not state.get("messages"):
        logger.error("Messages state is empty")
        return {
            "messages": [SystemMessage("状态为空，无法评分")],
            "relevance_score": None,
        }

    try:
        question = get_latest_question(state)
        context = state["messages"][-1].content
        print(f"Evaluating relevance - Question: {question}, Context: {context}")

        grade_chain = create_chain(
            llm_chat,
            os.getenv("PROMPT_TEMPLATE_TXT_GRADE"),
            DocumentRelevanceScore,
        )
        score = grade_chain.invoke(
            {"question": question, "context": context}
        ).binary_score
        print(f"Document relevance score: {score}")

        return {
            "messages": state["messages"],
            "relevance_score": score,
        }
    except Exception as e:
        logger.error(f"Unexpected error in grading: {e}")
        return {
            "messages": [SystemMessage("评分过程中出错")],
            "relevance_score": None,
        }


def rewrite(state, llm_chat):
    print("Rewriting query")
    breakpoint()
    try:
        question = get_latest_question(state)
        rewrite_chain = create_chain(llm_chat, os.getenv("PROMPT_TEMPLATE_TXT_REWRITE"))
        response = rewrite_chain.invoke({"question": question})
        print(f"rewrite question:{response}")
        rewrite_count = state.get("rewrite_count", 0) + 1
        print(f"Rewrite count: {rewrite_count}")
        return {"messages": [response], "rewrite_count": rewrite_count}
    except Exception as e:
        logger.error(f"Message access error in rewrite: {e}")
        return {"messages": [SystemMessage("无法重写查询")]}


def generate(state, llm_chat):
    breakpoint()
    try:
        response = create_chain(
            llm_chat, os.getenv("PROMPT_TEMPLATE_TXT_GENERATE")
        ).invoke(
            {
                "context": state["messages"][-1].content,
                "question": get_latest_question(state),
            }
        )
        print(f"{WorkFlow.GENERATE} response: {response}")
        return {
            "messages": [response],
            "node_error": False,
            "next_nodes": [END],
        }
    except Exception as e:
        logger.error(f"Message access error in generate: {e}")
        return {
            "messages": [SystemMessage("无法生成回复")],
            "node_error": True,
            "next_nodes": [END],
        }


def grade_documents_condition(state):
    breakpoint()

    if (
        not isinstance(state, dict)
        or "messages" not in state
        or not isinstance(state["messages"], (list, tuple))
        or "relevance_score" not in state
        or not isinstance(state["relevance_score"], str)
    ):
        logger.error("State is not a valid dictionary, defaulting to rewrite")
        return WorkFlow.REWRITE

    relevance_score = state.get("relevance_score")
    rewrite_count = state.get("rewrite_count", 0)
    print(
        f"Routing based on relevance_score: {relevance_score}, rewrite_count: {rewrite_count}"
    )

    if rewrite_count >= 3:
        print("Max rewrite limit reached, proceeding to generate")
        return WorkFlow.GENERATE

    try:
        if relevance_score.lower() == "yes":
            print("Documents are relevant, proceeding to generate")
            return WorkFlow.GENERATE

        print("Documents are not relevant or scoring failed, proceeding to rewrite")
        return WorkFlow.REWRITE
    except Exception as e:
        logger.error(
            f"Unexpected error in grade_documents_condition: {e}, defaulting to rewrite"
        )
        return WorkFlow.REWRITE


def create_graph(connection_pool, llm_chat, tools):
    try:
        checkpointer = PostgresSaver(connection_pool)
        checkpointer.setup()
    except Exception as e:
        logger.error(f"Failed to setup PostgresSaver: {e}")
        sys.exit(-1)
    try:
        workflow = StateGraph(MessagesState)
        workflow.add_node(
            WorkFlow.AGENT,
            lambda state: agent(state, llm_chat, tools),
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
            WorkFlow.GRADE_DOCS, lambda state: grade_documents(state, llm_chat)
        )
        workflow.add_edge(START, WorkFlow.AGENT)
        workflow.add_conditional_edges(
            WorkFlow.AGENT, lambda state: state.get("next_nodes")
        )
        workflow.add_conditional_edges(
            WorkFlow.CALL_TOOLS, lambda state: state.get("next_nodes")
        )
        workflow.add_conditional_edges(WorkFlow.GRADE_DOCS, grade_documents_condition)
        workflow.add_edge(WorkFlow.REWRITE, WorkFlow.AGENT)
        workflow.add_edge(WorkFlow.GENERATE, END)

    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        sys.exit(-1)

    graph = workflow.compile(checkpointer=checkpointer)
    save_graph_visualization(graph)

    return graph
