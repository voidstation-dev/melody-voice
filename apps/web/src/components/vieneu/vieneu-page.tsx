"use client";
import { useState } from "react";
import { Mic, UserPlus, Sparkles } from "lucide-react";

type Section = "voices" | "cloning";

export function VieneuPage() {
  const [section, setSection] = useState<Section>("voices");

  const sections: { key: Section; label: string; icon: typeof Mic; heading: string; body: string }[] = [
    {
      key: "voices",
      label: "Giọng nói",
      icon: Mic,
      heading: "Giọng nói (preset)",
      body: "Các giọng đọc tiếng Việt có sẵn của VieNeu. Tính năng sẽ khả dụng ở giai đoạn sau khi engine được tích hợp.",
    },
    {
      key: "cloning",
      label: "Nhân bản giọng",
      icon: UserPlus,
      heading: "Nhân bản giọng (voice cloning)",
      body: "Tạo giọng nói tùy chỉnh từ đoạn âm thanh tham chiếu của bạn. Tính năng sẽ khả dụng ở giai đoạn sau.",
    },
  ];

  const active = sections.find((s) => s.key === section)!;
  const Icon = active.icon;

  return (
    <div className="flex flex-col h-full">
      <div className="mb-6 shrink-0">
        <h1 className="text-2xl font-bold">VieNeu</h1>
        <p className="text-sm text-muted-foreground">
          Engine TTS tiếng Việt on-device với nhân bản giọng
        </p>
      </div>

      <div className="mb-6 shrink-0">
        <div className="inline-flex rounded-xl border border-border bg-card p-1 shadow-sm">
          {sections.map((s) => {
            const SectionIcon = s.icon;
            return (
              <button
                key={s.key}
                type="button"
                aria-pressed={section === s.key}
                onClick={() => setSection(s.key)}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-colors ${
                  section === s.key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <SectionIcon className="h-4 w-4" />
                {s.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 pr-2 pb-6">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card p-10 text-center shadow-sm min-h-[280px]">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Icon className="h-7 w-7" />
          </div>
          <h2 className="mt-5 text-lg font-bold text-foreground">{active.heading}</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{active.body}</p>
          <button
            type="button"
            disabled
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary/50 px-5 py-2.5 text-xs font-bold text-primary-foreground opacity-60 cursor-not-allowed"
            title="Sắp ra mắt"
          >
            <Sparkles className="h-4 w-4" />
            Sắp ra mắt
          </button>
          <p className="mt-4 text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60">
            Đang tích hợp · chưa khả dụng
          </p>
        </div>
      </div>
    </div>
  );
}