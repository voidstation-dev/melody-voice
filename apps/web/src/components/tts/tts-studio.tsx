"use client";
import { useState, useEffect } from "react";
import { TextComposer } from "./text-composer";
import { VoiceSettingsPanel } from "./voice-settings-panel";
import { useVoices } from "@/hooks/use-voices";
import { useQueue } from "@/hooks/use-queue";
import { useTextFileDrop } from "@/hooks/use-text-file-drop";
import { TextImportConflictDialog } from "./text-import-conflict-dialog";
import { JobQueueSidebar } from "./job-queue-sidebar";
import { BatchImportModal } from "./batch-import-modal";
import { ImportedTextFile, TextImportError } from "@/types/text-import";
import { apiFetch } from "@/lib/api-client";
import { getBatchLimitError } from "@/lib/batch-limits";
import { TTSJob, BatchJobCreateResponse } from "@/types/tts-job";
import { Sparkles, Loader2, Clipboard, FileUp, FolderOpen } from "lucide-react";
import { useRef } from "react";

export function TTSStudio() {
  const [text, setText] = useState("");
  const [selectedVoice, setSelectedVoice] = useState("BV421_vivn_streaming");
  const [rate, setRate] = useState(1.0);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [conflictDialog, setConflictDialog] = useState<{isOpen: boolean, file: ImportedTextFile | null}>({isOpen: false, file: null});
  
  const [batchModalOpen, setBatchModalOpen] = useState(false);
  const [batchFiles, setBatchFiles] = useState<ImportedTextFile[]>([]);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { addToQueue } = useQueue();

  const handleFiles = (files: ImportedTextFile[]) => {
    if (files.length === 0) return;
    
    if (files.length === 1 && !batchModalOpen) {
      const file = files[0];
      if (text.trim().length > 0) {
        setConflictDialog({ isOpen: true, file });
      } else {
        setText(file.text);
      }
    } else {
      setBatchFiles(files);
      setBatchModalOpen(true);
    }
  };

  const handleErrors = (errors: TextImportError[]) => {
    errors.forEach(err => alert(`Error importing ${err.fileName}: ${err.message}`));
  };

  const { isDragging, isValidDrag, dragProps, processFiles } = useTextFileDrop({
    allowMultiple: true,
    maxFileBytes: 10 * 1024 * 1024,
    onFiles: handleFiles,
    onErrors: handleErrors,
  });

  const handleFolderSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFiles(Array.from(e.target.files));
    }
    if (folderInputRef.current) {
      folderInputRef.current.value = "";
    }
  };

  const handleStartBatchJobs = async (selectedFiles: ImportedTextFile[]) => {
    const limitError = getBatchLimitError(selectedFiles);
    if (limitError === "BATCH_FILE_LIMIT_EXCEEDED") {
      alert("A batch can contain at most 50 files.");
      return;
    }
    if (limitError === "BATCH_TEXT_LIMIT_EXCEEDED") {
      alert("A batch can contain at most 500,000 characters.");
      return;
    }

    const createdJobs = [];
    // Generate a single batchId for all files in this batch so they group together in the queue
    const batchId = crypto.randomUUID();
    
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      try {
        const batchResponse = await apiFetch<BatchJobCreateResponse>("/api/v1/tts/jobs", {
          method: "POST",
          body: JSON.stringify({
            text: file.text,
            voiceType: selectedVoice,
            rate: file.speed ?? rate,
            sourceFileName: file.fileName,
            sourceFileSize: file.sizeBytes,
            batchId: batchId,
            batchPosition: i,
          }),
        });
        createdJobs.push(...batchResponse.jobs);
      } catch (err) {
        console.error(`Failed to create job for ${file.fileName}`, err);
      }
    }
    
    if (createdJobs.length > 0) {
      addToQueue(createdJobs);
    }
  };

  const { data: voiceData } = useVoices("vi-VN");

  useEffect(() => {
    const savedText = localStorage.getItem("melody_text");
    if (savedText) setText(savedText);
  }, []);

  useEffect(() => {
    localStorage.setItem("melody_text", text);
  }, [text]);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setIsSubmitting(true);
    try {
      const currentVoiceObj = voiceData?.items?.find(
        (v) => v.voiceType === selectedVoice,
      );
      const batchResponse = await apiFetch<BatchJobCreateResponse>("/api/v1/tts/jobs", {
        method: "POST",
        body: JSON.stringify({
          text,
          voiceType: selectedVoice,
          resourceId: currentVoiceObj?.resourceId || "",
          rate,
        }),
      });
      addToQueue(batchResponse.jobs);
      setText("");
    } catch (err) {
      console.error("Job creation failed", err);
    } finally {
      setIsSubmitting(false);
    }
  };

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
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length > 0) {
      processFiles(files);
    }
    e.target.value = "";
  };

  return (
    <div className="grid h-full min-h-0 gap-6 md:grid-cols-[1fr_340px] xl:grid-cols-[1fr_380px]">
      <div className="flex flex-col h-full min-h-0 relative gap-3">
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
            
            <button
              onClick={() => folderInputRef.current?.click()}
              disabled={isSubmitting}
              className="flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-primary/10 hover:text-primary transition-colors disabled:opacity-50"
              title="Import folder of TXT files"
            >
              <FolderOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Import Folder</span>
            </button>
            <input
              type="file"
              ref={folderInputRef}
              onChange={handleFolderSelect}
              className="hidden"
              // @ts-ignore - webkitdirectory is a valid property for folder selection
              webkitdirectory=""
              directory=""
              multiple
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
          disabled={isSubmitting}
          isDragging={isDragging}
          isValidDrag={isValidDrag}
          dragProps={dragProps}
        />
        <TextImportConflictDialog
          isOpen={conflictDialog.isOpen}
          fileName={conflictDialog.file?.fileName || ""}
          onClose={() => setConflictDialog({ isOpen: false, file: null })}
          onReplace={() => {
            setText(conflictDialog.file?.text || "");
            setConflictDialog({ isOpen: false, file: null });
          }}
          onAppend={() => {
            setText(text + (text ? "\n\n" : "") + (conflictDialog.file?.text || ""));
            setConflictDialog({ isOpen: false, file: null });
          }}
        />
        <BatchImportModal
          isOpen={batchModalOpen}
          onClose={() => setBatchModalOpen(false)}
          files={batchFiles}
          onStartJobs={handleStartBatchJobs}
        />
      </div>
      <div className="h-full flex flex-col gap-4 min-h-0 pr-2">
        <div className="shrink-0">
          <VoiceSettingsPanel
            voices={voiceData?.items ?? []}
            selectedVoice={selectedVoice}
            onSelectVoice={setSelectedVoice}
            rate={rate}
            onRateChange={setRate}
            onGenerate={handleGenerate}
            isSubmitting={isSubmitting}
          />
        </div>
        <JobQueueSidebar />
      </div>
    </div>
  );
}
