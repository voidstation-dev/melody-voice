"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Trash2,
  User,
  Mic,
  FileText,
  Music,
  Settings2,
  LayoutTemplate,
  Type,
  Download,
  MessageSquare,
  ChevronDown,
  Flame,
} from "lucide-react";

export function AppSidebar() {
  const pathname = usePathname();

  const navItem = (
    href: string,
    label: string,
    Icon: any,
    active?: boolean,
  ) => {
    const isActive = active !== undefined ? active : pathname === href;
    return (
      <Link
        key={href}
        href={href}
        className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
          isActive
            ? "bg-muted text-foreground"
            : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
        }`}
      >
        <Icon className="h-4 w-4" />
        {label}
      </Link>
    );
  };

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <nav className="space-y-1">
          {navItem("/", "Text to Speech", Mic, true)}
        </nav>
      </div>
    </aside>
  );
}
