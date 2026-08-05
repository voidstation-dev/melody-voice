"""Capability flags and provider descriptor for VieNeu.

Capabilities describe what a VieNeu engine instance supports (preset voices,
cloning, streaming, styles, batch, emotion tags) plus operational limits
(sample rate, max text length). The adapter (Phase 3+) uses these to route
requests and to answer capability queries from the frontend.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    supports_preset_voices: bool = True
    supports_voice_cloning: bool = True
    supports_streaming: bool = True
    supports_styles: bool = True
    supports_batch: bool = True
    supports_emotion_tags: bool = True
    max_text_chars: int | None = 256
    sample_rate: int = 48000


@dataclass(frozen=True)
class ProviderDescriptor:
    """Describes the VieNeu provider to the rest of VoidMelody."""

    id: str
    label: str
    version: str | None
    capabilities: Capabilities


def default_capabilities() -> Capabilities:
    """Return the VieNeu v3 Turbo capability set (surveyed in Phase 0).

    The default ``max_text_chars`` reflects the per-chunk character budget the
    engine uses internally (``max_chars=256`` in ``V3TurboVieNeuTTS.infer``);
    the adapter chunks longer inputs before calling the engine (Phase 5).
    """

    return Capabilities(
        supports_preset_voices=True,
        supports_voice_cloning=True,
        supports_streaming=True,
        supports_styles=True,
        supports_batch=True,
        supports_emotion_tags=True,
        max_text_chars=256,
        sample_rate=48000,
    )


def default_descriptor() -> ProviderDescriptor:
    return ProviderDescriptor(
        id="vieneu",
        label="VieNeu",
        version=None,
        capabilities=default_capabilities(),
    )
