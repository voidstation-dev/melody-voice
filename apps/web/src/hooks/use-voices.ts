import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { VoiceListResponse } from "@/types/voice"

export function useVoices(language?: string, q?: string) {
  return useQuery({
    queryKey: ["voices", language, q],
    queryFn: () => {
      const params = new URLSearchParams()
      if (language) params.set("language", language)
      if (q) params.set("q", q)
      return apiFetch<VoiceListResponse>(`/api/v1/voices?${params.toString()}`)
    },
  })
}
