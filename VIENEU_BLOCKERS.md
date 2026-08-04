# VIENEU BLOCKERS

Theo dõi các blocker đang mở. Mỗi blocker: mô tả, bằng chứng, trạng thái,
hành động tiếp theo. Blocker đã giải quyết được đánh dấu RESOLVED với ngày.

---

## B001 — MASTER_PLAN_FILE_MISSING (RESOLVED 2026-08-05, non-blocking)

**Mô tả:** File `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md` (tài liệu
"bắt buộc" theo prompt) không tồn tại trong repo local lẫn `origin/main`.

**Bằng chứng:**
- `find . -iname "*VIENEU*MASTER*"` → không kết quả.
- `git ls-tree -r origin/main --name-only | grep -i vieneu` → không kết quả.

**Trạng thái:** RESOLVED via D001. Đã tạo master plan file trong Phase 0.

---

## B002 — CI_NO_PR_WORKFLOW (RESOLVED 2026-08-05)

**Mô tả:** Repo không có CI workflow cho pull request.

**Bằng chứng:** `.github/workflows/` chỉ chứa `release.yml` (trigger tag/dispatch).

**Trạng thái:** RESOLVED via D002. Đã thêm `.github/workflows/ci.yml`.

---

## B003 — REPO_MERGE_POLICY (RESOLVED 2026-08-05)

**Mô tả:** Chính sách merge/branch protection của repo.

**Bằng chứng:**
- `gh api .../branches/main/protection` → 404 (KHÔNG có branch protection).
- `gh api .../collaborators/zfengyuu/permission` → role_name=write, push=true,
  maintain=false, admin=false.
- Repo settings: `allow_auto_merge=false`, `squash_merge=true`, `merge_commit=true`,
  `rebase_merge=true`, `delete_branch_on_merge=false`.
- Repo owner: `voidstation-dev` (không phải `zfengyuu`).

**Trạng thái:** RESOLVED. Không có branch protection → không có required reviews
→ có thể merge PR bằng `gh pr merge --squash --delete-branch` với quyền write.
KHÔNG phải stop condition #2.

**Hệ quả / hành động:**
- Chiến lược: tạo branch phase → push → tạo PR → chạy CI → khi CI xanh,
  `gh pr merge --squash --delete-branch`.
- Không có required reviews → plan bắt buộc independent review → vẫn chạy review
  agent trước merge (audit trail, chất lượng).
- Giới hạn: KHÔNG thể enable auto-merge (cần admin). Không ảnh hưởng.
- Nếu sau này owner thêm branch protection với required reviews → stop condition #2.

---

## B004 — TRACKED_BUILD_ARTIFACTS (OPEN, non-blocking, pre-existing)

**Mô tả:** `apps/web/out/` (36 files) và `apps/api/capvoice_api.egg-info/`
(5 files) được track trong repo nhưng là build artifacts. `.gitignore` cover
`.next` nhưng KHÔNG cover `out/`, `*.tsbuildinfo`, `egg-info/`.

**Bằng chứng:**
- `git ls-files apps/web/out/ | wc -l` → 36 files tracked.
- `git check-ignore apps/web/out/index.html` → NOT ignored.
- Mọi local build (`next build`) dirty working tree (`out/` regenerated).

**Trạng thái:** OPEN, non-blocking. Pre-existing repo hygiene, ngoài scope Phase 0.
Ghi nhận via D005.

**Hành động tiếp theo:** Cleanup PR riêng (add `apps/web/out/`, `*.tsbuildinfo`,
`apps/api/capvoice_api.egg-info/` to `.gitignore` + `git rm --cached`). Nên làm
trước Phase 1 để giảm noise, nhưng KHÔNG bundle vào phase VieNeu. Trong khi đó,
mỗi phase commit dùng `git add <explicit files>` để tránh build artifacts.