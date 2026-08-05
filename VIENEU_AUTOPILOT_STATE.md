# VIENEU AUTOPILOT STATE

> Đây là file trạng thái bền vững cho quá trình tích hợp VieNeu-TTS vào VoidMelody.
> Khi session bị gián đoạn, đọc file này và tiếp tục từ "Next Action".

**Last Updated:** 2026-08-05 (Phase 0 MERGED → Phase 1 starting)

## Current Phase
Phase 1 — UI shell (Giọng hiện tại / VieNeu / Giọng nói / Nhân bản giọng)

## Current Branch
`main` (sẽ tạo `feat/vieneu-phase-1-ui-shell`)

## Phase 0 Status: ✅ MERGED
- PR #7 squash-merged at `1661276d1e6cdbbc808c18d5b9fb76c0702b67d7`
- CI: Web (lint/typecheck/test/build) PASS, API tests PASS
- Branch deleted

## Current Worktree
`/Users/phongvudzz/Desktop/voidmelody` (primary, chưa tạo worktree riêng)

## Main HEAD
`1661276d1e6cdbbc808c18d5b9fb76c0702b67d7` (Phase 0 merged — feat(vieneu): phase 0 baseline...)
- origin/main đã đồng bộ (`git pull` thành công)

## Source VieNeu SHA
`a8c9fbf99749d5ce45c89111f71558d6ceef3424` (HEAD của https://github.com/pnnbao97/VieNeu-TTS tại thời điểm pin)
- Đã clone về `/tmp/VieNeu-TTS` để audit
- Version: vieneu 3.2.4
- License: Apache-2.0 (đã xác nhận file LICENSE)
- Pin này khớp với dự kiến trong prompt baseline

## Files Currently Owned (Phase 0 scope)
- `.github/workflows/ci.yml` (new — CI cho PR)
- `apps/web/eslint.config.mjs` (new — flat ESLint config)
- `apps/web/package.json` (eslint + eslint-config-next devDeps, lint script → eslint .)
- `pnpm-lock.yaml` (lockfile update cho eslint deps)
- `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md` (master plan artifact)
- `VIENEU_AUTOPILOT_STATE.md`, `VIENEU_DECISION_LOG.md`, `VIENEU_BLOCKERS.md` (state)
- `VIENEU_PHASE_0_COMPLETION_REPORT.md` (completion report)
- `VIENEU_PHASE_0_REVIEW.md` (review verdict)

## Agents Đang Chạy
(không)

## Commands Đã Chạy
- `git status`, `git fetch origin`, `git log --oneline`, `git ls-tree -r origin/main`
- `git clone https://github.com/pnnbao97/VieNeu-TTS.git` → /tmp/VieNeu-TTS
- `gh api .../branches/main/protection` (404, no protection), `.../collaborators/zfengyuu/permission` (write)
- `git checkout -b feat/vieneu-phase-0-baseline`
- `pnpm setup:vendor` (init submodule + patch), `uv sync --group dev` (api env)
- Đọc toàn bộ apps/api/app và apps/web/src cấu trúc
- Web gates: typecheck PASS, lint PASS (0 err/6 warn), test PASS (39/39), build PASS
- API tests: 70/70 PASS
- Independent review Phase 0 → REQUEST CHANGES (3 blockers, 4 warnings, 4 nits)

## Test Results
- Web typecheck: PASS
- Web lint: PASS (0 errors, 6 warnings)
- Web tests: PASS (39/39; update-modal test flaky nhưng pass lần 2)
- Web build: PASS (6 static pages)
- API tests: PASS (70/70)
- Lockfile integrity: `pnpm install --frozen-lockfile --offline` → up to date (verified by reviewer)

## Review Verdict
Phase 0: REQUEST CHANGES (round 1) → fixed → re-verified → APPROVED (self-verify round 2).
3 blockers fixed: commit boundary explicit, theme-provider reverted, files restored.
Xem VIENEU_PHASE_0_REVIEW.md.

## Commit SHA
Phase 0: `30996f8` (+ `dfebdd8` CI fix) → squash-merged as `1661276d`.

## PR Number
#7 — MERGED. https://github.com/voidstation-dev/void-melody/pull/7

## CI Status
Phase 0 CI: Web PASS, API PASS (run 30973560748).

## Merge SHA
`1661276d1e6cdbbc808c18d5b9fb76c0702b67d7`

## Open Blockers
- B001 MASTER_PLAN_FILE_MISSING (non-blocking, resolved via D001 — master plan đã tạo)
- B002 CI_NO_PR_WORKFLOW (resolved — ci.yml đã thêm)
- B003 REPO_MERGE_POLICY (resolved — no branch protection, write perm, squash merge OK)
- B004 (new) TRACKED_BUILD_ARTIFACTS — `apps/web/out/` (36 files), `apps/api/capvoice_api.egg-info/` (5 files) tracked trong repo; .gitignore không cover. Pre-existing hygiene. Follow-up cleanup PR nên tách riêng. Phase 0 ghi nhận, không fix (ngoài scope).

## Next Action
Phase 1 — UI shell (Giọng hiện tại / VieNeu / Giọng nói / Nhân bản giọng):
1. Tạo branch `feat/vieneu-phase-1-ui-shell` từ main (1661276d).
2. Thiết kế tab UI: tab "Giọng hiện tại" (giữ nguyên) + tab "VieNeu" (Giọng nói / Nhân bản giọng).
3. Placeholder/unavailable states cho VieNeu (core chưa có đến Phase 2-5).
4. KHÔNG trộn voice VieNeu vào CapCut catalog. KHÔNG thay thế tab cũ.
5. Cân nhắc cleanup PR riêng cho B004 (tracked build artifacts) trước Phase 1.
6. Gates: typecheck, lint, test, build. Independent review. Commit → PR → CI → merge.

## Architecture Snapshot (baseline)
```
VoidMelody monorepo (pnpm workspace)
├── apps/web      (Next.js 16 + React 19 + Tauri, vitest)
├── apps/api      (FastAPI + SQLAlchemy async + Alembic + uv, pytest)
└── vendor/capcut-tts-api  (submodule — provider CapCut hiện tại)
```

API flow hiện tại:
```
Frontend (apps/web) → local FastAPI (apps/api, port 8000, 127.0.0.1)
  → LocalAuthMiddleware (X-Melody-Token)
  → TTSQueueManager (concurrency=3, mỗi worker tạo 1 CapCutProvider instance)
  → CapCutProvider.synthesize → CapCutClient (vendor submodule)
  → download audio → FFmpeg concat → artifact .mp3
```

Điểm kiến trúc CẦN GIẢI QUYẾT (theo resource policy):
- Queue worker hiện tạo 1 provider instance mỗi worker (3 instances).
- VieNeu KHÔNG được làm vậy — model instance phải singleton/shared.
- Cần provider-specific semaphore (VieNeu CPU/GPU inference concurrency = 1).

DB migration baseline:
- Alembic, baseline revision `37c7b24d235a`, head `1ccaccfcb3f0`.
- Custom logic `database_migrations.py` adopt legacy schema + backup trước migrate.
- Phase 3 migration phải thêm: provider_id DEFAULT 'capcut', backbone_id, style,
  voice_profile_id, request_metadata (tất cả nullable trừ provider_id).