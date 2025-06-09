import os
from langchain_chroma import Chroma
from langchain_core.tools import StructuredTool, create_retriever_tool


def tool_multiply():
    def multiply(a, b):
        return a + b

    return StructuredTool.from_function(
        func=multiply,
        name="tool_multiply",
        description="这是计算两个数的乘积的工具，返回最终的计算结果",
    )


def tool_retriever(llm_embedding):
    vectorstore = Chroma(
        persist_directory=os.getenv("CHROMADB_DIRECTORY"),
        collection_name=os.getenv("CHROMADB_COLLECTION_NAME"),
        embedding_function=llm_embedding,
    )
    return create_retriever_tool(
        retriever=vectorstore.as_retriever(),
        name="tool_retrival",
        description="这是健康档案查询工具，搜索并返回有关用户的健康档案信息。",
    )


def build_route(tools):
    routing_config = {}
    for tool in tools:
        if tool.name == "tool_retrival":
            routing_config[tool.name] = "grade_documents"
        elif tool.name == "tool_multiply":
            routing_config[tool.name] = "generate"
    return routing_config


class ToolConfig:
    def __init__(self, llm_embedding):
        self.tools = (
            tool_retriever(llm_embedding),
            tool_multiply(),
        )
        self.tool_names = {tool.name for tool in self.tools}
        self.tool_routing_config = build_route(self.tools)

    def get_tools(self):
        return self.tools

    def get_tool_names(self):
        return self.tool_names

    def get_tool_route_config(self):
        return self.tool_routing_config
