# VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md

Master plan tích hợp VieNeu-TTS vào VoidMelody.

> **Ghi chú nguồn:** Tài liệu này được chuẩn hóa từ đặc tả autopilot do người điều
> phối cấp (prompt ngày 2026-08-05). Nếu tồn tại file `VOID_MELODY_VIENEU_*` khác
> do người dùng cung cấp, file đó override. Quyết định ghi trong
> `VIENEU_DECISION_LOG.md` (D001).

## 1. Mục tiêu

Tích hợp engine TTS VieNeu-TTS (Vietnamese, on-device, voice cloning) vào
VoidMelody desktop app song song với provider CapCut hiện có, mà không thay thế
hay pha trộn workflow/giọng cũ, có reusable core tách biệt để tái dùng cho
VOID STUDIO sau này.

## 2. Kiến trúc bắt buộc

```
VoidMelody frontend (apps/web)
  → existing authenticated local API (apps/api, 127.0.0.1, X-Melody-Token)
    → thin FastAPI adapter
      → ProviderRegistry
        → reusable vieneu-core (packages/vieneu-core/)
          → local model runtime (VieNeu ONNX/CPU)
            → existing artifact/FFmpeg pipeline
```

Tương lai (VOID STUDIO):
```
plugin handlers → same vieneu-core → TaskScheduler/ArtifactRegistry/ResourceGovernor/ToolRegistry
```

Cấu trúc sản phẩm (UI):
```
VoidMelody
├── Giọng hiện tại   (CapCut — giữ nguyên workflow và voice list hiện có)
└── VieNeu
    ├── Giọng nói     (preset voices)
    └── Nhân bản giọng (voice cloning)
```

Ràng buộc kiến trúc:
- KHÔNG tạo FastAPI server thứ hai.
- KHÔNG để React gọi trực tiếp VieNeu.
- KHÔNG mở thêm localhost port.
- KHÔNG để mỗi queue worker load một model VieNeu (singleton/shared).
- KHÔNG trộn voice VieNeu vào CapCut catalog cũ.
- KHÔNG thay thế tab cũ.

### 2.1 packages/vieneu-core/ — reusable core

Core KHÔNG được phụ thuộc: FastAPI, SQLAlchemy, Next.js, Tauri, TauriProvider,
VoidMelody queue, VoidMelody database models, global application state.

Core PHẢI cung cấp: contracts (capabilities, errors), fixtures, adapter surface
cho VieNeu `Vieneu(mode="v3turbo")` public API.

## 3. Load & resource policy

| Tài nguyên | Concurrency |
|---|---|
| CapCut | giữ behavior hiện tại (concurrency=3) |
| VieNeu CPU inference | 1 |
| VieNeu GPU inference | 1 |
| Model download | 1 |
| Model load | 1 |
| Voice cloning | 1 |
| VieNeu model instance | singleton/shared |
| Batch parallelism | dùng `infer_batch` bên trong model, không nhân bản model |

- Phải có provider-specific semaphore/resource limiter.
- Cancellation phải giải phóng semaphore và xóa temp files.
- Không được tạo ba VieNeu model instances theo ba queue workers.

## 4. Database compatibility

Migration thêm tối thiểu:
```sql
provider_id       VARCHAR NOT NULL DEFAULT 'capcut'
backbone_id       VARCHAR nullable
style             VARCHAR nullable
voice_profile_id  VARCHAR nullable
request_metadata  TEXT/JSON nullable
```

Yêu cầu:
- Job cũ tự nhận `provider_id='capcut'`.
- Không đổi ID cũ, không đổi audio path cũ, không mất queue history.
- Retry job cũ vẫn dùng provider cũ.
- Migration idempotent, có pre-migration fixture test, có rollback/safety test.
- Không destructive migration.

## 5. Phân phase (thực hiện đúng thứ tự)

