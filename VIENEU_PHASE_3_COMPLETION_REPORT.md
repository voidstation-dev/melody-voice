# VIENEU PHASE 3 — COMPLETION REPORT

**Phase:** 3 — ProviderRegistry, provider discriminator, DB migration
**Branch:** `feat/vieneu-phase-3-provider-registry`
**Base:** `main` @ `a1fa28717035bbb67b707c1e0a2d03d36db21897` (Phase 2 merge)
**Date:** 2026-08-05

## Scope đã hoàn thành
1. ProviderRegistry (`apps/api/app/providers/registry.py`) — registry descriptors
   cho CapCut + VieNeu (từ vieneu-core), KHÔNG instantiate engine.
2. Provider discriminator — `_build_tts_job`/create fns nhận `provider_id` (default
   capcut); retry copy `provider_id` + new fields → job cũ retry đúng provider.
3. DB migration `a3f1c9d2e7b4` thêm 5 cột: provider_id (NOT NULL DEFAULT 'capcut',
   index), backbone_id, style, voice_profile_id, request_metadata (nullable).
4. TTSJobModel + 5 cột mới.
5. Tests: migration (fresh/legacy-adopt/current-unversioned/rollback/backfill),
   registry, retry-preserve-provider (capcut + vieneu).

## Files changed
- **Modify:** apps/api/app/models/tts_job.py, services/database_migrations.py,
  services/tts_service.py, api/v1/tts_jobs.py, schemas/tts.py, pyproject.toml,
  build.py, tests/test_database_migrations.py, tests/test_endpoints.py.
- **Create:** apps/api/alembic/versions/a3f1c9d2e7b4_add_provider_fields.py,
  apps/api/app/providers/registry.py, apps/api/tests/test_provider_registry.py.

## Decisions
- Nâng apps/api `requires-python` >=3.9 → >=3.10 (vieneu-core cần >=3.10; Phase 0
  đã ghi nhận). Python 3.9 EOL Oct 2025; an toàn.
- provider_id dùng `server_default="capcut"` → existing rows tự nhận capcut qua
  SQLite ALTER TABLE ADD COLUMN constant default (không cần backfill UPDATE).
- POST_BASELINE_COLUMNS mở rộng để schema unversioned mới (create_all với model
  mới) stamp head thay vì adopt-legacy (tránh duplicate column).
- Downgrade dùng batch_alter_table (SQLite cần batch để drop column/index).
- ProviderRegistry hold descriptors, not engines (instantiate ở Phase 4/5).
- providerId trong TTSJobResponse là optional (default None) → additive, client
  cũ không break. CreateTTSJobRequest không đổi (CapCut-only phase này).
- build.py thêm `--hidden-import=vieneu_core` cho PyInstaller.

## Test gates
| Gate | Kết quả |
|---|---|
| API tests | PASS (81/81: 70 cũ + 4 migration + 6 registry + 1 retry vieneu) |
| vieneu-core tests | PASS (12/12, no change) |
| Web typecheck | PASS |
| Web tests | PASS (44/44) |
| uv.lock updated (vieneu-core) | PASS (3 occurrences) |

## Exclusions (out of scope)
- VieNeu engine instantiation / model loading → Phase 4/5.
- VieNeu job-creation endpoint → Phase 5.
- Worker routing by provider_id (VieNeu worker path) → Phase 5.
- Voice cloning fields beyond voice_profile_id → Phase 8.

## Review
Independent review agent launched. Xem VIENEU_PHASE_3_REVIEW.md (sẽ tạo sau review).

## Next action
Review → fix → commit (explicit git add apps/api + docs) → push → PR #10 → CI → merge → Phase 4.