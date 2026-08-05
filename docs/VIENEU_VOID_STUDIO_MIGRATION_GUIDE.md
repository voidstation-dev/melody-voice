# VieNeu-TTS Void Studio Migration Guide

This document details how to migrate and integrate the newly refactored `vieneu-core` standalone package into the broader VOID STUDIO ecosystem.

## 1. Portable Core Design
The `vieneu-core` module located in `packages/vieneu-core` has been explicitly designed to be framework-agnostic. Static analysis tests verify that it carries zero dependencies on `FastAPI`, `SQLAlchemy`, Tauri, or internal `app` modules.
It relies purely on universally available primitives (e.g. `asyncio`) and its direct Python dependencies (e.g. `onnxruntime`, `numpy`, `huggingface_hub`).

## 2. Installation
To install `vieneu-core` within VOID STUDIO:
```bash
# Add as a workspace dependency (if using monorepo structure)
uv add "vieneu-core @ ./packages/vieneu-core"
```

## 3. The ModelManager Contract (Singleton Pattern)
The core export of `vieneu-core` is the `ModelManager`. It handles:
- **Lazy Initialization**: It only allocates memory when `get_engine()` is called.
- **Concurrency Locks**: It ensures only a single thread/coroutine is loading the PyTorch/ONNX engine at a time to prevent OOMs.

### Example Integration:
```python
import asyncio
from vieneu_core.engine import ModelManager

# Maintain this at the application or dependency-injection level
manager = ModelManager(load_timeout_seconds=30.0)

async def synthesize_text(text: str):
    # This automatically loads the model into RAM if not already loaded
    engine = await manager.get_engine()
    
    # NOTE: inference is CPU bound. DO NOT run it directly in the async event loop!
    # Always offload to a thread pool behind a concurrency semaphore.
    wav = await asyncio.to_thread(
        engine.infer,
        text=text,
        voice="v3",
        style="tu_nhien"
    )
    return wav
```

## 4. Concurrency Management
Because the default execution uses the `v3turbo` ONNX engine, inference is completely CPU-bound.
**CRITICAL**: You MUST guard calls to `engine.infer` with an `asyncio.Semaphore(1)` (or small bound) and dispatch via `asyncio.to_thread`. Allowing unbound concurrency will saturate the CPU scheduler, freeze the main FastAPI event loop, and cause catastrophic cascading timeouts.

```python
inference_semaphore = asyncio.Semaphore(1)

async def safe_synthesize():
    async with inference_semaphore:
        return await asyncio.to_thread(engine.infer, ...)
```

## 5. Caching and Downloader Logic
`vieneu-core` ships with a deterministic `ModelDownloader`. It fetches the exact pinned SHAs for reproducibility. 
You can override the storage path by providing the `VIENEU_HF_HOME` environment variable before the app starts. The `ModelManager` will ensure that the underlying `huggingface_hub` client respects this directory path, preventing downloads to the user's root `~/.cache`.

## 6. Cleanup
If VOID STUDIO supports hot-reloading or graceful shutdown, ensure you invoke:
```python
manager.unload()
```
This forces the garbage collector to free the ONNX runtime session, clearing ~200MB+ of RAM immediately.
