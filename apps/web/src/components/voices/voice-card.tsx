"use client"
import { Voice } from "@/types/voice"

export function VoiceCard({ voice }: { voice: Voice }) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-border bg-card p-5 shadow-sm transition-all hover:border-primary">
      <div>
        <div className="flex items-center justify-between">
          <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            {voice.languageCode}
          </span>
        </div>
        <h3 className="mt-3 text-base font-bold">{voice.displayName}</h3>
        <p className="mt-1 font-mono text-xs text-muted-foreground">{voice.voiceType}</p>
      </div>
    </div>
  )
}
