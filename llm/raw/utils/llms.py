import logging
import os
import sys

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

log = logging.getLogger(__name__)

DEFAULT_LLM_TYPE = os.getenv("DASHSCOPE_MODEL")
MODEL_CONFIGS = {
    "openai": {
        "base_url": "",
        "api_key": "",
        "chat_model": "",
        "embedding_model": "",
        "enable": False,
    },
    DEFAULT_LLM_TYPE: {
        "base_url": os.getenv("DASHSCOPE_BASE_URL"),
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "chat_model": os.getenv("DASHSCOPE_MODEL"),
        "embedding_model": os.getenv("DASHSCOPE_EMBEDDING"),
        "enable": True,
    },
}


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
    except Exception as e:
        log.error(f"load llm fail: {str(e)}")
        sys.exit(1)
