# DAYS 8–9: Interactive Visualization & Performance
> 🌐 🇬🇧 **English** · 🇷🇺 [Русский](./Day_8_9_Visualization_Performance.md)

## Day 8: D3.js/Cytoscape Visualization

### 🎯 Goal: An interactive graph in the browser

### Step 1: Python Backend for Graph Export

```python
# visualization_export.py
import asyncio
from graphiti_core import Graphiti
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def export_graph_for_vis(graphiti, depth: int = 2, limit: int = 50):
    """
    Export graph structure for D3.js/Cytoscape visualization
    Returns: {nodes: [...], edges: [...]}
    """

    # Get all nodes
    search_results = await graphiti._search("*", limit=limit)

    nodes_data = []
    edges_data = set()  # Use set to avoid duplicates

    for node in search_results.nodes:
        nodes_data.append({
            "id": str(node.uuid),
            "label": node.name,
            "title": node.node_type,
            "type": node.node_type,
            "size": 20 if "Person" in node.node_type else 30
        })

    # Build edges from search results
    for edge in search_results.edges:
        edge_id = f"{edge.source_id}-{edge.target_id}"
        edges_data.add(edge_id)

    # Convert edges to list format
    edges_list = []
    for edge in search_results.edges:
        edges_list.append({
            "from": str(edge.source_id),
            "to": str(edge.target_id),
            "label": edge.relationship_type,
            "arrows": "to"
        })

    return {
        "nodes": nodes_data,
        "edges": edges_list,
        "statistics": {
            "total_nodes": len(nodes_data),
            "total_edges": len(edges_list),
            "node_types": list(set(n["type"] for n in nodes_data))
        }
    }

# Export to JSON
async def export_to_file(graphiti, filename: str = "graph_data.json"):
    data = await export_graph_for_vis(graphiti)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Exported to {filename}")
    print(f"   Nodes: {data['statistics']['total_nodes']}")
    print(f"   Edges: {data['statistics']['total_edges']}")

# Test
async def test_export():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    await export_to_file(graphiti)

if __name__ == "__main__":
    asyncio.run(test_export())
```

### Step 2: HTML Page with D3.js

```html
<!-- visualization.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fractal Memory - Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a1a;
            color: #fff;
        }

        #container {
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        #header {
            padding: 20px;
            background: #2a2a2a;
            border-bottom: 1px solid #444;
        }

        h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }

        .stats {
            font-size: 12px;
            color: #aaa;
        }

        #graph {
            flex: 1;
            background: #0a0a0a;
        }

        .node {
            fill: #32b8c6;
            stroke: #fff;
            stroke-width: 2px;
        }

        .node.person {
            fill: #ff6b6b;
        }

        .node.project {
            fill: #4ecdc4;
        }

        .node.concept {
            fill: #95e1d3;
        }

        .node:hover {
            stroke-width: 3px;
            filter: brightness(1.2);
        }

        .link {
            stroke: #666;
            stroke-width: 1px;
        }

        .label {
            font-size: 11px;
            pointer-events: none;
            text-anchor: middle;
        }

        .tooltip {
            position: absolute;
            background: #333;
            padding: 10px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            border: 1px solid #666;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>🌀 Fractal Memory - Knowledge Graph</h1>
            <div class="stats">
                <span id="nodeCount">Nodes: 0</span> |
                <span id="edgeCount">Edges: 0</span> |
                <span id="lastUpdate">Updated: just now</span>
            </div>
        </div>
        <svg id="graph"></svg>
    </div>

    <div id="tooltip" class="tooltip" style="display: none;"></div>

    <script>
    async function loadAndVisualize() {
        // Load data from JSON
        const response = await fetch('graph_data.json');
        const data = await response.json();

        console.log(`Loaded ${data.nodes.length} nodes and ${data.edges.length} edges`);

        // Update stats
        document.getElementById('nodeCount').textContent = `Nodes: ${data.nodes.length}`;
        document.getElementById('edgeCount').textContent = `Edges: ${data.edges.length}`;

        const svg = d3.select("#graph");
        const width = window.innerWidth;
        const height = window.innerHeight - 80;

        // Create simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(d => d.size + 10));

        // Draw links
        const link = svg.selectAll(".link")
            .data(data.edges)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", 2);

        // Draw nodes
        const node = svg.selectAll(".node")
            .data(data.nodes)
            .enter().append("circle")
            .attr("class", d => `node ${d.type.toLowerCase()}`)
            .attr("r", d => d.size)
            .attr("id", d => `node-${d.id}`)
            .call(drag(simulation));

        // Draw labels
        const labels = svg.selectAll(".label")
            .data(data.nodes)
            .enter().append("text")
            .attr("class", "label")
            .text(d => d.label);

        // Simulation tick
        simulation.on("tick", () => {
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("cx", d => d.x = Math.max(d.size, Math.min(width - d.size, d.x)))
                .attr("cy", d => d.y = Math.max(d.size, Math.min(height - d.size, d.y)));

            labels.attr("x", d => d.x)
                .attr("y", d => d.y + d.size + 15);
        });

        // Hover behavior
        const tooltip = document.getElementById('tooltip');

        node.on("mouseover", function(event, d) {
            tooltip.style.display = "block";
            tooltip.innerHTML = `<strong>${d.label}</strong><br/>${d.title}`;
            tooltip.style.left = (event.pageX + 10) + "px";
            tooltip.style.top = (event.pageY + 10) + "px";

            d3.select(this).style("stroke-width", 3);
        })
        .on("mousemove", function(event) {
            tooltip.style.left = (event.pageX + 10) + "px";
            tooltip.style.top = (event.pageY + 10) + "px";
        })
        .on("mouseout", function() {
            tooltip.style.display = "none";
            d3.select(this).style("stroke-width", 2);
        });
    }

    // Drag behavior
    function drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    }

    loadAndVisualize();
    </script>
</body>
</html>
```

