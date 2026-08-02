"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { getRuntimeVersion } from "@/lib/runtime-version";
import { useTauri } from "./tauri-provider";

export type UpdateStatus =
  | "idle"
  | "checking"
  | "up-to-date"
  | "available"
  | "downloading"
  | "installing"
  | "error";

export type AvailableUpdate = {
  currentVersion: string;
  version: string;
  date?: string;
  notes?: string;
};

type UpdateResource = {
  currentVersion: unknown;
  version: unknown;
  date?: unknown;
  body?: unknown;
  download: (onEvent?: (event: DownloadEvent) => void) => Promise<void>;
  install: () => Promise<void>;
  close: () => Promise<void>;
};

type DownloadEvent =
  | { event: "Started"; data: { contentLength?: number } }
  | { event: "Progress"; data: { chunkLength: number } }
  | { event: "Finished" };

type UpdateContextValue = {
  status: UpdateStatus;
  currentVersion: string;
  availableUpdate: AvailableUpdate | null;
  downloadedBytes: number;
  totalBytes?: number;
  errorMessage?: string;
  checkForUpdates: (options: { interactive: boolean }) => Promise<void>;
  installAvailableUpdate: () => Promise<void>;
  dismissUpdate: () => void;
};

const UpdateContext = createContext<UpdateContextValue | null>(null);
let startupCheckStarted = false;

function readUpdateMetadata(update: UpdateResource): AvailableUpdate | null {
  const { currentVersion, version, date, body } = update;
  if (
    typeof currentVersion !== "string" ||
    !currentVersion.trim() ||
    typeof version !== "string" ||
    !version.trim() ||
    (date !== undefined && typeof date !== "string") ||
    (typeof date === "string" && date.length > 0 && Number.isNaN(Date.parse(date))) ||
    (body !== undefined && typeof body !== "string")
  ) {
    return null;
  }

  const metadata: AvailableUpdate = { currentVersion, version };
  if (typeof date === "string" && date) metadata.date = date;
  if (typeof body === "string" && body) metadata.notes = body;
  return metadata;
}

async function closeUpdate(update: UpdateResource | null) {
  if (!update) return;
  try {
    await update.close();
  } catch {
    // Closing is best-effort and must not hide the user-facing updater result.
  }
}

export function useUpdate() {
  const context = useContext(UpdateContext);
  if (!context) {
    throw new Error("useUpdate must be used within UpdateProvider");
  }
  return context;
}

