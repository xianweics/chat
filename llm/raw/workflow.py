import logging
import os
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape
from typing import Literal, Annotated, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.store.postgres import PostgresStore
from langgraph.store.postgres.base import PostgresIndexConfig
from pydantic import BaseModel
from typing_extensions import TypedDict

from utils.tools_config import ToolConfig
from utils.utils import save_graph_visualization

logger = logging.getLogger(__name__)


class MessagesState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    relevance_score: str
    rewrite_count: int


class DocumentRelevanceScore(BaseModel):
    binary_score: Literal["yes", "no"]


class ParallelToolNode(ToolNode):
    def __init__(self, tools, max_workers: int = 5):
        super().__init__(tools)
        self.max_workers = max_workers
        self.tool_map = ToolConfig(tools).get_tool_names()

    def _run_single_tool(self, tool_call):
        tool_name = tool_call["name"]
        tool = self.tool_map.get(tool_name)
        try:
            result = tool.invoke(tool_call["args"])
            return ToolMessage(
                content=str(result), tool_call_id=tool_call["id"], name=tool_name
            )
        except Exception as e:
            logger.error(
                f"Error executing tool {tool_call.get('name', 'unknown')}: {e}"
            )
            return ToolMessage(
                content=f"Error: {str(e)}",
                tool_call_id=tool_call["id"],
                name=tool_call.get("name", "unknown"),
            )

    def __call__(self, state):
        logger.info("ParallelToolNode processing tool calls")
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        if not tool_calls:
            logger.warning("No tool calls found in state")
            return {"messages": []}

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_tool = {
                executor.submit(self._run_single_tool, tool_call): tool_call
                for tool_call in tool_calls
            }
            for future in as_completed(future_to_tool):
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    tool_call = future_to_tool[future]
                    results.append(
                        ToolMessage(
                            content=f"Unexpected error: {str(e)}",
                            tool_call_id=tool_call["id"],
                            name=tool_call.get("name", "unknown"),
                        )
                    )

        logger.info(f"Completed {len(results)} tool calls")
        return {"messages": results}


def get_latest_question(state):
    if (
        not state.get("messages")
        or not isinstance(state["messages"], (list, tuple))
        or len(state["messages"]) == 0
    ):
        logger.warning("No valid messages found in state for getting latest question")
        return None

    for message in reversed(state["messages"]):
        if message.__class__.__name__ == "HumanMessage" and hasattr(message, "content"):
            return message.content

    logger.warning("No HumanMessage found in state")
    return None


def filter_messages(messages):
    filtered = [
        msg
        for msg in messages
        if msg.__class__.__name__ in ["AIMessage", "HumanMessage"]
    ]
    num = 30
    return filtered[-num:] if len(filtered) > num else filtered


def store_memory(question, config, store):
    namespace = ("memories", config["configurable"]["user_id"])
    try:
        memories = store.search(namespace, query=question.content)
        user_info = "\n".join([d.value["data"] for d in memories])

        if "记住" in question.content.lower():
            memory = escape(question.content)
            store.put(namespace, str(uuid.uuid4()), {"data": memory})
            logger.info(f"Stored memory: {memory}")

        return user_info
    except Exception as e:
        logger.error(f"Error in store_memory: {e}")
        return None


def create_chain(llm_chat, template_file, structured_output=None):
    if not hasattr(create_chain, "prompt_cache"):
        create_chain.prompt_cache = {}
        create_chain.lock = threading.Lock()

    try:
        prompt_template = None
        if template_file in create_chain.prompt_cache:
            prompt_template = create_chain.prompt_cache[template_file]
            logger.info(f"Using cached prompt template for {template_file}")
        else:
            with create_chain.lock:
                logger.info(f"Loading and caching prompt template from {template_file}")
                prompt_template = create_chain.prompt_cache[template_file] = (
                    PromptTemplate.from_file(template_file, encoding="utf-8")
                )

        prompt = ChatPromptTemplate.from_messages([("human", prompt_template.template)])
        return prompt | (
            llm_chat.with_structured_output(structured_output)
            if structured_output
            else llm_chat
        )
    except Exception:
        logger.error(f"Fail to load {template_file}")
        raise


def agent(state, config, store, llm_chat, tool_config):
    logger.info("Agent processing user query")
    try:
        question = state["messages"][-1]
        logger.info(f"agent question:{question}")
        llm_chat_with_tool = llm_chat.bind_tools(tool_config.get_tools())

        agent_chain = create_chain(
            llm_chat_with_tool, os.getenv("PROMPT_TEMPLATE_TXT_AGENT")
        )
        response = agent_chain.invoke(
            {
                "question": question,
                "messages": filter_messages(state["messages"]),
                "userInfo": store_memory(question, config, store),
            }
        )
        logger.info(f"Agent response: {response}")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error in agent processing: {e}")
        return {"messages": [{"role": "system", "content": "处理请求时出错"}]}


def grade_documents(state, llm_chat):
    logger.info("Grading documents for relevance")
    if not state.get("messages"):
        logger.error("Messages state is empty")
        return {
            "messages": [{"role": "system", "content": "状态为空，无法评分"}],
            "relevance_score": None,
        }

    try:
        question = get_latest_question(state)
        context = state["messages"][-1].content
        logger.info(f"Evaluating relevance - Question: {question}, Context: {context}")

        grade_chain = create_chain(
            llm_chat,
            os.getenv("PROMPT_TEMPLATE_TXT_GRADE"),
            DocumentRelevanceScore,
        )
        score = grade_chain.invoke(
            {"question": question, "context": context}
        ).binary_score
        logger.info(f"Document relevance score: {score}")

        return {
            "messages": state["messages"],
            "relevance_score": score,
        }
    except Exception as e:
        logger.error(f"Unexpected error in grading: {e}")
        return {
            "messages": [{"role": "system", "content": "评分过程中出错"}],
            "relevance_score": None,
        }


