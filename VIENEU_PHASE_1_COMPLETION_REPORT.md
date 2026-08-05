# VIENEU PHASE 1 — COMPLETION REPORT

**Phase:** 1 — UI shell (Giọng hiện tại / VieNeu / Giọng nói / Nhân bản giọng)
**Branch:** `feat/vieneu-phase-1-ui-shell`
**Base:** `main` @ `1661276d1e6cdbbc808c18d5b9fb76c0702b67d7` (Phase 0 merge)
**Date:** 2026-08-05

## Scope đã hoàn thành
Thêm UI shell cho VieNeu như một nav item riêng trong sidebar, trỏ đến trang
`/vieneu` mới với 2 section (Giọng nói / Nhân bản giọng) hiển thị placeholder
"chưa khả dụng". KHÔNG có composer, KHÔNG gọi API VieNeu, KHÔNG mock. Workflow
"Giọng hiện tại" (CapCut, `/`) giữ nguyên.

## Decisions (from user)
- Tab placement: **sidebar nav tách biệt** (thêm "VieNeu" vào sidebar → `/vieneu`).
- Functional level: **placeholder only** (shell + unavailable states, no core).

## Files changed
- **Modify:** `apps/web/src/components/app-shell/app-sidebar.tsx` — thêm nav item
  "VieNeu" (icon Sparkles, href `/vieneu`).
- **Create:** `apps/web/src/app/vieneu/page.tsx` — page mỏng render `<VieneuPage />`
  trong `<PageContainer>`.
- **Create:** `apps/web/src/components/vieneu/vieneu-page.tsx` — segmented control
  (Giọng nói / Nhân bản giọng) + placeholder cards, pure presentational, no API.
- **Create:** `apps/web/src/components/vieneu/vieneu-page.test.tsx` — 4 vitest cases.

## Test gates
| Gate | Kết quả |
|---|---|
| Web typecheck | PASS |
| Web lint | PASS (0 errors, 6 warnings — all pre-existing) |
| Web tests | PASS (43/43: 39 cũ + 4 mới) |
| Web build | PASS (7 static pages, `/vieneu` appears) |

## Exclusions (out of scope)
- Không sửa tts-studio, voice-settings-panel, /voices, /, api-client, backend,
  configs, package.json, dependencies, types.
- Không thêm voice list, endpoint, hoặc mock functional.

## Risks / follow-up
- B004 tracked build artifacts — vẫn mở (cleanup PR riêng).
- Voice list / TTS functional → Phase 5.
- Cloning flow → Phase 8.

## Next action
Independent review → fix → commit → push → PR → CI → merge → Phase 2.