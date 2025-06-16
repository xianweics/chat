from pathlib import Path

from rag.utils.config import (
    TOOL_NAME_DEEPSEEK,
    TOOL_NAME_MULTIPLY,
    TOOL_NAME_HEALTH,
)


class WorkFlow:
    AGENT = "$AGENT"
    CALL_TOOLS = "$CALL_TOOLS"
    REWRITE = "$REWRITE"
    GENERATE = "$GENERATE"
    GRADE_DOCS = "$GRADE_DOCS"


TOOL_TO_NEXT_NODES = {
    TOOL_NAME_DEEPSEEK: WorkFlow.GRADE_DOCS,
    TOOL_NAME_MULTIPLY: WorkFlow.GENERATE,
    TOOL_NAME_HEALTH: WorkFlow.GRADE_DOCS,
}


# prompt
pp = Path(__file__).parent

PROMPT_TEMPLATE_AGENT_PATH = str(Path(f"{pp}/prompts/prompt_template_agent.txt"))
PROMPT_TEMPLATE_GRADE_PATH = str(Path(f"{pp}/prompts/prompt_template_grade.txt"))
PROMPT_TEMPLATE_REWRITE_PATH = str(Path(f"{pp}/prompts/prompt_template_rewrite.txt"))
PROMPT_TEMPLATE_GENERATE_PATH = str(Path(f"{pp}/prompts/prompt_template_generate.txt"))
