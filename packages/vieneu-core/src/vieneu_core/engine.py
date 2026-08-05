"""Runtime probe and singleton model manager for the VieNeu engine.

This module wraps `from vieneu import Vieneu` behind a framework-agnostic
surface so apps/api (Phase 5) and VOID STUDIO (future) can share one model
instance. Resource policy: model load concurrency = 1, model instance is
singleton/shared — never one-per-queue-worker.

The actual TTS call (``Vieneu(mode="v3turbo").infer(...)``) is wired in Phase 5;
this phase provides the probe + lazy singleton manager.
"""

from __future__ import annotations

import asyncio
import os
import platform
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeProbe:
    """Snapshot of the local runtime capabilities relevant to VieNeu."""

    device: str  # "cpu" | "cuda"
    backend: str  # "onnx" | "pytorch"
    onnxruntime_available: bool
    torch_available: bool
    torch_cuda_available: bool
    cpu_count: int
    threads: int  # 0 = engine default
    platform: str


def _importable(module_name: str) -> bool:
    try:
        import importlib

        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def probe_runtime() -> RuntimeProbe:
    """Probe the local runtime without loading the model.

    On Apple Silicon, ``device`` resolves to ``"cpu"`` (the v3 Turbo path does
    not use MPS) and the torch-free ONNX engine runs on CPU.
    """

    cpu_count = os.cpu_count() or 1
    onnx_available = _importable("onnxruntime")
    torch_available = _importable("torch")
    torch_cuda = False
    if torch_available:
        try:
            import torch  # type: ignore

            torch_cuda = bool(torch.cuda.is_available())
        except ImportError:
            torch_cuda = False
    device = "cuda" if torch_cuda else "cpu"
    # v3 Turbo: auto → ONNX on CPU, PyTorch on CUDA.
    backend = "pytorch" if torch_cuda else "onnx"
    threads = 0  # 0 = engine default (min(max(cpu_count // 2, 1), 8))
    return RuntimeProbe(
        device=device,
        backend=backend,
        onnxruntime_available=onnx_available,
        torch_available=torch_available,
        torch_cuda_available=torch_cuda,
        cpu_count=cpu_count,
        threads=threads,
        platform=platform.platform(),
    )


class ModelManager:
    """Singleton manager for the shared VieNeu engine instance.

    Resource policy: exactly one model instance per process. Load concurrency
    is 1 (an ``asyncio.Lock`` serializes loads). Callers obtain the shared
    instance via :meth:`get_engine`; the first call loads lazily.
    """

    def __init__(
        self,
        *,
        engine_factory: Callable[[], Any] | None = None,
        load_timeout_seconds: float | None = None,
    ) -> None:
        self._engine_factory = engine_factory
        self._engine: Any | None = None
        self._load_lock = asyncio.Lock()
        self._load_timeout = load_timeout_seconds

    def is_loaded(self) -> bool:
        return self._engine is not None

    async def get_engine(self) -> Any:
        """Return the shared engine instance, loading it on first call."""
        if self._engine is not None:
            return self._engine
        async with self._load_lock:
            # Re-check inside the lock (another task may have loaded it).
            if self._engine is not None:
                return self._engine
            factory = self._engine_factory or self._default_factory
            loop = asyncio.get_running_loop()
            if self._load_timeout is not None:
                self._engine = await asyncio.wait_for(
                    loop.run_in_executor(None, factory),
                    timeout=self._load_timeout,
                )
            else:
                self._engine = await loop.run_in_executor(None, factory)
        return self._engine

    def unload(self) -> None:
        """Release the engine instance (best-effort close)."""
        if self._engine is not None:
            close = getattr(self._engine, "close", None)
            if callable(close):
                try:
                    close()
                except RuntimeError:
                    pass
        self._engine = None

    @staticmethod
    def _default_factory() -> Any:
        """Default factory constructing the real VieNeu v3 Turbo engine.

        Sets ``HF_HOME`` if ``VIENEU_HF_HOME`` is present so the manager can
        point Vieneu at a pre-populated cache (Phase 4 downloader).
        """
        hf_home = os.environ.get("VIENEU_HF_HOME")
        if hf_home:
            os.environ.setdefault("HF_HOME", hf_home)
        from vieneu import Vieneu  # type: ignore

        return Vieneu(mode="v3turbo", device="auto", backend="auto", precision="int8")
