# 🔐 FM-17-pre External Freeze Anchor (v1.3.1)

**Purpose:** close `FULL_PACKAGE_PLUS_ROOT_REPLACEMENT` without scientific redesign.

## Authority

| Source | Role |
|--------|------|
| `--expected-frozen-root <sha256>` / `expected_frozen_root=` | **Authority** — pre-overlay EXTERNAL commitment |
| `package.frozen_root_commitment.root_sha256` | Audit / consistency only — **not** authority |
| Recomputed actual artifact digests → actual root | Compared to both |

`actual_root == package_local_root == EXTERNAL_EXPECTED_ROOT` required for GO.

If external expected root is absent → **FAIL** / `GO_ALLOWED=false`.  
The validator **never** defaults expected root from the package.

## Two-phase procedure

1. **PHASE 1 — BLIND FREEZE** (before evaluation overlay): finalize blinded structural package → hash artifacts → compute root R0 → record R0 **outside** the package (lab notebook / authorized receipt / future git commit of freeze materials) → **STOP**.
2. **PHASE 2 — EVALUATION**: only then expose evaluation overlay → validate with previously recorded R0 → A0–A3 only if PASS.

## Design choice

**EXTERNAL_ROOT** (mandatory CLI/API argument), not full Git commit retrieval.

Why: closes the Manus bypass with zero new infrastructure; Git commit pin remains a compatible *operational* way to *store* R0, but the validator authority is the externally supplied digest itself. No PKI/blockchain/signing.

## Residual procedural limit

The validator cannot prove when a human first saw the overlay. Temporal blinding remains operational. Machine gate only prevents the package from silently becoming its own root of trust after overlay exposure.
