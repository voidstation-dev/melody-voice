"use client"
import Link from "next/link"
import { Volume2, Activity } from "lucide-react"

export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
          <Volume2 className="h-5 w-5" />
        </div>
        <span className="text-lg font-bold tracking-tight">CapVoice Studio</span>
      </div>
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-emerald-500">
          <Activity className="h-3.5 w-3.5" /> API Ready
        </span>
      </div>
    </header>
  )
}
