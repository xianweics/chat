import logging
import os
import sys

from langchain_chroma import Chroma
from langchain_core.tools import create_retriever_tool, StructuredTool

from llm.raw.utils.config import TOOL_NAME_RETRIEVE, TOOL_NAME_MULTIPLY

logger = logging.getLogger(__name__)


def get_tools(llm_embedding):
    try:
        global retriever_tool
        vectorstore = Chroma(
            persist_directory=os.getenv("CHROMADB_DIRECTORY"),
            collection_name=os.getenv("CHROMADB_COLLECTION_NAME"),
            embedding_function=llm_embedding,
        )
        retriever = vectorstore.as_retriever()
        retriever_tool = create_retriever_tool(
            retriever,
            name=TOOL_NAME_RETRIEVE,
            description="这是健康档案查询工具，搜索并返回有关用户的健康档案信息。",
        )

        def multiply(a, b):
            return a * b

        return [
            retriever_tool,
            StructuredTool.from_function(
                func=multiply,
                name=TOOL_NAME_MULTIPLY,
                description="这是计算两个数的乘积的工具，返回最终的计算结果",
            ),
        ]
    except Exception as e:
        logger.error(f"Fail to create tools: {e}")
        sys.exit(1)
