from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from llm.llm.tools import ToolConfig
from llm.llm.utils import get_llm, create_graph, graph_response


def run_llm():
    llm_chat, llm_embedding = get_llm()
    tool_config = ToolConfig(llm_embedding)
    graph = create_graph(
        llm_chat=llm_chat,
        llm_embedding=llm_embedding,
        tool_config=tool_config,
    )
    config = {"configurable": {"thread_id": "1", "user_id": "1"}}
    breakpoint()
    graph_response(graph, "aaa", config, tool_config)


@asynccontextmanager
async def main(app):
    run_llm()
    yield app


if __name__ == "__main__":
    run_llm()
