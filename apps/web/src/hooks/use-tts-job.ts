import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

export function useTTSJob(jobId: string | null) {
  return useQuery({
    queryKey: ["tts-job", jobId],
    queryFn: () => apiFetch<TTSJob>(`/api/v1/tts/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "queued" || status === "processing" ? 1000 : false
    },
  })
}
