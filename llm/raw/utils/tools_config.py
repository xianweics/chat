import logging
import os
import sys

from langchain_chroma import Chroma
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def get_tools(llm_embedding):
    global retriever_tool
    try:
        vectorstore = Chroma(
            persist_directory=os.getenv("CHROMADB_DIRECTORY"),
            collection_name=os.getenv("CHROMADB_COLLECTION_NAME"),
            embedding_function=llm_embedding,
        )
        retriever = vectorstore.as_retriever()
        retriever_tool = create_retriever_tool(
            retriever,
            name="retrieve",
            description="这是健康档案查询工具，搜索并返回有关用户的健康档案信息。",
        )

        @tool
        def multiply(a: float, b: float) -> float:
            """这是计算两个数的乘积的工具，返回最终的计算结果"""
            return a * b

        return [retriever_tool, multiply]
    except Exception as e:
        logger.error(f"Fail to create tools: {e}")
        sys.exit(1)


class ToolConfig:
    def __init__(self, tools):
        self.tools = tools
        self.tool_names = {tool.name for tool in tools}
        self.tool_routing_config = self._build_routing_config()
        logger.info(
            f"Initialized ToolConfig with tools: {self.tool_names}, routing: {self.tool_routing_config}"
        )

    def _build_routing_config(self):
        routing_config = {}
        for tool in self.tools:
            tool_name = tool.name.lower()
            if tool_name == "retrieve":
                routing_config[tool_name] = "grade_documents"
                logger.info(
                    f"Tool '{tool_name}' routed to 'grade_documents' (retrieval tool)"
                )
            else:
                routing_config[tool_name] = "generate"
                logger.info(
                    f"Tool '{tool_name}' routed to 'generate' (non-retrieval tool)"
                )
        if not routing_config:
            logger.warning("No tools provided or routing config is empty")
        return routing_config

    def get_tools(self):
        return self.tools

    def get_tool_names(self):
        return self.tool_names

    def get_tool_routing_config(self):
        return self.tool_routing_config
