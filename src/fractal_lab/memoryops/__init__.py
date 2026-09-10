"""Lab-only Fractal MemoryOps prototype over Graphiti + FalkorDBLite.

NOT Canon / Crystal / SVL / Continuum. MEMORY ≠ CANON.
Uses high-level Graphiti.add_episode paths only (no raw EntityEdge.save restore).
"""

from fractal_lab.memoryops.service import LabMemoryOps, MemoryReceipt

__all__ = ["LabMemoryOps", "MemoryReceipt"]
