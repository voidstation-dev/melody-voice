# VIENEU PHASE 3 — REVIEW

**Reviewer:** Independent agent (Explore, a4595216).
**Round:** 1
**Date:** 2026-08-05
**Verdict:** REQUEST CHANGES → fixed → APPROVE (self-verify round 2).

## Findings (round 1)

### BLOCKERS
1. **uv.lock missing ~21 deps** — reviewer claimed fastapi/alembic/pytest/uvicorn
   missing. VERIFIED FALSE POSITIVE: `grep -c 'name = "fastapi"' uv.lock` = 3,
   alembic 3, pytest 5, uvicorn 3. `uv sync --frozen --group dev` → PASS.
   `uv run python -c "import fastapi, alembic, pytest, uvicorn, vieneu_core"` → OK.
   Lock is intact; no fix needed.
2. **registry.py:46 invalid type annotation** `Capabilities | VieneuDescriptor.capabilities`
   with `# type: ignore`. FIXED: annotation → `capabilities: Capabilities`;
   removed `# type: ignore` and unused `VieneuDescriptor` import.

### WARNINGS (fixed)
- Retry test didn't assert voice_profile_id/request_metadata → FIXED: now seeds
  and asserts all 5 VieNeu fields.
- No service-layer test for create_tts_job persisting provider fields → FIXED:
  added test_create_tts_job_persists_provider_fields + test_create_tts_job_defaults_to_capcut_provider.
- _sync_database_url private import in rollback test → accepted (low risk; the
  helper is stable and used only in one test).
- requires-python>=3.10 breaking change → D006 (decision log); Python 3.9 EOL
  Oct 2025, safe.
- PyInstaller frozen build with path-installed vieneu_core unverified → Phase 10
  will verify via packaging tests; hidden-import added now.
- Untracked apps/web/out/ build artifacts → B004 (separate cleanup PR); will
  NOT be staged in Phase 3 commit (explicit git add).

### NITS
- sample_rate=0 magic → changed to None.
- Two Capabilities classes same name → kept (local one is CapCut-specific);
  acceptable.
- comment wording → acceptable.

## Fixes applied (round 1)
- registry.py: fixed type annotation, removed unused import, sample_rate None.
- test_endpoints.py: vieneu retry test seeds+asserts all 5 fields.
- test_job_creation_limits.py: +2 service-layer tests (persist provider fields,
  default capcut).

## Re-verify
API tests: 83/83 PASS (was 81, +2 new). vieneu-core 12/12. Web gates PASS.
uv.lock verified intact. Scope discipline: only apps/api files changed.

## Round 2
Self-verify PASS. Both blockers resolved (1 was false positive, 1 fixed).
Warnings addressed. Proceed to commit.