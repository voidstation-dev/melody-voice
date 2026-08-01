"use client"
import { useState } from "react"
import { TextComposer } from "./text-composer"
import { VoiceSettingsPanel } from "./voice-settings-panel"
import { useVoices } from "@/hooks/use-voices"
import { useTTSJob } from "@/hooks/use-tts-job"
import { apiFetch } from "@/lib/api-client"
import { TTSJob } from "@/types/tts-job"

export function TTSStudio() {
  const [text, setText] = useState("")
  const [selectedVoice, setSelectedVoice] = useState("BV421_vivn_streaming")
  const [rate, setRate] = useState(1.0)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: voiceData } = useVoices("vi-VN")
  const { data: activeJob } = useTTSJob(activeJobId)

  const handleGenerate = async () => {
    if (!text.trim()) return
    setIsSubmitting(true)
    try {
      const job = await apiFetch<TTSJob>("/api/v1/tts/jobs", {
        method: "POST",
        body: JSON.stringify({
          text,
          voiceType: selectedVoice,
          rate,
        }),
      })
      setActiveJobId(job.id)
    } catch (err) {
      console.error("Job creation failed", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="flex flex-col gap-6 lg:col-span-2">
        <TextComposer value={text} onChange={setText} maxLength={3000} />
        {activeJob && (
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="text-sm font-semibold">Job Status: {activeJob.status}</div>
            {activeJob.audioUrl && (
              <audio controls src={`http://localhost:8000${activeJob.audioUrl}`} className="mt-4 w-full" />
            )}
          </div>
        )}
      </div>
      <div>
        <VoiceSettingsPanel
          voices={voiceData?.items ?? []}
          selectedVoice={selectedVoice}
          onSelectVoice={setSelectedVoice}
          rate={rate}
          onRateChange={setRate}
          onGenerate={handleGenerate}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  )
}
