import logging
import os
import sys

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr

log = logging.getLogger(__name__)


def get_llm():
    try:
        llm_chat = ChatOpenAI(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_API_MODEL"),
            temperature=0.5,
        )

        llm_embedding = OpenAIEmbeddings(
            base_url=os.getenv("EMBEDDING_BASE_URL"),
            api_key=SecretStr(os.getenv("EMBEDDING_API_KEY")),
            model=os.getenv("EMBEDDING"),
            check_embedding_ctx_length=False,
            dimensions=1536,
        )

        return llm_chat, llm_embedding
    except Exception as e:
        log.error(f"load llm fail: {str(e)}")
        sys.exit(-1)
