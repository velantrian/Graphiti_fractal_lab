"""Bootstrap Graphiti against an on-disk FalkorDBLite database (lab only).

Does NOT run Fractal Neo4j migrations. Uses deterministic providers only.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from redislite import AsyncFalkorDB

from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.graphiti import Graphiti
from graphiti_core.llm_client.client import LLMClient

from fractal_lab.experiments.deterministic_providers import (
    DeterministicCrossEncoder,
    DeterministicEmbedder,
    DeterministicLLMClient,
)


@dataclass
class LabGraphitiStack:
    """Owned resources for a lab Graphiti+FalkorDBLite session."""

    db_path: Path
    falkor_db: AsyncFalkorDB
    driver: FalkorDriver
    graphiti: Graphiti

    async def aclose(self) -> None:
        """Shut down Graphiti driver bookkeeping, then redislite server with save."""
        driver = self.driver
        # Mirror FalkorDriver.close init-task cancellation without relying solely on aclose
        init_task = getattr(driver, "_init_task", None)
        if init_task is not None:
            if not init_task.done():
                init_task.cancel()
                with suppress(asyncio.CancelledError):
                    await init_task
            elif not init_task.cancelled():
                with suppress(Exception):
                    init_task.exception()

        # Prefer full AsyncFalkorDB.close() so redislite persists + stops cleanly.
        # FalkorDriver.close() only calls aclose() and can leave RuntimeWarnings.
        await self.falkor_db.close()


async def open_lab_graphiti(
    db_path: str | Path,
    *,
    database: str = "default_db",
    build_indices: bool = True,
    llm_client: LLMClient | None = None,
) -> LabGraphitiStack:
    """Open FalkorDBLite at db_path and return Graphiti wired with deterministic stubs.

    Args:
        db_path: On-disk redislite/FalkorDBLite RDB path (created if missing).
        database: Initial Falkor graph name (driver default). Per-group add_episode
            still clones to group_id graphs under Falkor multi-tenant semantics.
        build_indices: When True, await Graphiti.build_indices_and_constraints().
        llm_client: Optional LLM client override (e.g. DeterministicTemporalLLMClient
            for P5). Defaults to DeterministicLLMClient — which must NOT be used for
            P5 temporal contradiction conclusions.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    falkor_db = AsyncFalkorDB(str(path))
    driver = FalkorDriver(falkor_db=falkor_db, database=database)
    graphiti = Graphiti(
        graph_driver=driver,
        llm_client=llm_client if llm_client is not None else DeterministicLLMClient(),
        embedder=DeterministicEmbedder(),
        cross_encoder=DeterministicCrossEncoder(),
    )
    if build_indices:
        await graphiti.build_indices_and_constraints()

    return LabGraphitiStack(
        db_path=path,
        falkor_db=falkor_db,
        driver=driver,
        graphiti=graphiti,
    )
