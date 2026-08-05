# VIENEU DECISION LOG

Nhật ký quyết định kỹ thuật cho quá trình tích hợp VieNeu-TTS vào VoidMelody.
Mỗi quyết định ghi: bối cảnh, lựa chọn, lý do, thay thế đã xét, hệ quả.

---

## D001 — MASTER_PLAN_FILE_MISSING: Tiếp tục với prompt làm spec nguồn sự thật

**Ngày:** 2026-08-05 (Phase 0)

**Bối cảnh:** Prompt yêu cầu đọc `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md`
như "tài liệu bắt buộc". File này KHÔNG tồn tại trong repo local, KHÔNG có trên
`origin/main` (`git ls-tree -r origin/main` không trả về file nào chứa "vieneu").

**Lựa chọn:** Tiến hành, dùng nội dung prompt (các mục 5–12: kiến trúc, resource
policy, DB compat, phase execution, test gates, security, licensing) làm spec
nguồn sự thật. Trong Phase 0, tạo file master plan (reverse-engineer từ prompt)
như artifact documentation, commit vào branch Phase 0.

**Lý do:**
- Prompt đã nhúng ĐỦ thông tin để định nghĩa toàn bộ 13 phase, kiến trúc, gates,
  security, licensing. Không thiếu quyết định kỹ thuật nào.
- Dừng để xin file master plan sẽ làm gián đoạn autopilot mà không thêm thông tin.
- Tạo file master plan trong repo có giá trị lâu dài (audit trail, handoff).

**Thay thế đã xét:**
- Dừng theo stop condition #5 ("thay đổi core architecture ngoài master plan") —
  BỎ vì plan đã có trong prompt, không có thay đổi nào "ngoài plan".
- Yêu cầu user cung cấp file — BỎ vì prompt đã đủ spec.

**Hệ quả:**
- File `VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md` sẽ được tạo trong Phase 0.
- Nếu user có file gốc khác, có thể override sau — ghi chú rủi ro này trong PR.

---

## D002 — CI strategy: Repo chưa có PR CI workflow

**Ngày:** 2026-08-05 (Phase 0)

**Bối cảnh:** Repo chỉ có `.github/workflows/release.yml` (trigger: tag push /
workflow_dispatch). KHÔNG có workflow chạy lint/typecheck/test trên PR. Do đó
gate "VERIFY CI" trong vòng lặp autopilot không thể đạt qua GitHub Actions.

**Lựa chọn:** Trong Phase 0, thêm `.github/workflows/ci.yml` chạy các gate
(lint/typecheck/test/build cho web + tests cho api) trên `pull_request` và `push`
to main. Điều này thuộc scope Phase 0 ("baseline") vì nó là điều kiện tiên quyết
cho toàn bộ các phase sau để merge PR có CI xanh.

**Lý do:**
- Vòng lặp autopilot yêu cầu "VERIFY CI" trước merge.
- Không có CI → không thể tự tin merge; chạy local không đủ vì không verify
  cross-platform và không để lại audit trail.
- CI workflow là hạ tầng cơ bản, không phải thay đổi kiến trúc ngoài plan.

**Thay thế đã xét:**
- Chỉ chạy gates local, bỏ qua CI — BỎ vì không audit trail, không verify Windows.
- Dừng theo stop condition #2 — chưa tới, vì vấn đề là thiếu workflow chứ không
  phải policy cấm auto-merge.

**Hệ quả:**
- Phase 0 PR sẽ thêm `ci.yml`. Cần đảm bảo nó xanh trên chính Phase 0 PR.
- Repo không có branch protection → merge được bằng `gh pr merge --squash`.

**Update sau review:** CI api job không cài ffmpeg (tests mock subprocess, OK).
Ghi nhận WARNING 1, không block. Có thể thêm ffmpeg sau nếu test thực shells out.

---

## D003 — Working tree có .DS_Store modified: không động đến trong Phase 0

**Ngày:** 2026-08-05 (Phase 0)

**Bối cảnh:** `git status` cho thấy 5 file `.DS_Store` modified. `.gitignore`
đã ignore `.DS_Store` nhưng chúng đã được track từ trước (lỗi hygiene cũ).

**Lựa chọn:** Không stage, không commit, không revert các `.DS_Store` trong
bất kỳ phase VieNeu nào. Mỗi phase branch chỉ chứa phase scope.

**Lý do:** Rule "không unrelated changes" trong branch phase.

**Hệ quả:** Các phase branch sẽ có working tree "dirty" về `.DS_Store` nhưng
commit sẽ không bao gồm chúng (dùng `git add <specific files>`).

---

## D004 — theme-provider.tsx: revert fix không cần thiết (sau review round 1)

**Ngày:** 2026-08-05 (Phase 0, post-review)

**Bối cảnh:** Tôi đã sửa `theme-provider.tsx` (đổi `import { type ThemeProviderProps }`
thành `React.ComponentProps<typeof NextThemesProvider>`) với lý do "fix pre-existing
typecheck error". Independent reviewer (BLOCKER 3) đã test trực tiếp: stash hết
working-tree changes, chạy `tsc --noEmit` trên pristine main → exit 0. Tôi đã xác
minh lại: `git show main:.../theme-provider.tsx > file` rồi `tsc --noEmit` → PASS.
`next-themes` 0.4.6 thực sự export `ThemeProviderProps` (type). Lỗi typecheck tôi
thấy trước đó là transient (index state), không phải lỗi thực.

**Lựa chọn:** Revert `theme-provider.tsx` về version main. KHÔNG sửa file này
trong Phase 0.

**Lý do:**
- Fix không cần thiết (typecheck pass trên main).
- Sửa production component ngoài scope Phase 0 ("baseline").
- Justification trong completion report sai về mặt sự thực → phải sửa report.

**Hệ quả:**
- `theme-provider.tsx` không nằm trong commit Phase 0.
- Completion report phải cập nhật: bỏ claim "fix pre-existing typecheck error".

---

## D005 — Tracked build artifacts (out/, egg-info/): ghi nhận, không fix trong Phase 0

**Ngày:** 2026-08-05 (Phase 0, post-review)

**Bối cảnh:** Reviewer (WARNING 4) chỉ ra `apps/web/out/` (36 files) và
`apps/api/capvoice_api.egg-info/` (5 files) được track trong repo nhưng là build
artifacts. `.gitignore` cover `.next` nhưng KHÔNG cover `out/`, `*.tsbuildinfo`,
`egg-info/`. Điều này làm mọi local build dirty working tree và đe dọa commit
hygiene của mọi phase.

**Lựa chọn:** Phase 0 KHÔNG fix (ngoài scope "baseline, source pinning, license
inventory"). Ghi nhận là B004 trong VIENEU_BLOCKERS.md. Khuyến nghị cleanup PR
riêng (add .gitignore entries + `git rm --cached`) — nên làm trước Phase 1 để
tránh noise, nhưng là PR riêng biệt không bundle vào phase VieNeu.

**Lý do:**
- Rule "không unrelated changes" trong phase branch.
- Cleanup repo hygiene là vấn đề riêng, nên là PR riêng để review focused.

**Hệ quả:**
- Mỗi phase phải `git add` explicit chỉ files scope, tránh build artifacts.
- B004 mở cho đến khi có cleanup PR riêng.
- Nếu cleanup PR không được làm trước Phase 1, Phase 1 commit sẽ cần cẩn thận
  tương tự Phase 0.