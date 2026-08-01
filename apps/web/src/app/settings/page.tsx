"use client"
import { PageContainer } from "@/components/app-shell/page-container"
import { useTheme } from "next-themes"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()

  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Cấu hình (Settings)</h1>
        <p className="text-sm text-muted-foreground">Cấu hình giao diện và tùy chọn mặc định</p>
      </div>

      <div className="max-w-xl space-y-6 rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold">Giao diện (Theme)</div>
            <div className="text-xs text-muted-foreground">Tùy chọn hiển thị sáng / tối</div>
          </div>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm"
          >
            <option value="dark">Dark Studio</option>
            <option value="light">Light</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>
    </PageContainer>
  )
}
