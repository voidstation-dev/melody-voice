"use client"
import { useState } from "react"
import { PageContainer } from "@/components/app-shell/page-container"
import { VoiceCard } from "@/components/voices/voice-card"
import { useVoices } from "@/hooks/use-voices"

export default function VoicesPage() {
  const [search, setSearch] = useState("")
  const { data, isLoading } = useVoices(undefined, search)

  return (
    <PageContainer>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Library</h1>
          <p className="text-sm text-muted-foreground">Khám phá và nghe thử các giọng đọc sẵn có</p>
        </div>
        <input
          type="text"
          placeholder="Tìm giọng đọc..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-border bg-card px-4 py-2 text-sm focus:outline-none"
        />
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading voices...</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((voice) => (
            <VoiceCard key={voice.voiceType} voice={voice} />
          ))}
        </div>
      )}
    </PageContainer>
  )
}
