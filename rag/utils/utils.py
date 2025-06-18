import logging
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph.state import CompiledStateGraph

from rag.workflow_config import WorkflowState

logger = logging.getLogger(__name__)


def save_graph_visualization(graph: CompiledStateGraph) -> None:
    pp = Path(__file__).parent.parent
    with open(Path(f"{pp}/graph.png"), "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())


def filter_messages(
    messages,
    included: tuple[BaseMessage] = (AIMessage, HumanMessage),
) -> list[BaseMessage]:
    filtered = [
        msg
        for msg in messages
        if len(
            list(
                filter(
                    lambda t: isinstance(msg, t),
                    included,
                )
            )
        )
        > 0
        and msg.content.strip()
    ]
    num = 30
    print(filtered)
    return filtered[-num:] if len(filtered) > num else filtered


def get_latest_question(state: WorkflowState, t=HumanMessage) -> BaseMessage | None:
    human_messages = list(
        filter(
            lambda message: isinstance(message, t),
            state["messages"],
        )
    )
    return human_messages[-1] if len(human_messages) > 0 else None