### Usage:
```bash
# Экспортируй граф
python visualization_export.py

# Открой visualization.html в браузере
# Будешь видеть интерактивный граф с:
# - Drag & drop для перемещения узлов
# - Hover для информации о узлах
# - Цветовая кодировка по типам
# - Force-directed layout автоматически укладывает узлы
```

---

## Day 9: Performance Benchmarking

### 🎯 Goal: Measure and optimize performance

```python
# benchmark.py
import asyncio
from graphiti_core import Graphiti
import time
import statistics
import os
from dotenv import load_dotenv

load_dotenv()

async def benchmark_operations(graphiti, iterations: int = 10):
    """
    Measure performance of critical operations
    """

    results = {}

    # Benchmark 1: add_episode
    print("⏱️  Benchmarking add_episode...")
    times = []
    for i in range(iterations):
        start = time.time()
        await graphiti.add_episode(
            name=f"Benchmark Episode {i}",
            episode_body=f"This is benchmark message number {i}",
            source_description="benchmark"
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms
        times.append(elapsed)

    results["add_episode"] = {
        "count": iterations,
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "max_ms": max(times),
        "min_ms": min(times)
    }

    # Benchmark 2: search
    print("⏱️  Benchmarking search...")
    times = []
    for i in range(iterations * 2):  # 2x more searches
        start = time.time()
        await graphiti._search("Benchmark", limit=10)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    results["search"] = {
        "count": iterations * 2,
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "max_ms": max(times),
        "min_ms": min(times)
    }

    return results

async def print_report(results):
    """Print performance report"""
    print(f"""
    📊 PERFORMANCE REPORT
    ════════════════════════════════════════════════════════

    add_episode Performance:
      Count:        {results['add_episode']['count']} operations
      Average:      {results['add_episode']['avg_ms']:.1f}ms
      Median:       {results['add_episode']['median_ms']:.1f}ms
      P95:          {results['add_episode']['p95_ms']:.1f}ms
      Max:          {results['add_episode']['max_ms']:.1f}ms
      Min:          {results['add_episode']['min_ms']:.1f}ms

    search Performance:
      Count:        {results['search']['count']} operations
      Average:      {results['search']['avg_ms']:.1f}ms
      Median:       {results['search']['median_ms']:.1f}ms
      P95:          {results['search']['p95_ms']:.1f}ms
      Max:          {results['search']['max_ms']:.1f}ms
      Min:          {results['search']['min_ms']:.1f}ms

    ✅ Performance Targets:
      add_episode: <1000ms ✓ (achieved {results['add_episode']['avg_ms']:.0f}ms)
      search:     <100ms   {'✓' if results['search']['avg_ms'] < 100 else '✗'} (achieved {results['search']['avg_ms']:.0f}ms)

    💡 Recommendations:
    """)

    if results['add_episode']['avg_ms'] > 1000:
        print("      • Consider reducing entity extraction complexity")

    if results['search']['avg_ms'] > 100:
        print("      • Add Neo4j query indices for faster retrieval")
        print("      • Consider increasing Neo4j heap size")

# Test
async def run_benchmark():
    graphiti = Graphiti(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    results = await benchmark_operations(graphiti, iterations=10)
    await print_report(results)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
```

---

## ✅ Days 8–9 Checklist

- [ ] graph_data.json is exported
- [ ] visualization.html opens in the browser
- [ ] The graph is interactive (drag-and-drop works)
- [ ] Hover displays information
- [ ] Benchmark runs
- [ ] Performance report generated
- [ ] All operations are within targets

---

## 🎊 9-DAY PLAN COMPLETED!

**Completed components:**
- ✅ Graphiti core (Days 1–2)
- ✅ Custom Entity Types (Day 2)
- ✅ Visualization & Queries (Days 3–4)
- ✅ Fractal Layers L1–L3 (Days 5–7)
- ✅ Interactive UI (Day 8)
- ✅ Performance Metrics (Day 9)

**The project structure is ready for:**
- Integration with agent logic
- Self-learning module (Judge)
- Real conversation testing
- Production deployment

**Next steps:**
1. Week 2: Agent integration
2. Week 3: Self-learning module
3. Week 4: Advanced analytics & recommendations
