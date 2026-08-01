import { useContext } from "react";
import { QueueContext } from "@/contexts/queue-context";

export function useQueue() {
  const context = useContext(QueueContext);
  if (context === undefined) {
    throw new Error("useQueue must be used within a QueueProvider");
  }
  return context;
}
