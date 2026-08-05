# VIENEU AUTOPILOT STATE

> Đây là file trạng thái bền vững cho quá trình tích hợp VieNeu-TTS vào VoidMelody.
> Khi session bị gián đoạn, đọc file này và tiếp tục từ "Next Action".

**Last Updated:** 2026-08-05 (Phase 0 — fixing review findings, round 1)

## Current Phase
Phase 0 — Baseline, architecture, source pinning, license inventory

## Current Branch
`feat/vieneu-phase-0-baseline` (chưa commit — đang fix review findings)

## Current Worktree
`/Users/phongvudzz/Desktop/voidmelody` (primary, chưa tạo worktree riêng)

## Main HEAD
`0e21ba3b8d083ba9a73ff76a781721c4ab472332` (v0.2.4 — release: v0.2.4 with portable static ffmpeg)
- origin/main đã đồng bộ (`git fetch origin` thành công, up to date)

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
**REQUEST CHANGES** (round 1). Blockers:
1. Chưa commit — branch không có commit nào.
2. Working tree polluted với build artifacts — cần clean commit boundary.
3. `theme-provider.tsx` fix không cần thiết (typecheck pass trên main) — revert.

Đang fix round 1. Xem VIENEU_PHASE_0_REVIEW.md.

## Commit SHA
— (chưa commit — đang fix review findings)

## PR Number
— (chưa tạo PR)

## CI Status
Repo hiện CHỈ có workflow `release.yml` (tag/dispatch). Phase 0 thêm `ci.yml` (PR/push).
Review chưa verify trên CI vì chưa push.

## Merge SHA
— (chưa merge)

## Open Blockers
- B001 MASTER_PLAN_FILE_MISSING (non-blocking, resolved via D001 — master plan đã tạo)
- B002 CI_NO_PR_WORKFLOW (resolved — ci.yml đã thêm)
- B003 REPO_MERGE_POLICY (resolved — no branch protection, write perm, squash merge OK)
- B004 (new) TRACKED_BUILD_ARTIFACTS — `apps/web/out/` (36 files), `apps/api/capvoice_api.egg-info/` (5 files) tracked trong repo; .gitignore không cover. Pre-existing hygiene. Follow-up cleanup PR nên tách riêng. Phase 0 ghi nhận, không fix (ngoài scope).

## Next Action
1. Khôi phục 7 file bị reviewer stash accident zeroed (ci.yml, eslint.config.mjs, 5 docs) — đang thực hiện.
2. Revert theme-provider.tsx về main version (BLOCKER 3) — DONE (đã verify tsc pass trên main version).
3. Cập nhật completion report + decision log cho review findings.
4. Tạo VIENEU_PHASE_0_REVIEW.md.
5. Stage CHỈ files Phase 0 scope (explicit git add), tránh build artifacts/DS_Store.
6. Re-run tất cả gates.
7. Re-review (round 2) hoặc nếu self-verify OK → commit → push → PR → CI → merge.

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