from enum import Enum

TOOL_NAME_DEEPSEEK = "DEEPSEEK"
TOOL_NAME_HEALTH = "HEALTH"
TOOL_NAME_MULTIPLY = "MULTIPLY"


class AIMessageRole(Enum):
    AI = "ai"
    USER = "user"
