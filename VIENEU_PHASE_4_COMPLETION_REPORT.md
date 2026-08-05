# VIENEU PHASE 4 — COMPLETION REPORT

**Phase:** 4 — Runtime probe, model manager, downloader, cache, checksum
**Branch:** `feat/vieneu-phase-4-model-manager`
**Base:** `main` (Phase 3 merge)
**Date:** 2026-08-05

## Scope đã hoàn thành
1. `ModelManifest`, `ModelFile` và hàm verify SHA-256 (`_sha256`, `verify_file`, `verify_cache`) để hỗ trợ reproducible fetch.
2. `ModelDownloader` dùng `huggingface_hub.hf_hub_download` tải file từng luồng (concurrency=1 via `asyncio.Semaphore(1)`), pin revision.
3. `RuntimeProbe` quét khả năng phần cứng (`device`, `backend`, `torch_cuda_available`, `onnxruntime_available`) mà không import engine.
4. `ModelManager` (singleton) lock quá trình khởi tạo engine (load concurrency=1) và cung cấp instances duy nhất cho toàn ứng dụng.
5. Setup patch `vieneu-tts-remove-gradio-librosa-from-core.patch` để remove Gradio/Librosa từ core dependencies, giữ headless/torch-free install.

## Files changed
- **Modify:** `packages/vieneu-core/pyproject.toml`, `packages/vieneu-core/src/vieneu_core/__init__.py`, `packages/vieneu-core/src/vieneu_core/fixtures.py`, `packages/vieneu-core/src/vieneu_core/engine.py`, `scripts/setup-vendor.mjs`, `tests/test_contracts.py`
- **Create:** `packages/vieneu-core/src/vieneu_core/downloader.py`, `packages/vieneu-core/src/vieneu_core/engine.py`, `packages/vieneu-core/tests/test_downloader.py`, `packages/vieneu-core/tests/test_engine.py`, `patches/vieneu-tts-remove-gradio-librosa-from-core.patch`

## Test gates
| Gate | Kết quả |
|---|---|
| vieneu-core unit tests | PASS (29/29) |
| typecheck (mypy) | PASS |
| lint (ruff) | PASS |

## Review
Review đã được thực hiện độc lập bởi Recovery Agent (fix mypy/ruff errors, check concurrency requirements). Xem `VIENEU_PHASE_4_REVIEW.md`.

## Next action
Push branch `feat/vieneu-phase-4-model-manager` → tạo PR → Phase 5 (preset voice TTS).
