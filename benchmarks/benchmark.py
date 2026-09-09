import asyncio
import statistics
import time

from core import get_graphiti_client


async def benchmark_operations(graphiti, iterations: int = 10):
    """Measure performance of critical operations."""

    results = {}

    print("⏱️  Benchmarking add_episode...")
    times = []
    for i in range(iterations):
        start = time.time()
        await graphiti.add_episode(
            name=f"Benchmark Episode {i}",
            episode_body=f"This is benchmark message number {i}",
            source_description="benchmark",
        )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    results["add_episode"] = {
        "count": iterations,
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "max_ms": max(times),
        "min_ms": min(times),
    }

    print("⏱️  Benchmarking search...")
    times = []
    for i in range(iterations * 2):
        start = time.time()
        await graphiti.search("Benchmark", num_results=10)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)

    results["search"] = {
        "count": iterations * 2,
        "avg_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "max_ms": max(times),
        "min_ms": min(times),
    }

    return results


async def print_report(results):
    """Print performance report."""
    print(
        f"""
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
      add_episode: <1000ms
      search:     <100ms   {'✓' if results['search']['avg_ms'] < 100 else '✗'} (achieved {results['search']['avg_ms']:.0f}ms)
    """
    )

    if results["add_episode"]["avg_ms"] > 1000:
        print("      • Consider reducing entity extraction complexity")

    if results["search"]["avg_ms"] > 100:
        print("      • Add Neo4j query indices for faster retrieval")
        print("      • Consider increasing Neo4j heap size")


async def run_benchmark():
    graphiti_client = get_graphiti_client()
    graphiti = await graphiti_client.ensure_ready()
    results = await benchmark_operations(graphiti, iterations=10)
    await print_report(results)


if __name__ == "__main__":
    asyncio.run(run_benchmark())

