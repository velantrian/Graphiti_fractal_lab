"""Lab-only Fractal MemoryOps prototype over Graphiti + FalkorDBLite.

NOT Canon / Crystal / SVL / Continuum. MEMORY ≠ CANON.
Uses high-level Graphiti.add_episode paths only (no raw EntityEdge.save restore).

FM-9 temporal classify + FM-10 provenance are lab-layer AFTER Graphiti.search.
"""

from fractal_lab.memoryops.service import LabMemoryOps, MemoryReceipt
from fractal_lab.memoryops.temporal import (
    TEMPORAL_UNKNOWN,
    TEMPORALLY_CURRENT,
    TEMPORALLY_EXPIRED,
    TEMPORALLY_NOT_YET_VALID,
    classify_temporal_status,
)

__all__ = [
    "LabMemoryOps",
    "MemoryReceipt",
    "TEMPORALLY_CURRENT",
    "TEMPORALLY_EXPIRED",
    "TEMPORALLY_NOT_YET_VALID",
    "TEMPORAL_UNKNOWN",
    "classify_temporal_status",
]
