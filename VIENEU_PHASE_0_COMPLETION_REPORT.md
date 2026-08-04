# VIENEU PHASE 0 — COMPLETION REPORT

**Phase:** 0 — Baseline, architecture, source pinning, license inventory
**Branch:** `feat/vieneu-phase-0-baseline`
**Base:** `main` @ `0e21ba3b8d083ba9a73ff76a781721c4ab472332` (v0.2.4)
**Date:** 2026-08-05

## Scope đã hoàn thành

1. **Repository & working tree verification**
   - Repo: `voidstation-dev/void-melody`, default branch `main`.
   - Working tree: 5 `.DS_Store` modified (pre-existing hygiene, không động — D003).
     Build artifacts (`apps/web/out/`, `apps/api/capvoice_api.egg-info/`) tracked
     pre-existing — ghi nhận B004, không fix trong Phase 0 (D005).
   - `origin/main` fetched và up-to-date.

2. **Baseline pinning**
   - VoidMelody main HEAD: `0e21ba3b8d083ba9a73ff76a781721c4ab472332` (v0.2.4).
   - VieNeu-TTS source SHA: `a8c9fbf99749d5ce45c89111f71558d6ceef3424` (vieneu 3.2.4).
     - Đã clone về `/tmp/VieNeu-TTS` để audit; SHA khớp HEAD repo tại thời điểm pin.
   - HF model repo: `pnnbao-ump/VieNeu-TTS-v3-Turbo` (subfolder `update` / `onnx_int8`).
     - Codec: `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano` (PyTorch) / `...-ONNX` (CPU).
   - **Rủi ro pinning:** VieNeu không pin `revision=` trong `hf_hub_download` (luôn fetch latest `main`). Pin revision ngoài sẽ là task Phase 4 (model manager) — ghi nhận, không block Phase 0.

3. **License inventory**
   | Component | License | Source | Ghi chú |
   |---|---|---|---|
   | VieNeu-TTS (source) | Apache-2.0 | LICENSE file, pyproject classifier | "designed and trained from scratch" bởi tác giả |
   | MOSS-Audio-Tokenizer-Nano | Apache-2.0 | HF model card metadata | codec cho v3 Turbo |
   | MOSS-Audio-Tokenizer-Nano-ONNX | Apache-2.0 (giả định cùng bản gốc) | HF | Cần verify lại Phase 4 |
   | sea-g2p | Apache-2.0 | GitHub repo + PyPI | phonemizer Rust |
   | neucodec | Apache-2.0, commercial OK | HF model card | dùng cho legacy backends, không cho v3 Turbo |
   | perth | CHƯA XÁC MINH (optional) | — | audio watermark, skipped if absent; không block |
   | onnxruntime | MIT | upstream | runtime inference |
   | CapCut (legacy provider) | KHÔNG ĐƯỢC COI license-clear | submodule K07VN/capcut-tts-api | blocker riêng giữ nguyên (xem master plan §9) |

   - **Kết luận licensing:** VieNeu stack cốt lõi (engine + codec + phonemizer) Apache-2.0, commercial-friendly. Cần thêm `THIRD_PARTY_NOTICES` attribution trong Phase 2/12. CapCut legacy giữ blocker riêng.

4. **Architecture baseline (đã khảo sát)**
   - Monorepo pnpm workspace: `apps/web` (Next.js 16 + React 19 + Tauri 2.11), `apps/api` (FastAPI + SQLAlchemy async + Alembic + uv), `vendor/capcut-tts-api` (submodule).
   - API flow: Frontend → local FastAPI (127.0.0.1:8000, X-Melody-Token) → `TTSQueueManager` (concurrency=3, mỗi worker tạo 1 `CapCutProvider`) → `CapCutClient` → download → FFmpeg concat → artifact `.mp3`.
   - DB: SQLite WAL, Alembic baseline `37c7b24d235a`, head `1ccaccfcb3f0`. Custom `database_migrations.py` adopt legacy + backup.
   - Điểm tích hợp Phase 3: `TTSQueueManager.provider_factory` (cần route theo provider); model VieNeu phải singleton + semaphore (concurrency=1), không nhân bản theo worker.

5. **Persistent state files** (tạo)
   - `VIENEU_AUTOPILOT_STATE.md` — trạng thái bền vững.
   - `VIENEU_DECISION_LOG.md` — D001 (master plan), D002 (CI), D003 (.DS_Store), D004 (theme-provider revert), D005 (build artifacts).
   - `VIENEU_BLOCKERS.md` — B001–B004.
   - `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md` — master plan artifact.