| Phase | Branch | Scope |
|---|---|---|
| 0 | feat/vieneu-phase-0-baseline | Baseline, architecture, source pinning, license inventory, CI workflow |
| 1 | feat/vieneu-phase-1-ui-shell | UI shell: Giọng hiện tại / VieNeu / Giọng nói / Nhân bản giọng + placeholder/unavailable states; legacy tab unchanged |
| 2 | feat/vieneu-phase-2-core | Reusable vieneu-core contracts, capabilities, errors, fixtures |
| 3 | feat/vieneu-phase-3-provider-registry | ProviderRegistry, provider discriminator, DB migration |
| 4 | feat/vieneu-phase-4-model-manager | Runtime probe, model manager, downloader, cache, checksum |
| 5 | feat/vieneu-phase-5-preset-tts | VieNeu preset voice single TTS, shared queue, artifact output |
| 6 | feat/vieneu-phase-6-styles-emotions | Reading styles & experimental emotion cues |
| 7 | feat/vieneu-phase-7-streaming | Streaming preview & cancellation |
| 8 | feat/vieneu-phase-8-voice-cloning | Voice cloning, local storage, consent, delete lifecycle |
| 9 | feat/vieneu-phase-9-batch | Batch inference, adaptive resource limits, queue fairness |
| 10 | build/vieneu-phase-10-packaging | EXE/DMG packaging with embedded Python runtime |
| 11 | test/vieneu-phase-11-reliability | Performance, reliability, security, chaos tests |
| 12 | docs/vieneu-phase-12-void-studio-migration | VOID STUDIO migration readiness docs & portable core verification |

Mỗi phase phải có: `VIENEU_PHASE_<N>_COMPLETION_REPORT.md`, `VIENEU_PHASE_<N>_REVIEW.md`.

## 6. Vòng lặp autopilot mỗi phase

```
PLAN → IMPLEMENT → FORMAT → TYPECHECK → TEST → BUILD
→ INDEPENDENT REVIEW → FIX FINDINGS → RE-TEST → RE-REVIEW
→ COMMIT → PUSH → CREATE PR → VERIFY CI → MERGE (khi đủ điều kiện)
→ SYNC MAIN → NEXT PHASE
```

- Reviewer không được là agent đã implement cùng phase.
- Tối đa 3 review-fix cycles cho cùng một blocker.

## 7. Test gates

**Frontend:** install integrity, lint, typecheck, unit tests, component tests,
accessibility tests, production build.

**Python:** formatter, lint, typecheck, unit tests, integration tests, migration
tests, package import isolation test.

**Desktop:** Rust format, Rust clippy, Rust tests, Tauri build checks.

**Integration:** legacy voice list, old job create/batch/retry, old audio
playback, old MP3/M4A download, old DB upgrade, mixed CapCut/VieNeu queue,
VieNeu singleton model, cancellation, checksum failure, interrupted download,
low disk, corrupted model cache, offline cached generation, voice-profile
create/delete, clean temp files.

**Final packaging:** Windows clean machine, macOS Apple Silicon clean machine,
no system Python, no system FFmpeg, first model download, restart, offline
generation, app update preserves model and voice profiles.

Không bỏ test để CI pass. Không đổi expected sai thành đúng. Không mock toàn bộ
end-to-end path rồi tuyên bố production-ready.

## 8. Security & privacy

Local auth áp dụng cho endpoint mới; API bind localhost; không public tunnel;
MIME sniffing; size & duration limits; path traversal protection; safe temp
directories; không log raw audio / secrets / full reference transcript; custom
voice assets lưu local; delete profile xóa toàn bộ owned files; failed profile
creation cleanup; consent bắt buộc trước voice cloning; UI nói rõ người dùng
phải có quyền sử dụng giọng; không tự upload reference audio.

## 9. Licensing

**VieNeu:** giữ Apache-2.0; thêm third-party notices; ghi attribution; pin
source/model revisions; audit transitive dependencies; đánh dấu modified source.

**CapCut:** không coi là license-clear bởi việc thêm VieNeu; giữ licensing
blocker riêng; hỗ trợ build option `legacy+vieneu` và `vieneu-only`. Không
publish public build chứa legacy provider nếu licensing gate chưa đạt.

Model/codec licenses cần audit (MOSS-Audio-Tokenizer-Nano, neucodec, sea-g2p)
— xem license cards HF, có thể restrictive hơn Apache-2.0.

## 10. Stop conditions

Dừng hỏi người điều phối khi:
1. Cần secret/signing certificate chưa tồn tại.
2. Repo bắt buộc human merge, không có auto-merge (→ decision packet).
3. Licensing evidence yêu cầu xin phép rights holder.
4. Migration có thể xóa/rewrite dữ liệu thật.
5. Cần thay đổi public/core architecture ngoài master plan.
6. Cần chi phí/tài khoản trả phí/cloud resource.
7. Security vulnerability không có safe remediation.
8. Cùng blocker không sửa được sau 3 review-fix cycles.
9. Chuẩn bị production tag/publish release chính thức.
10. Không build được trên platform cần phần cứng/credential chưa có.

Khi dừng → tạo `VIENEU_AUTOPILOT_DECISION_PACKET.md`.

