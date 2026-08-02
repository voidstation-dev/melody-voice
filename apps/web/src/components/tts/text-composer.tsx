"use client";
import { FileText } from "lucide-react";

type TextComposerProps = {
  value: string;
  onChange: (val: string) => void;
  maxLength: number;
  disabled?: boolean;
  isDragging?: boolean;
  isValidDrag?: boolean;
  dragProps?: React.HTMLAttributes<HTMLDivElement>;
};

export function TextComposer({
  value,
  onChange,
  maxLength,
  disabled,
  isDragging,
  isValidDrag,
  dragProps,
}: TextComposerProps) {
  const hasText = value.length > 0;

  return (
    <div 
      className={`relative flex flex-1 flex-col h-full min-h-[300px] rounded-2xl p-6 shadow-sm transition-all duration-200 ease-in-out border-2 ${
        isDragging 
          ? isValidDrag ? "border-primary bg-primary/5" : "border-destructive bg-destructive/5" 
          : "border-transparent bg-card"
      }`}
      {...dragProps}
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
          Text to Speech Playground
        </h2>
        <span className="text-xs font-semibold text-muted-foreground/70">
          {value.length.toLocaleString()} / {maxLength.toLocaleString()} chars
        </span>
      </div>

      <div className="relative flex-1 min-h-0 w-full">
        {/* Beautiful Placeholder - Only visible when empty */}
        {!hasText && (
          <div className="pointer-events-none absolute inset-0 text-base lg:text-lg font-normal leading-relaxed text-muted-foreground/30 p-1">
            Welcome to <span className="bg-primary/20 text-primary px-2 py-0.5 rounded-lg inline-block font-bold">Melody</span>, your premium voice synthesis studio.
            <br />
            <br />
            Paste your script, select a voice, and let our AI breathe life into your words. Ready to create something amazing?
          </div>
        )}

        {/* Actual Textarea for input */}
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          maxLength={maxLength}
          placeholder=""
          className="absolute inset-0 h-full w-full resize-none bg-transparent text-base lg:text-lg font-normal leading-relaxed text-foreground focus:outline-none disabled:opacity-50 z-10 custom-scrollbar p-1"
        />
      </div>

      {/* Drag Overlay */}
      {isDragging && (
        <div className="pointer-events-none absolute inset-0 z-50 flex flex-col items-center justify-center rounded-2xl bg-background/40 backdrop-blur-[2px]">
          <div className={`flex flex-col items-center justify-center p-8 rounded-2xl ${isValidDrag ? "text-primary" : "text-destructive"}`}>
            <FileText className="h-16 w-16 mb-4 animate-bounce" />
            <h3 className="text-2xl font-bold">
              {isValidDrag ? "Drop TXT file to import" : "Only .txt files are supported"}
            </h3>
            {isValidDrag && (
              <p className="text-muted-foreground mt-2 text-center max-w-sm">
                UTF-8 plain text · up to 2MB
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
