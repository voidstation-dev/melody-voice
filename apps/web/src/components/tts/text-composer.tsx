"use client"
type TextComposerProps = {
  value: string
  onChange: (val: string) => void
  maxLength: number
  disabled?: boolean
}

export function TextComposer({ value, onChange, maxLength, disabled }: TextComposerProps) {
  const currentLen = value.length
  const warning = currentLen >= maxLength * 0.85

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="font-medium">Script Input</span>
        <span className={warning ? "text-amber-500 font-bold" : ""}>
          {currentLen} / {maxLength} chars
        </span>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        maxLength={maxLength}
        placeholder="Nhập nội dung cần chuyển thành giọng nói tại đây..."
        className="min-h-[280px] w-full resize-y bg-transparent text-sm focus:outline-none disabled:opacity-50"
      />
    </div>
  )
}
