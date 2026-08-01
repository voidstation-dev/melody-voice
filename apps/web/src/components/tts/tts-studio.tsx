"use client";
import { useState, useEffect } from "react";
import { TextComposer } from "./text-composer";
import { VoiceSettingsPanel } from "./voice-settings-panel";
import { useVoices } from "@/hooks/use-voices";
import { useTTSJob } from "@/hooks/use-tts-job";
import { apiFetch } from "@/lib/api-client";
import { TTSJob } from "@/types/tts-job";
import { Sparkles, Loader2, Clipboard, FileUp } from "lucide-react";
import { useRef } from "react";

export function TTSStudio() {
  const [text, setText] = useState("");
  const [selectedVoice, setSelectedVoice] = useState("BV421_vivn_streaming");
  const [rate, setRate] = useState(1.0);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fakeProgress, setFakeProgress] = useState(0);

  const { data: voiceData } = useVoices("vi-VN");
  const { data: activeJob } = useTTSJob(activeJobId);

  // Load from localStorage on mount
  useEffect(() => {
    const savedText = localStorage.getItem("capvoice_text");
    if (savedText) setText(savedText);

    const savedJobId = localStorage.getItem("capvoice_job_id");
    if (savedJobId) setActiveJobId(savedJobId);
  }, []);

  // Save to localStorage when changed
  useEffect(() => {
    localStorage.setItem("capvoice_text", text);
  }, [text]);

  useEffect(() => {
    if (activeJobId) {
      localStorage.setItem("capvoice_job_id", activeJobId);
    } else {
      localStorage.removeItem("capvoice_job_id");
    }
  }, [activeJobId]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (activeJob?.status === "processing" || activeJob?.status === "queued") {
      setIsSubmitting(true);
      interval = setInterval(() => {
        setFakeProgress((prev) => {
          if (prev >= 95) return prev;
          return prev + Math.floor(Math.random() * 4) + 1;
        });
      }, 800);
    } else if (activeJob?.status === "completed") {
      setIsSubmitting(false);
      setFakeProgress(100);
    } else if (activeJob?.status === "failed") {
      setIsSubmitting(false);
      setFakeProgress(0);
    }
    return () => clearInterval(interval);
  }, [activeJob?.status]);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setIsSubmitting(true);
    setFakeProgress(0);
    try {
      const currentVoiceObj = voiceData?.items?.find(
        (v) => v.voiceType === selectedVoice,
      );
      const job = await apiFetch<TTSJob>("/api/v1/tts/jobs", {
        method: "POST",
        body: JSON.stringify({
          text,
          voiceType: selectedVoice,
          resourceId: currentVoiceObj?.resourceId || "",
          rate,
        }),
      });
      setActiveJobId(job.id);
    } catch (err) {
      console.error("Job creation failed", err);
      setIsSubmitting(false);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePaste = async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      if (clipboardText) {
        setText(text + (text ? " " : "") + clipboardText);
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
        setText(text + (text ? "\n\n" : "") + content);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="grid h-full min-h-0 gap-8 lg:grid-cols-[1fr_360px]">
      <div className="flex flex-col h-full min-h-0 relative gap-2">
        <div className="rounded-2xl border border-border bg-card p-2 shadow-sm z-20 transition-all flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={handlePaste}
              disabled={isSubmitting}
              className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
              title="Paste from clipboard"
            >
              <Clipboard className="h-4 w-4" />
              <span className="hidden sm:inline">Paste</span>
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isSubmitting}
              className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
              title="Import text file"
            >
              <FileUp className="h-4 w-4" />
              <span className="hidden sm:inline">Import TXT</span>
            </button>
            <input
              type="file"
              accept=".txt"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={isSubmitting || !text}
            className="flex items-center gap-2 rounded-xl bg-primary px-8 py-2.5 text-xs font-bold text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {isSubmitting ? "PROCESSING..." : "SEND"}
          </button>
        </div>
        <TextComposer
          value={text}
          onChange={setText}
          maxLength={500000}
          onGenerate={handleGenerate}
          isSubmitting={isSubmitting}
        />
      </div>
      <div className="h-full overflow-y-auto pr-2">
        <VoiceSettingsPanel
          voices={voiceData?.items ?? []}
          selectedVoice={selectedVoice}
          onSelectVoice={setSelectedVoice}
          rate={rate}
          onRateChange={setRate}
          onGenerate={handleGenerate}
          isSubmitting={isSubmitting}
          activeJob={activeJob}
          fakeProgress={fakeProgress}
        />
      </div>
    </div>
  );
}
