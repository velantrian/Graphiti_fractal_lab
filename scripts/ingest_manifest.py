import asyncio
import logging
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.graphiti_client import get_graphiti_client
from core.memory_ops import MemoryOps
from core.text_utils import split_into_semantic_chunks, fingerprint

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("IngestManifest")

async def check_if_fingerprint_exists(driver, fp: str, group_id: str = "project") -> bool:
    """Checks Neo4j directly if this chunk fingerprint already exists."""
    query = "MATCH (e:Episodic {group_id: $group_id}) WHERE e.fingerprint = $fp RETURN e.uuid LIMIT 1"
    try:
        res = await driver.execute_query(query, fp=fp, group_id=group_id)
        return len(res.records) > 0
    except Exception as e:
        logger.warning(f"Failed to check fingerprint {fp}: {e}")
        return False

async def ingest_manifest_with_robustness():
    """
    Ingests the architecture manifest into Graphiti group 'project'.
    - 20-minute timeout.
    - Pre-ingest fingerprint check (save costs).
    - Progress visualization.
    - Connectivity bridges.
    """
    manifest_path = Path("architecture_manifest.md")
    if not manifest_path.exists():
        logger.error("❌ architecture_manifest.md not found!")
        return

    content = manifest_path.read_text(encoding='utf-8')
    
    # Split into semantic chunks
    # We use a large size to minimize extraction overhead, but keep it manageable
    chunks = split_into_semantic_chunks(content, max_chunk_size=8000, min_chunk_size=1000)
    total_chunks = len(chunks)
    
    logger.info(f"🚀 Starting ingestion: {total_chunks} chunks detected.")
    
    client = get_graphiti_client()
    graphiti = await client.ensure_ready()
    ops = MemoryOps(graphiti, "system")
    driver = graphiti.driver
    
    start_time = datetime.now()
    processed_count = 0
    skipped_count = 0

    try:
        # Python 3.10 compatible timeout (20 minutes)
        async def _run_ingest():
            nonlocal processed_count, skipped_count
            for i, chunk in enumerate(chunks):
                progress = int(((i + 1) / total_chunks) * 100)
                logger.info(f"📊 [Progress: {progress}%] Processing chunk {i+1}/{total_chunks}...")
                
                # 1. Pre-calculate fingerprint
                fp = fingerprint(chunk)
                
                # 2. Check if already exists (Cost saving!)
                if await check_if_fingerprint_exists(driver, fp):
                    logger.info(f"⏭️  Chunk {i+1} already exists (fingerprint match). Skipping API calls.")
                    skipped_count += 1
                    continue
                
                # 3. Add explicit mention of User and System to force connections in Neo4j
                connected_chunk = (
                    f"Это часть архитектурного манифеста системы Марк.\n"
                    f"Разработчик: Сергей. Система: Марк.\n\n"
                    f"{chunk}"
                )
                
                # 4. Actual Ingest (triggers LLM and Embeddings if not skipped)
                result = await ops.ingest_pipeline(
                    connected_chunk,
                    source_description=f"architecture_manifest_part_{i+1}",
                    memory_type="project"
                )
                
                if result.get("status") == "success":
                    logger.info(f"✅ Chunk {i+1} saved successfully.")
                    processed_count += 1
                else:
                    logger.warning(f"⚠️ Chunk {i+1} status: {result.get('status')} - {result.get('reason')}")

            # 5. Link the project memory to Sergey entity to bridge 'personal' and 'project'
            logger.info("🔗 Creating final bridge relationship between 'project' and 'personal'...")
            bridge_query = """
            MATCH (p:Entity {name: 'Сергей'})
            MATCH (m:Entity) WHERE m.name CONTAINS 'Архитектурный Манифест' OR m.name = 'Марк'
            MERGE (p)-[:DEVELOPES]->(m)
            """
            await driver.execute_query(bridge_query)
            logger.info("✅ Bridge relationship established: (Сергей)-[:DEVELOPES]->(Марк/Манифест)")

        # Timeout: 20 minutes (1200 seconds)
        await asyncio.wait_for(_run_ingest(), timeout=2400.0)

    except asyncio.TimeoutError:
        logger.error("❌ TIMEOUT: Ingestion took more than 40 minutes. Stopped to prevent infinite spin.")
        return
    except Exception as e:
        logger.error(f"❌ ERROR during ingestion: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"✨ Manifest ingestion finished in {elapsed:.1f}s. "
        f"Processed: {processed_count}, Skipped: {skipped_count}, Total: {total_chunks}"
    )

if __name__ == "__main__":
    try:
        asyncio.run(ingest_manifest_with_robustness())
    except KeyboardInterrupt:
        logger.info("🛑 Ingestion interrupted by user.")
    except Exception:
        sys.exit(1)
