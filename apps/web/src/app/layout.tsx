import "./globals.css"
import { ThemeProvider } from "@/components/providers/theme-provider"
import { QueryProvider } from "@/components/providers/query-provider"

export const metadata = {
  title: "Melody - Text to Speech Studio",
  description: "A premium Text to Speech Studio created by VoidStation.",
}

import { QueueProvider } from "@/contexts/queue-context"

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>
          <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light">
            <QueueProvider>
              {children}
            </QueueProvider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