def rewrite(state, llm_chat):
    logger.info("Rewriting query")
    try:
        question = get_latest_question(state)
        rewrite_chain = create_chain(llm_chat, os.getenv("PROMPT_TEMPLATE_TXT_REWRITE"))
        response = rewrite_chain.invoke({"question": question})
        logger.info(f"rewrite question:{response}")
        rewrite_count = state.get("rewrite_count", 0) + 1
        logger.info(f"Rewrite count: {rewrite_count}")
        return {"messages": [response], "rewrite_count": rewrite_count}
    except Exception as e:
        logger.error(f"Message access error in rewrite: {e}")
        return {"messages": [{"role": "system", "content": "无法重写查询"}]}


def generate(state, llm_chat):
    logger.info("Generating final response")
    try:
        question = get_latest_question(state)
        context = state["messages"][-1].content
        logger.info(f"generate - Question: {question}, Context: {context}")
        generate_chain = create_chain(
            llm_chat, os.getenv("PROMPT_TEMPLATE_TXT_GENERATE")
        )
        response = generate_chain.invoke({"context": context, "question": question})
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Message access error in generate: {e}")
        return {"messages": [{"role": "system", "content": "无法生成回复"}]}


def route_after_tools(state, tool_config):
    if not state.get("messages") or not isinstance(state["messages"], list):
        logger.error("Messages state is empty or invalid, defaulting to generate")
        return "generate"

    try:
        last_message = state["messages"][-1]
        if not hasattr(last_message, "name") or last_message.name is None:
            logger.info("Last message has no name attribute, routing to generate")
            return "generate"

        tool_name = last_message.name
        if tool_name not in tool_config.get_tool_names():
            logger.info(f"Unknown tool {tool_name}, routing to generate")
            return "generate"

        target = tool_config.get_tool_routing_config().get(tool_name, "generate")
        logger.info(f"Tool {tool_name} routed to {target} based on config")
        return target

    except Exception as e:
        logger.error(
            f"Unexpected error in route_after_tools: {e}, defaulting to generate"
        )
        return "generate"


def route_after_grade(state):
    if (
        not isinstance(state, dict)
        or "messages" not in state
        or not isinstance(state["messages"], (list, tuple))
        or "relevance_score" not in state
        or not isinstance(state["relevance_score"], str)
    ):
        logger.error("State is not a valid dictionary, defaulting to rewrite")
        return "rewrite"

    relevance_score = state.get("relevance_score")
    rewrite_count = state.get("rewrite_count", 0)
    logger.info(
        f"Routing based on relevance_score: {relevance_score}, rewrite_count: {rewrite_count}"
    )

    if rewrite_count >= 3:
        logger.info("Max rewrite limit reached, proceeding to generate")
        return "generate"

    try:
        if relevance_score.lower() == "yes":
            logger.info("Documents are relevant, proceeding to generate")
            return "generate"

        logger.info(
            "Documents are not relevant or scoring failed, proceeding to rewrite"
        )
        return "rewrite"
    except Exception as e:
        logger.error(
            f"Unexpected error in route_after_grade: {e}, defaulting to rewrite"
        )
        return "rewrite"


def create_graph(connection_pool, llm_chat, llm_embedding, tool_config):
    try:
        checkpointer = PostgresSaver(connection_pool)
        checkpointer.setup()
        logger.info(f"Succeed to setup PostgresSaver")
    except Exception as e:
        logger.error(f"Failed to setup PostgresSaver: {e}")
        sys.exit(-1)
    try:
        index: PostgresIndexConfig = {
            "dims": int(os.getenv("DEFAULT_DIMENSIONS")),
            "embed": llm_embedding,
        }
        store = PostgresStore(
            connection_pool,
            index=index,
        )
        store.setup()
        logger.info(f"Succeed to setup PostgresStore")
    except Exception as e:
        logger.error(f"Failed to setup PostgresStore: {e}")
        sys.exit(-1)
    try:
        workflow = StateGraph(MessagesState)
        workflow.add_node(
            "agent",
            lambda state, config: agent(
                state, config, store=store, llm_chat=llm_chat, tool_config=tool_config
            ),
        )
        workflow.add_node(
            "call_tools", ParallelToolNode(tool_config.get_tools(), max_workers=5)
        )
        workflow.add_node("rewrite", lambda state: rewrite(state, llm_chat=llm_chat))
        workflow.add_node("generate", lambda state: generate(state, llm_chat=llm_chat))
        workflow.add_node(
            "grade_documents", lambda state: grade_documents(state, llm_chat=llm_chat)
        )

        workflow.add_edge(START, end_key="agent")
        workflow.add_conditional_edges(
            source="agent",
            path=tools_condition,
            path_map={"tools": "call_tools", END: END},
        )
        workflow.add_conditional_edges(
            source="call_tools",
            path=lambda state: route_after_tools(state, tool_config),
            path_map={"generate": "generate", "grade_documents": "grade_documents"},
        )
        workflow.add_conditional_edges(
            source="grade_documents",
            path=route_after_grade,
            path_map={"generate": "generate", "rewrite": "rewrite"},
        )
        workflow.add_edge(start_key="generate", end_key=END)
        workflow.add_edge(start_key="rewrite", end_key="agent")
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        sys.exit(-1)

    graph = workflow.compile(checkpointer=checkpointer, store=store)
    save_graph_visualization(graph)

    return graph
