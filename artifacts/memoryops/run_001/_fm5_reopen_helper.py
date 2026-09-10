import asyncio, json, sys
from fractal_lab.memoryops.service import LabMemoryOps

async def main(db_path: str, group_id: str, query: str) -> int:
    mem = await LabMemoryOps.open(db_path, default_group_id=group_id, build_indices=True)
    try:
        r = await mem.query(query, group_id=group_id, num_results=10)
        print(json.dumps(r.to_dict(), default=str))
        return 0 if r.edges else 2
    finally:
        await mem.aclose()

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3])))
