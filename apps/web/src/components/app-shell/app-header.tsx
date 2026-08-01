"use client";
import { Volume2, Activity } from "lucide-react";

export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-border bg-card px-6">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Activity className="h-5 w-5" />
        </div>
        <span className="text-xl font-extrabold tracking-tight">Melody</span>
      </div>
    </header>
  );
}
