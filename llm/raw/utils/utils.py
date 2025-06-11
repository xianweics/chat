import logging

logger = logging.getLogger(__name__)


def save_graph_visualization(graph, filename="graph.png") -> None:
    try:
        with open(filename, "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        logger.info(f"Graph visualization saved as {filename}")
    except IOError as e:
        logger.warning(f"Failed to save graph visualization: {e}")
