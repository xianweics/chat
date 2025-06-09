import os
import uuid
from typing import Optional

from dotenv import load_dotenv

from fastapi import FastAPI

from llm.tools import ToolConfig

load_dotenv()

from llm.db import DB
from llm.utils import get_llm, create_graph, save_graph_visualization


def run_llm():
    llm_chat, llm_embedding, oai = get_llm()
    tool_config = ToolConfig(llm_embedding)
    graph = create_graph(
        llm_chat=llm_chat,
        tool_config=tool_config,
    )

    save_graph_visualization(graph)

    # db = DB(oai)
    # db.create_user()
    # id = uuid.uuid4()
    # user_id = "6b8f1bff-cddb-405f-8f5d-c7ab18bef43c"
    # db.save(
    #     id=id,
    #     user_id=user_id,
    #     data="haha",
    # )
    # a = db.get(id=id, user_id=user_id)
    # print(a)


if __name__ == "__main__":
    run_llm()
