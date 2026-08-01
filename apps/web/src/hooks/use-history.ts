import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

type HistoryResponse = {
  items: TTSJob[]
  page: number
  pageSize: number
  total: number
}

export function useHistory(page = 1) {
  return useQuery({
    queryKey: ["history", page],
    queryFn: () => apiFetch<HistoryResponse>(`/api/v1/tts/jobs?page=${page}`),
  })
}
