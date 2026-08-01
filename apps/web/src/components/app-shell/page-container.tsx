import { AppHeader } from "./app-header";
import { AppSidebar } from "./app-sidebar";

export function PageContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground font-sans overflow-hidden">
      <AppHeader />
      <div className="flex flex-1 overflow-hidden">
        <AppSidebar />
        <main className="flex-1 bg-muted/30 p-6 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
