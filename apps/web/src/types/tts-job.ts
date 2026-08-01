export type TTSJobStatus = "queued" | "processing" | "completed" | "failed" | "cancelled"

export type TTSJob = {
  id: string
  text: string
  textPreview: string
  voiceType: string
  voiceDisplayName: string
  resourceId: string | null
  rate: number
  status: TTSJobStatus
  progress: number | null
  audioUrl: string | null
  downloadUrl: string | null
  fileSize: number | null
  errorCode: string | null
  errorMessage: string | null
  createdAt: string
  updatedAt: string
  completedAt: string | null
}
