import "./globals.css"
import { ThemeProvider } from "@/components/providers/theme-provider"
import { QueryProvider } from "@/components/providers/query-provider"

export const metadata = {
  title: "CapVoice Studio",
  description: "Local-first Text to Speech Studio",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <QueryProvider>
          <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light">
            {children}
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
