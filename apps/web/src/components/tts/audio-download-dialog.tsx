import { useState, useEffect } from "react";
import { Download, X, FileAudio } from "lucide-react";
import { getFirstLine, slugify } from "@/lib/utils";
import { TTSJob } from "@/types/tts-job";

type AudioDownloadDialogProps = {
  isOpen: boolean;
  onClose: () => void;
  job: TTSJob | null;
  format: "mp3" | "m4a";
  onStartDownload: (fileName: string) => void;
};

export function AudioDownloadDialog({
  isOpen,
  onClose,
  job,
  format,
  onStartDownload,
}: AudioDownloadDialogProps) {
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    if (isOpen && job) {
      const suggestedName = slugify(getFirstLine(job.text)) || `melody-${job.id}`;
      setFileName(suggestedName);
    }
  }, [isOpen, job]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose();
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => {
        document.body.style.overflow = "unset";
        window.removeEventListener("keydown", handleKeyDown);
      };
    } else {
      document.body.style.overflow = "unset";
    }
  }, [isOpen, onClose]);

  if (!isOpen || !job) return null;

  const handleDownload = () => {
    if (!fileName.trim()) return;
    onStartDownload(fileName.trim());
  };

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="mb-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <FileAudio className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground">Download Audio</h3>
              <p className="text-xs text-muted-foreground mt-0.5 text-orange-500/80">
                You can close this popup during download
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mb-6 flex flex-col gap-2">
          <label className="text-xs font-medium text-muted-foreground ml-1">File Name</label>
          <div className="relative flex items-center">
            <input
              type="text"
              value={fileName}
              onChange={(e) => setFileName(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none transition-colors focus:border-primary pr-12"
              placeholder="audio-filename"
              autoFocus
            />
            <span className="absolute right-4 text-sm text-muted-foreground pointer-events-none">
              .{format}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button
            onClick={handleDownload}
            disabled={!fileName.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-all"
          >
            <Download className="h-4 w-4" />
            <span>Start Download</span>
          </button>
          
          <button
            onClick={onClose}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-muted/50 px-4 py-2.5 text-sm font-bold text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
