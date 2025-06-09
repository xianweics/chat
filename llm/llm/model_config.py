import os

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
