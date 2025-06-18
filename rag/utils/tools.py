import logging
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, Any

from langchain_chroma import Chroma
from langchain_core.tools import create_retriever_tool, StructuredTool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

from utils.config import (
    TOOL_NAME_MULTIPLY,
    TOOL_NAME_HEALTH,
    TOOL_NAME_DEEPSEEK,
)

logger = logging.getLogger(__name__)

# chromadb
pp = Path(__file__).parent.parent
CHROMADB_PATH = str(Path(f"{pp}/chromaDB"))
CHROMADB_COLLECTION_DEEPSEEK = "deep_seek"
CHROMADB_COLLECTION_HEALTH = "health"

# tool description
TOOL_DESCRIPTION_HEALTH = "这是健康档案查询工具，搜索并返回有关用户的健康档案信息。"
TOOL_DESCRIPTION_DEEPSEEK = "当用户询问关于 Deep-seek 模型的具体信息时，使用此工具搜索并返回相关信息。这个工具可以访问 Deep-seek 的详细文档。"
TOOL_DESCRIPTION_MULTIPLY = "这是计算两个数的乘积的工具，返回最终的计算结果。"

# file path
DEEPSEEK_PATH = str(Path(f"{pp}/docs/deepseek-v3-1-4.pdf"))
HEALTH_PATH = str(Path(f"{pp}/docs/健康档案.pdf"))


def extract_pdf_to_texts(pdf_path):
    texts = ""
    pages = enumerate(extract_pages(pdf_path), start=1)
    for page_num, page_layout in pages:
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    texts += text
    return texts


def text_to_chucks(texts):
    # handle special characters：
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


def generate_retriever_tool(
    llm_embedding, file_path, collection_name, tool_name, tool_description
):
    chunks = text_to_chucks(extract_pdf_to_texts(file_path))
    vectorstore = Chroma(
        persist_directory=CHROMADB_PATH,
        collection_name=collection_name,
        embedding_function=llm_embedding,
    )
    vectorstore.add_texts(
        texts=chunks,
        ids=[str(uuid.uuid4()) for _ in range(len(chunks))],
    )
    return create_retriever_tool(
        retriever=vectorstore.as_retriever(),
        name=tool_name,
        description=tool_description,
    )


def multiply(a: float, b: float) -> Dict[str, Any]:
    """计算两个数的乘积。

    Args:
        a: 第一个数
        b: 第二个数

    Returns:
        包含结果的字典
    """
    return {"result": a * b}


def get_tools(llm_embedding):
    try:
        return [
            generate_retriever_tool(
                llm_embedding,
                file_path=HEALTH_PATH,
                collection_name=CHROMADB_COLLECTION_HEALTH,
                tool_name=TOOL_NAME_HEALTH,
                tool_description=TOOL_DESCRIPTION_HEALTH,
            ),
            generate_retriever_tool(
                llm_embedding,
                file_path=DEEPSEEK_PATH,
                collection_name=CHROMADB_COLLECTION_DEEPSEEK,
                tool_name=TOOL_NAME_DEEPSEEK,
                tool_description=TOOL_DESCRIPTION_DEEPSEEK,
            ),
            StructuredTool.from_function(
                func=multiply,
                name=TOOL_NAME_MULTIPLY,
                description=TOOL_DESCRIPTION_MULTIPLY,
            ),
        ]
    except Exception as e:
        logger.error(f"Fail to create tools: {e}")
        sys.exit(1)
