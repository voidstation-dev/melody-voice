"""Deterministic in-memory fixtures for vieneu-core tests and adapter tests.

These fixtures do NOT load the real VieNeu model or its preset-voice JSON; they
are small, stable, and dependency-free, so later phases (apps/api adapter
tests, Phase 3+) can exercise the adapter/registry without a real model.
"""

from __future__ import annotations

from vieneu_core.capabilities import Capabilities, default_capabilities
from vieneu_core.contracts import Style, SynthesizeRequest, Voice

# Three known VieNeu v3 Turbo reading styles (Phase 0 survey).
FIXTURE_STYLES: tuple[Style, ...] = (
    Style(id="tu_nhien", label="Tự nhiên", token_id=16),
    Style(id="tin_tuc", label="Tin tức", token_id=17),
    Style(id="doc_truyen", label="Đọc truyện", token_id=18),
)

# A small, deterministic subset of preset voices — NOT the full 14-voice
# catalog (that is loaded at runtime in Phase 4/5). Names follow the VieNeu
# convention of Vietnamese display names used as voice ids.
FIXTURE_VOICES: tuple[Voice, ...] = (
    Voice(
        voice_id="Minh Đức",
        display_name="Minh Đức",
        language_code="vi-VN",
        gender="male",
        style="tin_tuc",
        description="Nam · Bắc · tin tức",
        source="preset",
    ),
    Voice(
        voice_id="Trúc Ly",
        display_name="Trúc Ly",
        language_code="vi-VN",
        gender="female",
        style="tu_nhien",
        description="Nữ · Bắc · tự nhiên",
        source="preset",
    ),
    Voice(
        voice_id="Thái Sơn",
        display_name="Thái Sơn",
        language_code="vi-VN",
        gender="male",
        style="doc_truyen",
        description="Nam · Nam · kể chuyện",
        source="preset",
    ),
)


def make_synthesize_request(**overrides) -> SynthesizeRequest:
    """Build a SynthesizeRequest with sensible defaults for tests."""

    return SynthesizeRequest(
        text=overrides.get("text", "Xin chào, đây là đoạn thử nghiệm."),
        voice_id=overrides.get("voice_id", "Minh Đức"),
        style=overrides.get("style", None),
        rate=overrides.get("rate", 1.0),
        ref_audio_path=overrides.get("ref_audio_path", None),
    )


def make_capabilities(**overrides) -> Capabilities:
    """Build a Capabilities object with the VieNeu defaults for tests."""

    base = default_capabilities()
    return Capabilities(
        supports_preset_voices=overrides.pop(
            "supports_preset_voices", base.supports_preset_voices
        ),
        supports_voice_cloning=overrides.pop(
            "supports_voice_cloning", base.supports_voice_cloning
        ),
        supports_streaming=overrides.pop("supports_streaming", base.supports_streaming),
        supports_styles=overrides.pop("supports_styles", base.supports_styles),
        supports_batch=overrides.pop("supports_batch", base.supports_batch),
        supports_emotion_tags=overrides.pop(
            "supports_emotion_tags", base.supports_emotion_tags
        ),
        max_text_chars=overrides.pop("max_text_chars", base.max_text_chars),
        sample_rate=overrides.pop("sample_rate", base.sample_rate),
    )
