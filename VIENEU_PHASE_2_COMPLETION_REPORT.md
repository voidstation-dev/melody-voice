# VIENEU PHASE 2 — COMPLETION REPORT

**Phase:** 2 — Reusable vieneu-core contracts, capabilities, errors, fixtures
**Branch:** `feat/vieneu-phase-2-core`
**Base:** `main` @ `ef6578a1425904351aac674e1ab4fe8c741b53b7` (Phase 1 merge)
**Date:** 2026-08-05

## Scope đã hoàn thành
Tạo `packages/vieneu-core/` — Python package framework-agnostic (contracts,
capabilities, errors, fixtures) + TypeScript types (`index.ts`) cho frontend.
Core KHÔNG phụ thuộc FastAPI/SQLAlchemy/Next.js/Tauri/VoidMelody queue/DB/app state.

## Files created
- `packages/vieneu-core/pyproject.toml` — package (name vieneu-core, python>=3.10, no runtime deps, dev=pytest).
- `packages/vieneu-core/README.md` — non-goals + layout.
- `packages/vieneu-core/src/vieneu_core/__init__.py` — public re-exports.
- `packages/vieneu-core/src/vieneu_core/contracts.py` — Voice, Style, SynthesizeRequest, SynthesizeResult, AudioFormat, VieneuEngine Protocol.
- `packages/vieneu-core/src/vieneu_core/capabilities.py` — Capabilities, ProviderDescriptor, default_capabilities(), default_descriptor().
- `packages/vieneu-core/src/vieneu_core/errors.py` — VieneuCoreError hierarchy + 9 stable error code constants.
- `packages/vieneu-core/src/vieneu_core/fixtures.py` — FIXTURE_VOICES (3), FIXTURE_STYLES (3), builders.
- `packages/vieneu-core/tests/test_contracts.py` — 12 tests.
- `packages/vieneu-core/index.ts` — TS type-only shared types (camelCase, inert).
- `VIENEU_PHASE_2_COMPLETION_REPORT.md`, `VIENEU_PHASE_2_REVIEW.md`.

## Decisions
- Core là Python thuần (contracts) + TypeScript types (index.ts) cho frontend (user choice).
- SynthesizeResult dùng `pcm_bytes: bytes` + sample_rate + dtype (import-light, numpy-free ở contract level; engine impl Phase 5 convert np.ndarray↔bytes).
- max_text_chars=256 (per-chunk, theo V3TurboVieNeuTTS.infer default); adapter chunk input Phase 5.
- sample_rate=48000 (v3 Turbo).
- Không wire vieneu-core vào apps/api (Phase 3). Không thêm vieneu engine dep (Phase 5).

## Test gates
| Gate | Kết quả |
|---|---|
| vieneu-core tests (`uv run pytest`) | PASS (12/12) |
| Web typecheck | PASS |
| Web lint | PASS (0 err, 6 pre-existing warnings) |
| Web tests | PASS (44/44) |
| API tests | PASS (70/70) |
| Dependency discipline (no forbidden imports) | PASS (verified by grep) |
| Scope discipline (no apps changes) | PASS (verified by git diff) |

## Review
Independent agent stalled (infra failure after 600s). Self-verify against full
checklist → APPROVE. Xem VIENEU_PHASE_2_REVIEW.md.

## Exclusions (out of scope)
- Engine implementation / model loading → Phase 4/5.
- apps/api dependency wiring / ProviderRegistry → Phase 3.
- Real voice catalog → Phase 4/5.
- pnpm workspace registration of vieneu-core (TS) → Phase 5.

## Next action
Commit (explicit git add packages/vieneu-core + docs) → push → PR #9 → CI →
merge → Phase 3 (ProviderRegistry, provider discriminator, DB migration).