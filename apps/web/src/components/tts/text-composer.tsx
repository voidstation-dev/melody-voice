"use client";
import { Sparkles, Loader2, Clipboard, FileUp } from "lucide-react";
import { useRef } from "react";

type TextComposerProps = {
  value: string;
  onChange: (val: string) => void;
  maxLength: number;
  disabled?: boolean;
  onGenerate: () => void;
  isSubmitting: boolean;
};

export function TextComposer({
  value,
  onChange,
  maxLength,
  disabled,
  onGenerate,
  isSubmitting,
}: TextComposerProps) {
  const hasText = value.length > 0;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePaste = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      if (clipboardText) {
        onChange(value + (value ? " " : "") + clipboardText);
      }
    } catch (err) {
      console.error("Failed to read clipboard contents: ", err);
      alert("Please allow clipboard permissions or paste manually.");
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        onChange(value + (value ? "\n\n" : "") + content);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="relative flex flex-col h-full rounded-2xl bg-card p-8 shadow-sm">
      <h2 className="mb-6 text-sm font-semibold text-foreground">
        Text to Speech Playground
      </h2>

      <div className="relative flex-1">
        {/* Beautiful Placeholder - Only visible when empty */}
        {!hasText && (
          <div className="pointer-events-none absolute inset-0 text-xl lg:text-2xl font-medium leading-relaxed text-muted-foreground/30">
            Bring your attention to the crown of your head... Notice any
            sensations there. Slowly let your{" "}
            <span className="bg-primary text-primary-foreground px-2 rounded-lg inline-block">
              awareness
            </span>{" "}
            travel down to your forehead, your eyes, your jaw.
            <br />
            <br />
            If you notice any tension, imagine it softening with each breath.
          </div>
        )}

        {/* Actual Textarea for input */}
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled || isSubmitting}
          maxLength={maxLength}
          placeholder=""
          className="absolute inset-0 h-full w-full resize-none bg-transparent text-xl lg:text-2xl font-medium leading-relaxed text-foreground focus:outline-none disabled:opacity-50 z-10 custom-scrollbar"
        />
      </div>
    </div>
  );
}
