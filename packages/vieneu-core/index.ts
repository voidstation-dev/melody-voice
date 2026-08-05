// TypeScript shared types for the VieNeu-TTS integration.
//
// These mirror the Python contracts in src/vieneu_core/ so the VoidMelody web
// frontend can type the VieNeu data returned by the local API. The frontend
// never imports the Python core; it imports these type-only declarations.
//
// Field naming follows camelCase to match the API JSON conventions already
// used by the existing CapCut endpoints (see apps/web/src/types/voice.ts).
//
// This file is type-only (no runtime values) and is inert until the API
// returns VieNeu data (Phase 5). Phase 5 will wire a tsconfig path alias
// (@vieneu-core/* -> packages/vieneu-core/*) so apps/web can import from it.

export type VoiceSource = "preset" | "cloned"

export interface Voice {
  voiceId: string
  displayName: string
  languageCode: string
  gender: string
  style?: string | null
  description?: string | null
  source: VoiceSource
}

export interface Style {
  id: string
  label: string
  tokenId?: number | null
}

export type AudioFormat = "wav" | "mp3" | "m4a"

export interface Capabilities {
  supportsPresetVoices: boolean
  supportsVoiceCloning: boolean
  supportsStreaming: boolean
  supportsStyles: boolean
  supportsBatch: boolean
  supportsEmotionTags: boolean
  maxTextChars: number | null
  sampleRate: number
}

export interface ProviderDescriptor {
  id: string
  label: string
  version: string | null
  capabilities: Capabilities
}

export interface SynthesizeRequest {
  text: string
  voiceId: string
  style?: string | null
  rate: number
  refAudioPath?: string | null
}

export interface SynthesizeResult {
  sampleRate: number
  dtype: string
  durationSeconds: number | null
  // pcmBytes is a base64 string when transported over JSON from the API.
  // The frontend generally consumes the final artifact URL, not raw PCM.
  pcmBytesBase64?: string | null
}

export type VieneuErrorCode =
  | "MODEL_NOT_AVAILABLE"
  | "MODEL_LOAD_FAILED"
  | "VOICE_NOT_FOUND"
  | "INVALID_TEXT"
  | "INVALID_STYLE"
  | "INVALID_VOICE"
  | "INFERENCE_ERROR"
  | "CLONING_CONSENT_REQUIRED"
  | "RESOURCE_BUSY"
  | "VIENEU_CORE_ERROR"

export interface VieneuErrorPayload {
  code: VieneuErrorCode
  message: string
  retryable: boolean
}