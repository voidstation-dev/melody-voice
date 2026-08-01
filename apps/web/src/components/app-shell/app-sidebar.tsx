"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Mic, Library, History, Settings } from "lucide-react"

const navItems = [
  { label: "Studio", href: "/", icon: Mic },
  { label: "Voice Library", href: "/voices", icon: Library },
  { label: "History", href: "/history", icon: History },
  { label: "Settings", href: "/settings", icon: Settings },
]

export function AppSidebar() {
  const pathname = usePathname()
  return (
    <aside className="hidden md:flex w-60 flex-col border-r border-border bg-card p-4">
      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
