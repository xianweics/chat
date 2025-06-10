import os
import re
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape
from typing import Annotated, TypedDict, Sequence, Optional

from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.constants import START, END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from pydantic import BaseModel

from llm.llm.db import create_db
from llm.llm.model_config import MODEL_CONFIGS, DEFAULT_LLM_TYPE
from llm.llm.prompts.config import (
    PROMPT_TEMPLATE_TXT_REWRITE,
    PROMPT_TEMPLATE_TXT_GRADE,
    PROMPT_TEMPLATE_TXT_AGENT,
    PROMPT_TEMPLATE_TXT_GENERATE,
)


def get_default_llm(llm_type=DEFAULT_LLM_TYPE):
    config = MODEL_CONFIGS.get(llm_type)
    if config is None or not config["enable"]:
        config = MODEL_CONFIGS.get(DEFAULT_LLM_TYPE)
    return config


def get_llm(llm_type=DEFAULT_LLM_TYPE):
    config = get_default_llm(llm_type)
    try:
        llm_chat = ChatOpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
            model=config["chat_model"],
            temperature=os.getenv("DEFAULT_TEMPERATURE"),
        )

        llm_embedding = OpenAIEmbeddings(
            base_url=config["base_url"],
            api_key=config["api_key"],
            model=config["embedding_model"],
            dimensions=os.getenv("DEFAULT_DIMENSIONS"),
        )

        return llm_chat, llm_embedding
    except Exception:
        raise


def extract_pdf_texts(pdf_path):
    texts = ""
    pages = enumerate(extract_pages(pdf_path), start=1)
    for page_num, page_layout in pages:
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    texts += text
    return texts


def text_split_to_chucks(texts):
    # 处理特殊小数点：
    # 14.1
    # 3.3.2
    # U.S.A
    normalized = re.sub(
        r"(?<=\d)\.(?=\d)|(?<=[vV]\d)\.(?=\d)|(?<=\w)\.(?=\w)", "∮∮", texts
    )
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=[r"(?<=[。！？；?!.])"],
        keep_separator=True,
        is_separator_regex=True,
    ).split_text(normalized)
    return [chunk.replace("∮∮", ".") for chunk in chunks if chunk.strip()]


class MessagesState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    relevance_score: Optional[str]
    rewrite_count: Optional[int]


class ParallelToolNode(ToolNode):

    def __init__(self, tool_config, max_workers=5):
        super().__init__(tool_config.get_tools())
        self.tool_config = tool_config
        self.max_workers = max_workers
        breakpoint()

    def _run_single_tool(self, tool_call, tool_map):
        tool_name = tool_call["name"]
        try:
            result = tool_map.get(tool_name).invoke(tool_call["args"])
            return ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
                name=tool_name,
            )
        except Exception as e:
            return ToolMessage(
                content=f"Error: {str(e)}",
                tool_call_id=tool_call["id"],
                name=tool_call.get("name", "unknown"),
            )

    def __call__(self, state):
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        if not tool_calls:
            return {"messages": []}

        tool_map = self.tool_config.tool_names()
        results = []

        with ThreadPoolExecutor(self.max_workers) as executor:
            future_to_tool = {
                executor.submit(self._run_single_tool, tool_call, tool_map): tool_call
                for tool_call in tool_calls
            }
            for future in as_completed(future_to_tool):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    tool_call = future_to_tool[future]
                    results.append(
                        ToolMessage(
                            content=f"Unexpected error: {str(e)}",
                            tool_call_id=tool_call["id"],
                            name=tool_call.get("name", "unknown"),
                        )
                    )

        return {"messages": results}


def route_after_tools(state, tool_config):
    breakpoint()

    try:
        return tool_config.get_tool_route_config().get(
            state["messages"][-1].name, "generate"
        )
    except Exception:
        raise


