"""Standalone error hierarchy for vieneu-core.

These errors are framework-agnostic (no FastAPI/HTTP coupling). The thin
adapter (Phase 3) maps them to HTTP status codes and the existing
``TTSJobError`` codes used by the VoidMelody queue/worker. Error codes are
string constants so they stay stable across the core↔adapter boundary.
"""

from __future__ import annotations

# Error code constants — stable across the core↔adapter boundary.
MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
VOICE_NOT_FOUND = "VOICE_NOT_FOUND"
INVALID_TEXT = "INVALID_TEXT"
INVALID_STYLE = "INVALID_STYLE"
INVALID_VOICE = "INVALID_VOICE"
INFERENCE_ERROR = "INFERENCE_ERROR"
CLONING_CONSENT_REQUIRED = "CLONING_CONSENT_REQUIRED"
RESOURCE_BUSY = "RESOURCE_BUSY"
MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"


class VieneuCoreError(Exception):
    """Base error for vieneu-core.

    Attributes:
        code: stable string code (see module constants) for adapter mapping.
        message: human-readable detail.
        retryable: whether the caller may retry the same request.
    """

    code: str = "VIENEU_CORE_ERROR"

    def __init__(
        self, *, message: str, retryable: bool = False, code: str | None = None
    ):
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        if code is not None:
            self.code = code


class ModelNotAvailableError(VieneuCoreError):
    """The model is not loaded / not downloaded yet."""

    code = MODEL_NOT_AVAILABLE

    def __init__(
        self, *, message: str = "VieNeu model is not available", retryable: bool = True
    ):
        super().__init__(message=message, retryable=retryable, code=self.code)


class ModelLoadFailedError(VieneuCoreError):
    """Loading the model failed (corrupted cache, OOM, etc.)."""

    code = MODEL_LOAD_FAILED

    def __init__(
        self, *, message: str = "Failed to load VieNeu model", retryable: bool = False
    ):
        super().__init__(message=message, retryable=retryable, code=self.code)


class VoiceNotFoundError(VieneuCoreError):
    code = VOICE_NOT_FOUND

    def __init__(self, *, voice_id: str, retryable: bool = False):
        super().__init__(
            message=f"Voice not found: {voice_id!r}",
            retryable=retryable,
            code=self.code,
        )
        self.voice_id = voice_id


class InvalidTextError(VieneuCoreError):
    code = INVALID_TEXT

    def __init__(self, *, message: str = "Invalid text", retryable: bool = False):
        super().__init__(message=message, retryable=retryable, code=self.code)


class InvalidStyleError(VieneuCoreError):
    code = INVALID_STYLE

    def __init__(self, *, style: str, retryable: bool = False):
        super().__init__(
            message=f"Invalid style: {style!r}",
            retryable=retryable,
            code=self.code,
        )
        self.style = style


class InvalidVoiceError(VieneuCoreError):
    code = INVALID_VOICE

    def __init__(self, *, message: str = "Invalid voice", retryable: bool = False):
        super().__init__(message=message, retryable=retryable, code=self.code)


class InferenceError(VieneuCoreError):
    code = INFERENCE_ERROR

    def __init__(
        self, *, message: str = "VieNeu inference failed", retryable: bool = True
    ):
        super().__init__(message=message, retryable=retryable, code=self.code)


class CloningConsentError(VieneuCoreError):
    """Raised when a voice-cloning request lacks the required consent (Phase 8)."""

    code = CLONING_CONSENT_REQUIRED

    def __init__(
        self,
        *,
        message: str = "Voice cloning requires explicit consent",
        retryable: bool = False,
    ):
        super().__init__(message=message, retryable=retryable, code=self.code)


class ResourceBusyError(VieneuCoreError):
    """Raised when the per-provider semaphore is exhausted (concurrency=1)."""

    code = RESOURCE_BUSY

    def __init__(
        self, *, message: str = "VieNeu engine is busy", retryable: bool = True
    ):
        super().__init__(message=message, retryable=retryable, code=self.code)
