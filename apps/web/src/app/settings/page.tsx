"use client"
import { PageContainer } from "@/components/app-shell/page-container"
import { UpdateSettings } from "@/components/settings/update-settings"
import { useTheme } from "next-themes"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()

  return (
    <PageContainer>
      <div className="overflow-y-auto pb-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">Manage appearance and app updates.</p>
        </div>

        <div className="max-w-2xl space-y-4">
          <section aria-labelledby="appearance-heading" className="rounded-xl border border-border bg-card p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 id="appearance-heading" className="font-semibold">Appearance</h2>
                <p className="mt-1 text-xs text-muted-foreground">Choose how the studio looks.</p>
              </div>
              <select
                aria-label="Theme"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="min-h-10 rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <option value="dark">Dark Studio</option>
                <option value="light">Light</option>
                <option value="system">System</option>
              </select>
            </div>
          </section>

          <UpdateSettings />
        </div>
      </div>
    </PageContainer>
  )
}