# todo:
# 1. add user_info
# 2. transfer hardcode to constant
def agent(state, config, llm_chat, tool_config, store):
    breakpoint()
    question = state["messages"][-1]

    try:
        filtered = [
            msg
            for msg in state["messages"]
            if msg.__class__.__name__ in ["AIMessage", "HumanMessage"]
        ]
        messages = filtered[-30:] if len(filtered) > 30 else filtered
        llm_chat_with_tool = llm_chat.bind_tools(tool_config.get_tools())
        print("llm_chat_with_tool")
        user_info = store_memory(question, config, store)
        print(user_info)
        agent_chain = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "human",
                        PromptTemplate.from_file(
                            PROMPT_TEMPLATE_TXT_AGENT,
                            encoding="utf-8",
                        ).template,
                    )
                ]
            )
            | llm_chat_with_tool
        )
        print(question, messages, user_info)
        response = agent_chain.invoke(
            {
                "question": question,
                "messages": messages,
                "user_info": user_info,
            }
        )
        return {"messages": [response]}
    except Exception:
        return {"messages": [{"role": "system", "content": "处理请求时出错"}]}


class DocumentRelevanceScore(BaseModel):
    # 定义binary_score字段，表示相关性评分，取值为"yes"或"no"
    binary_score: str


def grade_documents(state, llm_chat):
    breakpoint()
    if not state.get("messages"):
        return {
            "messages": [{"role": "system", "content": "状态为空，无法评分"}],
            "relevance_score": None,
        }

    try:
        reversed_msg = reversed(state["messages"])
        question = ""
        for message in reversed_msg:
            if message.__class__.__name__ == "HumanMessage" and hasattr(
                message, "content"
            ):
                question = message.content
        context = state["messages"][-1].content

        grade_chain = ChatPromptTemplate.from_messages(
            [
                (
                    "human",
                    PromptTemplate.from_file(
                        PROMPT_TEMPLATE_TXT_GRADE,
                        encoding="utf-8",
                    ).template,
                )
            ]
        ) | llm_chat.with_structured_output(DocumentRelevanceScore)
        scored_result = grade_chain.invoke({"question": question, "context": context})
        return {
            "messages": state["messages"],
            "relevance_score": scored_result.binary_score,
        }
    except Exception:
        return {
            "messages": [{"role": "system", "content": "评分过程中出错"}],
            "relevance_score": None,
        }


def rewrite(state, llm_chat):
    breakpoint()
    try:
        question = ""
        msg = reversed(state["messages"])
        for message in msg:
            if message.__class__.__name__ == "HumanMessage" and hasattr(
                message, "content"
            ):
                question = message.content
        rewrite_chain = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "human",
                        PromptTemplate.from_file(
                            PROMPT_TEMPLATE_TXT_REWRITE,
                            encoding="utf-8",
                        ).template,
                    )
                ]
            )
            | llm_chat
        )
        response = rewrite_chain.invoke({"question": question})
        rewrite_count = state.get("rewrite_count", 0) + 1
        return {"messages": [response], "rewrite_count": rewrite_count}
    except Exception:
        return {"messages": [{"role": "system", "content": "无法重写查询"}]}


def generate(state, llm_chat):
    breakpoint()
    try:
        question = ""
        for message in reversed(state["messages"]):
            if message.__class__.__name__ == "HumanMessage" and hasattr(
                message, "content"
            ):
                question = message.content
        context = state["messages"][-1].content
        generate_chain = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "human",
                        PromptTemplate.from_file(
                            PROMPT_TEMPLATE_TXT_GENERATE,
                            encoding="utf-8",
                        ).template,
                    )
                ]
            )
            | llm_chat
        )
        response = generate_chain.invoke({"context": context, "question": question})
        return {"messages": [response]}
    # 捕获索引或键错误
    except Exception:
        return {"messages": [{"role": "system", "content": "无法生成回复"}]}


