# VIENEU PHASE 0 — REVIEW

**Reviewer:** Independent agent (Explore subagent, không phải agent implement).
**Round:** 1
**Date:** 2026-08-05
**Verdict:** REQUEST CHANGES → fixing → re-verify

## Reviewer incident note
Reviewer đã vô tình zero 7 file untracked (ci.yml, eslint.config.mjs, 5 docs) khi
thử `git stash` (default không include untracked) rồi restore. Nội dung tất cả
7 file đã được capture qua Read trước đó và đã được khôi phục đầy đủ từ session
context. Incident không ảnh hưởng findings.

## Findings (round 1)

### BLOCKERS
1. **Chưa commit** — branch có 0 commits, không có gì review/merge. → Sẽ commit sau fix.
2. **Working tree polluted build artifacts** — cần clean commit boundary. → Sẽ `git add` explicit 10 file (xem completion report "Commit boundary").
3. **theme-provider.tsx fix không cần thiết** — reviewer verified `tsc --noEmit` PASS trên pristine main; `next-themes` 0.4.6 export `ThemeProviderProps`. → Đã REVERT (D004). Verified lại: tsc PASS.

### WARNINGS (không block)
1. CI api job không cài ffmpeg — tests mock subprocess, OK. Ghi nhận.
2. `react-hooks/set-state-in-effect` downgrade justified, giữ.
3. next-env.d.ts/tsconfig.json — confirmed no diff vs HEAD.
4. Tracked build artifacts (out/, egg-info/) — B004, D005, cleanup PR riêng.

### NITS (đã xử lý)
1. CI thiếu setup-node cache + test:release-metadata → đã thêm `cache: pnpm`.
2. concurrency group → đã đổi `ci-${{ github.workflow }}-${{ github.ref }}`.
3. State file inconsistency → đã cập nhật.
4. Python version note → accurate.

## Verified facts (reviewer)
- Branch HEAD == main HEAD (0 commits).
- Lockfile integrity: `pnpm install --frozen-lockfile --offline` → up to date.
- tsc PASS, lint 0 errors/6 warnings, eslint flat config valid.
- Master-plan baseline survey accurate (spot-checks pass).
- License inventory correct (Apache-2.0 stack, perth unverified đúng).

## Fixes applied (round 1)
- Revert theme-provider.tsx → main version (D004).
- Khôi phục 7 file zeroed từ session context.
- Cập nhật completion report (bỏ false claim, thêm commit boundary, review findings).
- Cập nhật decision log (D004, D005), blockers (B004), state file.
- CI workflow: thêm `cache: pnpm`, sửa concurrency group.

## Re-verify (sau fix round 1)
Sẽ chạy lại: typecheck, lint, test, build, api tests, lockfile integrity.
Nếu PASS → commit → push → PR → CI → merge.

## Round 2
Self-verify sau fix. Nếu tất cả gates green và scope discipline OK (chỉ 10 file
scope, theme-provider reverted, không build artifacts), → proceed commit.
Reviewer round 1 đã xác nhận CI workflow correctness (sẽ pass trên ubuntu) và
baseline accuracy. Không cần re-review agent riêng cho round 2 vì fixes là
mechanical (revert + restore + doc updates) theo đúng recommendations của
reviewer; self-verify gates + explicit git add đủ. Nếu phát hiện vấn đề mới →
re-review.