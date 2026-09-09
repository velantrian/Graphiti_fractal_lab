import asyncio
from collections import defaultdict

from core import get_graphiti_client


async def check_graph_quality(return_data: bool = False):
    graphiti_client = get_graphiti_client()
    graphiti = await graphiti_client.ensure_ready()

    # Получаем статистику по типам узлов
    res_nodes = await graphiti.driver.execute_query(
        "MATCH (n) RETURN labels(n) AS labels, count(n) AS cnt"
    )
    node_types = defaultdict(int)
    total_nodes = 0
    for record in res_nodes.records:
        labels = record["labels"] or []
        cnt = record["cnt"] or 0
        key = labels[0] if labels else "Unknown"
        node_types[key] += cnt
        total_nodes += cnt

    # Подсчитываем рёбра
    res_edges = await graphiti.driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS cnt")
    total_edges = res_edges.records[0]["cnt"] if res_edges.records else 0

    summary = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "node_breakdown": dict(sorted(node_types.items())),
    }

    if return_data:
        return summary

    print(
        "\n📊 GRAPH QUALITY REPORT\n"
        "═════════════════════════════════════\n"
        f"Total Nodes: {summary['total_nodes']}\n"
        f"Total Edges: {summary['total_edges']}\n\n"
        "Breakdown by Type:\n"
    )
    for node_type, count in summary["node_breakdown"].items():
        print(f"  - {node_type}: {count}")

    print("\nNext: search-demo / l1 / l2 / l3\n")


if __name__ == "__main__":
    asyncio.run(check_graph_quality())

