"""vieneu-core: framework-agnostic contracts for the VieNeu-TTS integration.

Public re-exports for the stable surface adapters depend on. This package has
no dependency on FastAPI, SQLAlchemy, Next.js, Tauri, or VoidMelody app state.
"""

from vieneu_core.capabilities import (
    Capabilities,
    ProviderDescriptor,
    default_capabilities,
    default_descriptor,
)
from vieneu_core.contracts import (
    AudioFormat,
    Style,
    SynthesizeRequest,
    SynthesizeResult,
    VieneuEngine,
    Voice,
)
from vieneu_core.errors import (
    CloningConsentError,
    InferenceError,
    InvalidStyleError,
    InvalidTextError,
    InvalidVoiceError,
    ModelLoadFailedError,
    ModelNotAvailableError,
    ResourceBusyError,
    VieneuCoreError,
    VoiceNotFoundError,
)

__all__ = [
    "AudioFormat",
    "Capabilities",
    "CloningConsentError",
    "InferenceError",
    "InvalidStyleError",
    "InvalidTextError",
    "InvalidVoiceError",
    "ModelLoadFailedError",
    "ModelNotAvailableError",
    "ProviderDescriptor",
    "ResourceBusyError",
    "Style",
    "SynthesizeRequest",
    "SynthesizeResult",
    "VieneuCoreError",
    "VieneuEngine",
    "Voice",
    "VoiceNotFoundError",
    "default_capabilities",
    "default_descriptor",
]