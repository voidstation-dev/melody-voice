"""Framework-agnostic contracts for the VieNeu-TTS integration.

These dataclasses and the VieneuEngine Protocol are the stable surface that
VoidMelody's thin FastAPI adapter (Phase 3+) and VOID STUDIO plugin handlers
(future) depend on. Nothing here imports FastAPI, SQLAlchemy, numpy, or the
VieNeu engine itself — contracts are pure standard-library Python so they can
be imported in any context (tests, adapter, UI type generation).

The concrete engine implementation (wrapping `from vieneu import Vieneu`) is
Phase 4/5; this module only defines the shape it must conform to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class AudioFormat(str, Enum):
    """Output artifact formats the adapter can produce via FFmpeg."""

    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"


@dataclass(frozen=True)
class Style:
    """A VieNeu reading style.

    Known styles (from the v3 Turbo config surveyed in Phase 0):
    ``tu_nhien`` (natural), ``tin_tuc`` (news), ``doc_truyen`` (storytelling).
    ``token_id`` is the model's internal style token; ``None`` means "use the
    voice's default style".
    """

    id: str
    label: str
    token_id: int | None = None


@dataclass(frozen=True)
class Voice:
    """A VieNeu voice (preset or cloned).

    ``source`` is ``"preset"`` for built-in voices and ``"cloned"`` for
    user-created voice profiles (Phase 8). ``voice_id`` is the stable id used
    in API requests (for preset voices it is the Vietnamese display name, e.g.
    ``"Minh Đức"``).
    """

    voice_id: str
    display_name: str
    language_code: str
    gender: str
    style: str | None = None
    description: str | None = None
    source: str = "preset"


@dataclass(frozen=True)
class SynthesizeRequest:
    """A request to synthesize speech.

    ``ref_audio_path`` is set only for voice-cloning requests (Phase 8); for
    preset-voice synthesis it is ``None`` and ``voice_id`` selects a preset.
    ``rate`` is a 0.5–2.0 multiplier (matches the existing CapCut schema).
    """

    text: str
    voice_id: str
    style: str | None = None
    rate: float = 1.0
    ref_audio_path: str | None = None


@dataclass(frozen=True)
class SynthesizeResult:
    """Raw PCM audio returned by the engine.

    The adapter (Phase 5) converts this to an artifact (MP3/M4A) via FFmpeg.
    To keep contracts import-light, audio is stored as raw little-endian
    float32 PCM bytes plus ``sample_rate`` and ``dtype``; the engine
    implementation is responsible for converting numpy arrays to this form
    (``arr.astype("<f4").tobytes()``).
    """

    pcm_bytes: bytes
    sample_rate: int
    dtype: str = "float32"
    duration_seconds: float | None = None


class VieneuEngine(Protocol):
    """Structural protocol for a VieNeu TTS engine.

    The concrete implementation lives in phases 4–5; adapters depend on this
    Protocol so they can be tested with a stub/fake engine.
    """

    def list_voices(self) -> list[Voice]: ...

    def synthesize(self, request: SynthesizeRequest) -> SynthesizeResult: ...