export type Voice = {
  id: string
  languageCode: string
  languageShort: string
  voiceType: string
  displayName: string
  resourceId: string
  capturedAt: string | null
}

export type VoiceListResponse = {
  items: Voice[]
  page: number
  pageSize: number
  total: number
}
