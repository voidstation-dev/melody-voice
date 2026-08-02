"use client";
import { createContext, useContext, useState, ReactNode } from "react";
import { TTSJob } from "@/types/tts-job";

type QueueContextType = {
  queue: TTSJob[];
  addToQueue: (jobs: TTSJob[]) => void;
  removeFromQueue: (jobId: string) => void;
  retryJob: (jobId: string) => void;
  clearQueue: () => void;
  refreshQueue: () => void;
  activeJobs: TTSJob[];
  completedJobs: TTSJob[];
};

import { useQuery, useQueries, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";

type TTSJobListResponse = {
  items: TTSJob[];
  page: number;
  pageSize: number;
  total: number;
};

export const QueueContext = createContext<QueueContextType | undefined>(undefined);

export function QueueProvider({ children }: { children: ReactNode }) {
  const [localAddedJobs, setLocalAddedJobs] = useState<TTSJob[]>([]);

  const { data, refetch: refetchList } = useQuery({
    queryKey: ["tts-jobs-list"],
    queryFn: async () => {
      const res = await apiFetch<TTSJobListResponse>("/api/v1/tts/jobs?pageSize=50");
      setLocalAddedJobs([]); // Clear local jobs when the main list updates
      return res;
    },
    // No refetchInterval! List only fetches on mount, window focus, or manual trigger
  });

  const baseQueue = data?.items || [];

  // Combine base list with newly added local jobs
  const combinedMap = new Map<string, TTSJob>();
  baseQueue.forEach(j => combinedMap.set(j.id, j));
  localAddedJobs.forEach(j => {
    if (!combinedMap.has(j.id)) combinedMap.set(j.id, j);
  });
  
  const allInitialJobs = Array.from(combinedMap.values());

  // Identify which jobs are currently active and need polling
  const activeIdsToPoll = allInitialJobs
    .filter(j => j.status === "queued" || j.status === "processing")
    .map(j => j.id);

  // Dynamically poll ONLY the active jobs
  const jobQueries = useQueries({
    queries: activeIdsToPoll.map(id => ({
      queryKey: ["tts-job", id],
      queryFn: () => apiFetch<TTSJob>(`/api/v1/tts/jobs/${id}`),
      refetchInterval: (query: any) => {
        const data = query.state.data;
        if (data && (data.status === "completed" || data.status === "failed")) {
          return false; // Stop polling when finished
        }
        return 1000; // Poll every 1 second
      },
    }))
  });

  // Merge the polled data over the initial list
  let queue = allInitialJobs.map(job => {
    const q = jobQueries.find(q => q.data && q.data.id === job.id);
    return q?.data || job;
  });

  // Keep it sorted: newest first
  queue.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

  const addToQueue = (jobs: TTSJob[]) => {
    setLocalAddedJobs(prev => {
      const newJobs = jobs.filter(j => !prev.find(p => p.id === j.id));
      return [...newJobs, ...prev];
    });
    // Trigger list fetch in the background to sync eventually
    refetchList();
  };

  const queryClient = useQueryClient();

  const removeFromQueue = async (jobId: string) => {
    // Optimistically remove from cache list
    queryClient.setQueryData<TTSJobListResponse>(["tts-jobs-list"], (old) => {
      if (!old) return old;
      return { ...old, items: old.items.filter(j => j.id !== jobId) };
    });
    // Optimistically remove from local adds
    setLocalAddedJobs(prev => prev.filter(j => j.id !== jobId));

    try {
      await apiFetch(`/api/v1/tts/jobs/${jobId}`, {
        method: "DELETE"
      });
      // Optionally refetch to ensure sync
      refetchList();
    } catch (error) {
      console.error("Failed to delete job:", error);
      // Revert if failed
      refetchList();
    }
  };

  const retryJob = async (jobId: string) => {
    try {
      await apiFetch(`/api/v1/tts/jobs/${jobId}/retry`, {
        method: "POST"
      });
      refetchList();
    } catch (error) {
      console.error("Failed to retry job:", error);
    }
  };

  const clearQueue = () => {
    refetchList();
  };

  const activeJobs = queue.filter((j) => j.status === "processing" || j.status === "queued");
  const completedJobs = queue.filter((j) => j.status === "completed" || j.status === "failed");

  return (
    <QueueContext.Provider
      value={{
        queue,
        addToQueue,
        removeFromQueue,
        retryJob,
        clearQueue,
        refreshQueue: () => refetchList(),
        activeJobs,
        completedJobs,
      }}
    >
      {children}
    </QueueContext.Provider>
  );
}