## 11. Production release boundary

Được phép: release candidate branch, unsigned artifacts, packaging tests, draft
GitHub release, release notes.

KHÔNG được tự: publish production GitHub Release, tạo production tag, upload
private signing keys, notarize bằng tài khoản cá nhân chưa được cấp, phát hành
public build chứa unresolved legacy licensing. Dừng trước production publication
→ `VIENEU_FINAL_RELEASE_DECISION_PACKET.md`.

## 12. Baseline pins (xác minh Phase 0)

- VoidMelody main HEAD: `0e21ba3b8d083ba9a73ff76a781721c4ab472332` (v0.2.4).
- VieNeu-TTS source SHA: `a8c9fbf99749d5ce45c89111f71558d6ceef3424` (vieneu 3.2.4, Apache-2.0).
- HF model repo: `pnnbao-ump/VieNeu-TTS-v3-Turbo` (subfolder `update` cho PyTorch,
  `onnx_int8` cho ONNX/CPU default). Codec: `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano[-ONNX]`.
  - **Rủi ro:** VieNeu không pin `revision=` trong `hf_hub_download` — luôn fetch
    latest `main`. Cần pin revision ngoài (snapshot HF_HOME hoặc vendor manifest)
    để reproducible. Đây là task Phase 4.
- Python: `>=3.10` (VieNeu); API hiện `>=3.9`. Cần nâng API lên `>=3.10` hoặc
  kiểm tra tương thích — quyết định Phase 2/4.
- Core runtime VieNeu torch-free: onnxruntime, numpy, soundfile, soxr,
  tokenizers, huggingface_hub, sea-g2p, librosa, perth (optional). Không cần
  torch cho CPU/v3 Turbo.

## 13. Kiến trúc baseline hiện tại (đã khảo sát)

### API (apps/api, FastAPI + SQLAlchemy async + Alembic + uv)
- `app/main.py`: lifespan chạy migrations, cleanup, recover jobs, start queue.
- `app/config.py`: Settings (tts_queue_concurrency=3, tts_chunk_concurrency=1).
- `app/providers/base.py`: `TTSProvider` Protocol (`list_voices`, `synthesize`).
- `app/providers/capcut_provider.py`: `CapCutProvider` wrap `CapCutClient`.
- `app/workers/queue_manager.py`: `TTSQueueManager` — mỗi worker tạo 1 provider
  instance qua `provider_factory` (mặc định `CapCutProvider`).
- `app/workers/tts_worker.py`: `execute_tts_job_step` — chunk text, synthesize
  từng chunk qua `asyncio.to_thread(provider.synthesize)`, download, FFmpeg concat.
- `app/models/tts_job.py`: `TTSJobModel` (bảng `tts_jobs`).
- `app/services/tts_service.py`: `create_tts_job`, `claim_job`, batch limits.
- `app/services/database_migrations.py`: Alembic runner + legacy adopt logic.
- `app/middleware/local_auth.py`: `LocalAuthMiddleware` (X-Melody-Token).
- Alembic: baseline `37c7b24d235a`, head `1ccaccfcb3f0`.

### Frontend (apps/web, Next.js 16 + React 19 + Tauri, vitest)
- `src/app/page.tsx` → `TTSStudio`.
- `src/components/tts/tts-studio.tsx`: orchestrator, `useVoices("vi-VN")`,
  default voice `BV421_vivn_streaming`.
- `src/components/tts/voice-settings-panel.tsx`: dropdown giọng + speed slider.
- `src/app/voices/page.tsx`: Voice Library grid.
- `src/lib/api-client.ts`: fetch wrapper, X-Melody-Token.
- `src/hooks/use-voices.ts`: `useVoices(language, q)`.
- `src/contexts/tauri-provider.tsx`: spawn sidecar, port discovery.
- `src-tauri/tauri.conf.json`: productName VoidMelody, externalBin melody-api,
  resources ffmpeg + Voice.json.

### Điểm tích hợp chính
- Phase 1: thêm tab "VieNeu" (Giọng nói / Nhân bản giọng) vào UI; `/voices` page
  + `voice-settings-panel.tsx` + `tts-studio.tsx`. Placeholder states khi
  vieneu-core chưa sẵn sàng.
- Phase 3: migration thêm `provider_id` etc.; `TTSQueueManager` phải route theo
  provider; VieNeu worker path dùng singleton model + semaphore.
- Phase 5: endpoint tạo job VieNeu, queue xử lý, artifact output qua FFmpeg
  pipeline hiện có.