export function UpdateProvider({ children }: { children: React.ReactNode }) {
  const { isDesktop, isReady, shutdownSidecar, restartSidecar } = useTauri();
  const [status, setStatus] = useState<UpdateStatus>("idle");
  const [currentVersion, setCurrentVersion] = useState("dev");
  const [availableUpdate, setAvailableUpdate] = useState<AvailableUpdate | null>(null);
  const [downloadedBytes, setDownloadedBytes] = useState(0);
  const [totalBytes, setTotalBytes] = useState<number | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const updateResourceRef = useRef<UpdateResource | null>(null);
  const checkPromiseRef = useRef<Promise<void> | null>(null);
  const installPromiseRef = useRef<Promise<void> | null>(null);
  const dismissedRef = useRef(false);

  const checkForUpdates = useCallback(
    async ({ interactive }: { interactive: boolean }) => {
      if (!isDesktop) return;
      if (checkPromiseRef.current) return checkPromiseRef.current;
      if (installPromiseRef.current) return installPromiseRef.current;

      if (interactive) dismissedRef.current = false;
      const checkPromise = (async () => {
        setStatus("checking");
        setErrorMessage(undefined);
        const previousUpdate = updateResourceRef.current;
        updateResourceRef.current = null;
        setAvailableUpdate(null);
        await closeUpdate(previousUpdate);

        try {
          const { check } = await import("@tauri-apps/plugin-updater");
          const update = (await check()) as UpdateResource | null;
          if (!update) {
            setStatus("up-to-date");
            return;
          }

          const metadata = readUpdateMetadata(update);
          if (!metadata) {
            await closeUpdate(update);
            if (interactive) {
              setErrorMessage("Update information could not be read. Try again.");
              setStatus("error");
            } else {
              setStatus("idle");
            }
            return;
          }

          if (dismissedRef.current && !interactive) {
            await closeUpdate(update);
            setStatus("idle");
            return;
          }

          updateResourceRef.current = update;
          setAvailableUpdate(metadata);
          setStatus("available");
        } catch {
          if (interactive) {
            setErrorMessage("Could not check for updates. Try again.");
            setStatus("error");
          } else {
            setStatus("idle");
          }
        }
      })();

      checkPromiseRef.current = checkPromise.finally(() => {
        checkPromiseRef.current = null;
      });
      return checkPromiseRef.current;
    },
    [isDesktop],
  );

  const dismissUpdate = useCallback(() => {
    dismissedRef.current = true;
    const update = updateResourceRef.current;
    updateResourceRef.current = null;
    setAvailableUpdate(null);
    setErrorMessage(undefined);
    setStatus("idle");
    void closeUpdate(update);
  }, []);

  const installAvailableUpdate = useCallback(async () => {
    if (!isDesktop) return;
    if (installPromiseRef.current) return installPromiseRef.current;
    if (checkPromiseRef.current) return checkPromiseRef.current;

    const update = updateResourceRef.current;
    if (!update) return;

    let phase: "download" | "install" = "download";
    let sidecarWasShutdown = false;
    const installPromise = (async () => {
      setStatus("downloading");
      setErrorMessage(undefined);
      setDownloadedBytes(0);
      setTotalBytes(undefined);

      try {
        await update.download((event) => {
          if (event.event === "Started") {
            const contentLength = event.data.contentLength;
            setTotalBytes(
              typeof contentLength === "number" && Number.isFinite(contentLength) && contentLength > 0
                ? contentLength
                : undefined,
            );
          } else if (event.event === "Progress") {
            const chunkLength = event.data.chunkLength;
            if (Number.isFinite(chunkLength) && chunkLength > 0) {
              setDownloadedBytes((bytes) => bytes + chunkLength);
            }
          }
        });

        phase = "install";
        setStatus("installing");
        await shutdownSidecar();
        sidecarWasShutdown = true;
        await update.install();

        updateResourceRef.current = null;
        await closeUpdate(update);
        const { relaunch } = await import("@tauri-apps/plugin-process");
        await relaunch();
      } catch {
        if (updateResourceRef.current === update) {
          updateResourceRef.current = null;
          await closeUpdate(update);
        }
        if (sidecarWasShutdown) {
          try {
            await restartSidecar();
          } catch {
            // Keep the updater error visible even if the sidecar cannot restart.
          }
        }
        setErrorMessage(
          phase === "download"
            ? "Could not download the update. Try again."
            : "Could not install the update. Try again.",
        );
        setStatus("error");
      }
    })();

    installPromiseRef.current = installPromise.finally(() => {
      installPromiseRef.current = null;
    });
    return installPromiseRef.current;
  }, [isDesktop, restartSidecar, shutdownSidecar]);

  useEffect(() => {
    let active = true;
    void getRuntimeVersion().then((version) => {
      if (active) setCurrentVersion(version);
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isDesktop || !isReady || startupCheckStarted) return;
    startupCheckStarted = true;
    void checkForUpdates({ interactive: false });
  }, [checkForUpdates, isDesktop, isReady]);

  useEffect(
    () => () => {
      const update = updateResourceRef.current;
      updateResourceRef.current = null;
      void closeUpdate(update);
    },
    [],
  );

  const contextValue = useMemo(
    () => ({
      status,
      currentVersion,
      availableUpdate,
      downloadedBytes,
      totalBytes,
      errorMessage,
      checkForUpdates,
      installAvailableUpdate,
      dismissUpdate,
    }),
    [
      availableUpdate,
      checkForUpdates,
      currentVersion,
      dismissUpdate,
      downloadedBytes,
      errorMessage,
      installAvailableUpdate,
      status,
      totalBytes,
    ],
  );

  return <UpdateContext.Provider value={contextValue}>{children}</UpdateContext.Provider>;
}
