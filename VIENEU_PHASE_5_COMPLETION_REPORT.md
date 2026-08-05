# Phase 5 Completion Report

## Scope
- Tích hợp singleton VieNeu engine từ `ModelManager`.
- Implement endpoint hỗ trợ preset voice TTS (dùng FIXTURE_VOICES).
- Tích hợp shared queue (định tuyến `provider_id='vieneu'` dùng lock/semaphore).
- Bơm artifact output từ model vào FFmpeg pipeline hiện có.

## Implementation Details
1. Created `VieneuProvider` in `app/providers/vieneu_provider.py` implementing the `TTSProvider` async protocol.
2. Initialized `ModelManager` and limited CPU inference to 1 concurrency using `asyncio.Semaphore(1)`.
3. Encoded generated PCM `wav` into `mp3` via FFmpeg subprocess directly in the provider, making it seamlessly compatible with the existing `combine_audio_parts` FFmpeg concat pipeline.
4. Updated `queue_manager.py` to route requests based on `job.provider_id` via a `provider_registry`.
5. Created unit tests for `VieneuProvider` in `test_vieneu_provider.py`.
6. Formatted and checked types for the entire `apps/api` codebase.

## Verification
- Linter and typechecker pass.
- Unit tests pass.
- Direct model loading and inference works on local runtime, correctly raising `ValueError` on invalid voice types, verifying full engine instantiation.

## Next Steps
Proceed to Phase 6: Reading styles & experimental emotion cues.
