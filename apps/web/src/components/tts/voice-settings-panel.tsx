"use client"
import { Voice } from "@/types/voice"

type VoiceSettingsPanelProps = {
  voices: Voice[]
  selectedVoice: string
  onSelectVoice: (v: string) => void
  rate: number
  onRateChange: (r: number) => void
  onGenerate: () => void
  isSubmitting: boolean
}

export function VoiceSettingsPanel({
  voices,
  selectedVoice,
  onSelectVoice,
  rate,
  onRateChange,
  onGenerate,
  isSubmitting,
}: VoiceSettingsPanelProps) {
  return (
    <div className="flex flex-col gap-6 rounded-xl border border-border bg-card p-5">
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold text-muted-foreground">Giọng đọc (Voice)</label>
        <select
          value={selectedVoice}
          onChange={(e) => onSelectVoice(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none"
        >
          {voices.map((v) => (
            <option key={v.voiceType} value={v.voiceType}>
              {v.displayName} ({v.languageCode})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex justify-between text-xs font-semibold text-muted-foreground">
          <span>Tốc độ đọc (Speed)</span>
          <span className="text-foreground">{rate.toFixed(2)}x</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="2.0"
          step="0.05"
          value={rate}
          onChange={(e) => onRateChange(parseFloat(e.target.value))}
          className="accent-primary"
        />
      </div>

      <button
        onClick={onGenerate}
        disabled={isSubmitting}
        className="mt-2 w-full rounded-lg bg-primary py-3 font-semibold text-primary-foreground shadow transition-opacity hover:opacity-90 disabled:opacity-50"
      >
        {isSubmitting ? "Creating audio..." : "Generate Speech"}
      </button>
    </div>
  )
}