6. **CI workflow** (thêm)
   - `.github/workflows/ci.yml` — chạy trên PR/push to main: web (lint, typecheck, test, build) + api (tests). Submodules recursive, pnpm cache.
   - Bổ sung tooling: `eslint` 9, `eslint-config-next` 16, `apps/web/eslint.config.mjs` (flat config).
   - `lint` script đổi từ `next lint` (broken trong Next 16: "Invalid project directory .../lint") sang `eslint .`.

## Test gates đã chạy (local)

| Gate | Kết quả |
|---|---|
| Web typecheck (`tsc --noEmit`) | PASS |
| Web lint (`eslint .`) | PASS (0 errors, 6 warnings) |
| Web unit/component tests (`vitest run`) | PASS (39/39; 1 flaky update-modal test pass ở lần 2) |
| Web production build (`next build`) | PASS (6 static pages) |
| API tests (`pytest`) | PASS (70/70) |
| Lockfile integrity (`pnpm install --frozen-lockfile --offline`) | PASS (verified by reviewer) |
| install integrity | sẽ verify trên CI (ubuntu) |

## Review findings đã xử lý (round 1)

- **BLOCKER 1 (chưa commit):** Sẽ commit sau khi fix xong round 1.
- **BLOCKER 2 (clean commit boundary):** Sẽ `git add` explicit chỉ 8 file Phase 0
  scope (xem "Commit boundary" dưới). KHÔNG stage `out/`, `egg-info/`, `tsbuildinfo`, `.DS_Store`.
- **BLOCKER 3 (theme-provider.tsx):** Đã REVERT về main version. Verified
  `tsc --noEmit` PASS trên main version (`next-themes` 0.4.6 export `ThemeProviderProps`).
  File không còn trong scope commit Phase 0. (D004)
- WARNING 1 (CI api job thiếu ffmpeg): tests mock subprocess, OK. Ghi nhận, không block.
- WARNING 2 (set-state-in-effect downgrade): justified, giữ nguyên.
- WARNING 3 (next-env.d.ts/tsconfig.json): confirmed no diff vs HEAD.
- WARNING 4 (tracked build artifacts): ghi nhận B004, D005. Cleanup PR riêng.
- NIT 1 (setup-node cache, test:release-metadata): đã thêm `cache: pnpm`.
- NIT 2 (concurrency group): đã đổi thành `ci-${{ github.workflow }}-${{ github.ref }}`.
- NIT 3 (state file inconsistency): đã cập nhật state file.
- NIT 4 (Python version note): accurate, no issue.

## Commit boundary (explicit)
Stage CHỈ những file sau:
- `.github/workflows/ci.yml`
- `apps/web/eslint.config.mjs`
- `apps/web/package.json`
- `pnpm-lock.yaml`
- `VIENEU_AUTOPILOT_STATE.md`
- `VIENEU_DECISION_LOG.md`
- `VIENEU_BLOCKERS.md`
- `VIENEU_PHASE_0_COMPLETION_REPORT.md`
- `VIENEU_PHASE_0_REVIEW.md`
- `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md`

KHÔNG stage: `apps/web/out/**`, `apps/api/capvoice_api.egg-info/**`,
`apps/web/tsconfig.tsbuildinfo`, `.DS_Store`, `apps/web/src/components/providers/theme-provider.tsx`,
`apps/web/next-env.d.ts`, `apps/web/tsconfig.json`, submodule `vendor/capcut-tts-api`.

## Exclusions (không thuộc Phase 0)
- Không thay đổi logic CapCut provider, queue, worker, models, schemas.
- Không thêm VieNeu code thực thi (Phase 1+).
- Không fix `.DS_Store` / `out/` / `egg-info/` hygiene (D003, D005, B004).
- Không động CapCut licensing blocker.
- Không sửa `theme-provider.tsx` (D004, revert theo review).

## Risks & follow-up
- **HF revision pinning** (Phase 4): VieNeu fetch latest `main`; cần snapshot/vendor manifest.
- **MOSS-Audio-Tokenizer-Nano-ONNX license** (Phase 4): giả định Apache-2.0 theo bản PyTorch; verify lại.
- **perth license** (Phase 4/12): optional; xác minh hoặc loại dependency.
- **B004 tracked build artifacts**: cleanup PR riêng nên làm trước Phase 1.
- **update-modal.test flakiness**: pre-existing timing; nếu CI fail flaky → retry.

## Next action
Re-run tất cả gates → tạo VIENEU_PHASE_0_REVIEW.md → stage explicit 10 files →
commit → push → PR → verify CI → merge (squash, delete branch) → sync main → Phase 1.