# 定义响应函数
def graph_response(graph, user_input, config, tool_config):
    breakpoint()
    try:
        # 启动状态图流处理用户输入
        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}], "rewrite_count": 0},
            config,
        )
        # 遍历事件流
        for event in events:
            # 遍历事件中的值
            for value in event.values():
                # 检查是否有有效消息
                if "messages" not in value or not isinstance(value["messages"], list):
                    print("No valid messages in response")
                    continue

                # 获取最后一条消息
                last_message = value["messages"][-1]

                # 检查消息是否包含工具调用
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    # 遍历工具调用
                    for tool_call in last_message.tool_calls:
                        # 检查工具调用是否为字典且包含名称
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            # 记录工具调用日志
                            print(f"Calling tool: {tool_call['name']}")
                    # 跳过本次循环
                    continue

                # 检查消息是否有内容
                if hasattr(last_message, "content"):
                    content = last_message.content

                    # 情况1：工具输出（动态检查工具名称）
                    if (
                        hasattr(last_message, "name")
                        and last_message.name in tool_config.get_tool_names()
                    ):
                        tool_name = last_message.name
                        print(f"Tool Output [{tool_name}]: {content}")
                    # 情况2：大模型输出（非工具消息）
                    else:
                        print(f"Assistant: {content}")
                else:
                    print(value, last_message)
                    print("Assistant: 未获取到相关回复")
    except Exception:
        print("Assistant: 处理响应时发生未知错误")


def route_after_grade(state):
    breakpoint()
    if "messages" not in state or not isinstance(state["messages"], (list, tuple)):
        return "rewrite"
    # 获取状态中的 relevance_score，若不存在则返回 None
    relevance_score = state.get("relevance_score")

    if state.get("rewrite_count", 0) >= 3:
        print("Max rewrite limit reached, proceeding to generate")
        return "generate"

    try:
        if not isinstance(relevance_score, str):
            print(
                f"Invalid relevance_score type: {type(relevance_score)}, defaulting to rewrite"
            )
            return "rewrite"

        # 如果评分结果为 "yes"，表示文档相关，路由到 generate 节点
        if relevance_score.lower() == "yes":
            print("Documents are relevant, proceeding to generate")
            return "generate"

        print("Documents are not relevant or scoring failed, proceeding to rewrite")
        return "rewrite"

    except Exception:
        return "rewrite"


def create_graph(**kwargs):
    llm_embedding = kwargs.get("llm_embedding")
    llm_chat = kwargs.get("llm_chat")
    tool_config = kwargs.get("tool_config")

    checkpointer, store = create_db(llm_embedding)

    workflow = StateGraph(MessagesState)
    workflow.add_node(
        "agent",
        lambda state, config: agent(state, config, llm_chat, tool_config, store),
    )
    workflow.add_node("call_tools", ParallelToolNode(tool_config=tool_config))
    workflow.add_node("rewrite", lambda state: rewrite(state, llm_chat=llm_chat))
    workflow.add_node("generate", lambda state: generate(state, llm_chat=llm_chat))
    workflow.add_node(
        "grade_documents", lambda state: grade_documents(state, llm_chat=llm_chat)
    )

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        source="agent",
        path=tools_condition,
        path_map={"call_tools": "call_tools", END: END},
    )
    workflow.add_conditional_edges(
        source="call_tools",
        path=lambda state: route_after_tools(state, tool_config),
        path_map={
            "tool_multiply": "generate",
            "tool_retrival": "grade_documents",
        },
    )
    workflow.add_conditional_edges(
        source="grade_documents",
        path=route_after_grade,
        path_map={"generate": "generate", "rewrite": "rewrite"},
    )
    workflow.add_edge(start_key="generate", end_key=END)
    workflow.add_edge(start_key="rewrite", end_key="agent")
    graph = workflow.compile(checkpointer=checkpointer, store=store)
    save_graph_visualization(graph)

    return graph


def save_graph_visualization(graph, filename="./graph.png"):
    with open(filename, "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())


def store_memory(question, config, store):
    namespace = ("memories", config["configurable"]["user_id"])
    breakpoint()
    try:
        print(namespace, question.content)
        memories = store.search(namespace, query=str(question.content))
        print(memories)
        user_info = "\n".join([d.value["data"] for d in memories])
        print(user_info, question)
        if "记住" in question.content.lower():
            memory = escape(question.content)
            store.put(namespace, str(uuid.uuid4()), {"data": memory})
        return user_info
    except Exception:
        print(traceback.format_exc())
        raise
