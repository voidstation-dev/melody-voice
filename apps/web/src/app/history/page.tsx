"use client"
import { PageContainer } from "@/components/app-shell/page-container"
import { useHistory } from "@/hooks/use-history"

export default function HistoryPage() {
  const { data, isLoading } = useHistory()

  return (
    <PageContainer>
      <div className="flex flex-col h-full">
        <div className="mb-6 shrink-0">
          <h1 className="text-2xl font-bold">Lịch sử tạo (History)</h1>
          <p className="text-sm text-muted-foreground">Quản lý các file âm thanh đã khởi tạo</p>
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 pr-2 pb-6">
          {isLoading ? (
            <div className="text-sm text-muted-foreground">Loading history...</div>
          ) : (
            <div className="flex flex-col gap-3">
              {data?.items.map((job) => (
                <div key={job.id} className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
                  <div>
                    <div className="font-semibold">{job.voiceDisplayName}</div>
                    <div className="text-xs text-muted-foreground">{job.textPreview}</div>
                  </div>
                  <div className="text-xs font-semibold capitalize">{job.status}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
