"use client";
import { useQueue } from "@/hooks/use-queue";
import { Loader2, CheckCircle2, XCircle, Clock, Download, Play, Trash2, RotateCcw, Layers } from "lucide-react";
import { TTSJob } from "@/types/tts-job";
import { apiFetch, resolveApiUrl } from "@/lib/api-client";
import { useState, useRef } from "react";

export function JobQueueSidebar() {
  const { queue, activeJobs, completedJobs } = useQueue();

  // Sort queue: processing/queued first, then completed (newest first)
  const sortedQueue = [...queue].sort((a, b) => {
    const aActive = a.status === "processing" || a.status === "queued" ? 1 : 0;
    const bActive = b.status === "processing" || b.status === "queued" ? 1 : 0;
    if (aActive !== bActive) return bActive - aActive;
    
    // If they belong to the same batch, sort by batchPosition ascending so the first item stays at top
    if (a.batchId && b.batchId && a.batchId === b.batchId) {
      return (a.batchPosition ?? 0) - (b.batchPosition ?? 0);
    }
    
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  if (queue.length === 0) {
    return (
      <div className="relative rounded-2xl border-2 border-dashed border-border/60 bg-muted/10 p-8 flex flex-col items-center justify-center text-center overflow-hidden min-h-[240px] group transition-colors hover:border-primary/30 hover:bg-muted/20">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative flex items-center justify-center w-14 h-14 rounded-full bg-background shadow-sm border border-border/50 mb-4 group-hover:scale-110 transition-transform duration-300">
          <Layers className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
        <h3 className="text-sm font-bold text-foreground mb-1.5">Queue is empty</h3>
        <p className="text-xs text-muted-foreground max-w-[200px] leading-relaxed">
          Submit a job from the playground to see the generation progress here.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm flex flex-col gap-4 flex-1 min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <h3 className="text-sm font-bold tracking-wider text-muted-foreground">QUEUE</h3>
        <span className="text-xs font-medium text-muted-foreground px-2 py-0.5 rounded-full bg-muted">
          {activeJobs.length} active
        </span>
      </div>

      <div className="flex flex-col gap-3 overflow-y-auto pr-1 pb-2">
        {sortedQueue.map((job) => (
          <JobItem key={job.id} job={job} />
        ))}
      </div>
    </div>
  );
}

function JobItem({ job }: { job: TTSJob }) {
  const { removeFromQueue, retryJob } = useQueue();
  const [playing, setPlaying] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const togglePlay = () => {
    if (playing) {
      audioRef.current?.pause();
    } else {
      audioRef.current?.play();
    }
    setPlaying(!playing);
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    await removeFromQueue(job.id);
  };

  const handleRetry = async () => {
    setIsRetrying(true);
    await retryJob(job.id);
    setIsRetrying(false);
  };

  return (
    <div className={`shrink-0 relative overflow-hidden rounded-xl border p-3.5 flex flex-col gap-3 transition-all duration-300 ${
      job.status === "completed" ? "bg-primary/[0.02] border-primary/20 shadow-sm" : 
      job.status === "processing" ? "bg-background border-primary/30 shadow-md shadow-primary/5" :
      job.status === "failed" ? "bg-destructive/[0.02] border-destructive/20" :
      "bg-background border-border"
    }`}>
      {/* Subtle background progress bar for processing */}
      {job.status === "processing" && (
        <div 
          className="absolute bottom-0 left-0 h-[3px] bg-primary transition-all duration-500 ease-out"
          style={{ width: `${job.progress ?? 0}%` }}
        />
      )}

      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {job.sourceFileName && (
              <span className="truncate max-w-[120px] rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-bold text-muted-foreground border border-border/50">
                {job.sourceFileName}
              </span>
            )}
            
            <span className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary border border-primary/20">
              {job.rate?.toFixed(1) || "1.0"}x
            </span>
            
            {/* Show processing status and progress */}
            {job.status === "processing" && (
              <span className="text-[9px] font-black uppercase tracking-widest text-primary">
                PROCESSING {job.progress !== null ? `· ${job.progress}%` : ""}
              </span>
            )}
            
            {/* Show duration if completed or failed */}
            {(job.status === "completed" || job.status === "failed") && job.startedAt && (job.completedAt || job.updatedAt) && (
              <span className="text-[10px] font-medium text-muted-foreground/60">
                {(() => {
                  const start = new Date(job.startedAt).getTime();
                  const end = new Date(job.completedAt || job.updatedAt).getTime();
                  const diff = Math.max(0, Math.round((end - start) / 1000));
                  if (diff < 60) return `${diff}s`;
                  const m = Math.floor(diff / 60);
                  const s = diff % 60;
                  return `${m}m ${s}s`;
                })()}
              </span>
            )}
          </div>
          <p className={`text-xs leading-relaxed line-clamp-2 ${job.status === "completed" ? "text-foreground font-medium" : "text-muted-foreground"}`}>
            {job.textPreview}
          </p>
        </div>
        
        <div className="shrink-0 flex items-center gap-1.5">
          <div className="flex items-center justify-center h-8 w-8 rounded-full bg-background border border-border/50 shadow-sm">
            {job.status === "queued" && <Clock className="h-4 w-4 text-muted-foreground" />}
            {job.status === "processing" && <Loader2 className="h-4 w-4 text-primary animate-spin" />}
            {job.status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
            {job.status === "failed" && <XCircle className="h-4 w-4 text-red-500" />}
          </div>
          
          {job.status === "failed" && (
            <button 
              onClick={handleRetry}
              disabled={isRetrying}
              className="flex items-center justify-center h-8 w-8 rounded-full bg-background border border-border/50 shadow-sm text-blue-500/70 hover:text-blue-500 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all cursor-pointer disabled:opacity-50"
              title="Retry Job"
            >
              <RotateCcw className={`h-3.5 w-3.5 ${isRetrying ? "animate-spin" : ""}`} />
            </button>
          )}

          <button 
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex items-center justify-center h-8 w-8 rounded-full bg-background border border-border/50 shadow-sm text-red-500/70 hover:text-red-500 hover:border-red-500/30 hover:bg-red-500/5 transition-all cursor-pointer disabled:opacity-50"
            title="Delete Job"
          >
            {isDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {job.status === "completed" && job.audioUrl && (
        <div className="flex items-center gap-2 mt-1 pt-3 border-t border-border/40">
          <button 
            onClick={togglePlay}
            className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2 text-[10px] font-extrabold uppercase tracking-wider transition-all ${
              playing 
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20" 
                : "bg-primary/10 text-primary hover:bg-primary/20"
            }`}
          >
            <Play className={`h-3 w-3 ${playing ? "animate-pulse" : ""}`} />
            {playing ? "Pause" : "Play"}
          </button>
          
          <div className="flex-none flex items-center gap-1.5">
            <a 
              href={job.downloadUrl ? resolveApiUrl(`${job.downloadUrl}?format=mp3`) : ""} 
              download
              className="flex items-center justify-center px-2.5 py-2 rounded-lg border border-border hover:bg-muted text-[10px] font-bold text-muted-foreground hover:text-foreground transition-colors"
              title="Download MP3"
            >
              MP3
            </a>
            <a 
              href={job.downloadUrl ? resolveApiUrl(`${job.downloadUrl}?format=m4a`) : ""} 
              download
              className="flex items-center justify-center px-2.5 py-2 rounded-lg border border-border hover:bg-muted text-[10px] font-bold text-muted-foreground hover:text-foreground transition-colors"
              title="Download M4A"
            >
              M4A
            </a>
          </div>
          
          <audio 
            ref={audioRef} 
            src={resolveApiUrl(job.audioUrl)} 
            onEnded={() => setPlaying(false)} 
            onPause={() => setPlaying(false)}
            onPlay={() => setPlaying(true)}
            className="hidden" 
          />
        </div>
      )}

      {job.status === "failed" && (
        <div className="mt-1 p-2 rounded-md bg-destructive/10 border border-destructive/20">
          <p className="text-[10px] font-medium text-destructive">
            {job.errorMessage || "An error occurred"}
          </p>
        </div>
      )}
    </div>
  );
}
