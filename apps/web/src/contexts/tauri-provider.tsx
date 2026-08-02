"use client";

import { useEffect, useState } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import { appDataDir, resolveResource } from "@tauri-apps/api/path";
import { setApiConnection } from "@/lib/api-client";
import { Loader2 } from "lucide-react";

export function TauriProvider({ children }: { children: React.ReactNode }) {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if we are running in Tauri
    // @ts-ignore
    if (!window.__TAURI_INTERNALS__) {
      setIsReady(true); // Web mode (development)
      return;
    }

    let sidecarProcess: any = null;
    let isMounted = true;
    const apiToken = crypto.randomUUID();

    async function probeHealth(url: string) {
      try {
        const res = await fetch(`${url}/api/v1/health/live`, { method: "GET" });
        if (res.ok && isMounted) {
          console.log(`Successfully connected to API at ${url}`);
          setApiConnection(url, apiToken);
          setIsReady(true);
          return true;
        }
      } catch (e) {
        // Not reachable yet
      }
      return false;
    }

    async function bootstrap() {
      try {
        const dataDir = await appDataDir();
        const catalogPath = await resolveResource("bin/Voice.json");
        
        // Determine ffmpeg binary name based on OS
        const isWindows = navigator.userAgent.toLowerCase().includes("windows");
        const ffmpegName = isWindows ? "bin/ffmpeg.exe" : "bin/ffmpeg";
        const ffmpegPath = await resolveResource(ffmpegName);
        
        // Let Python pick a random free port
        const apiPort = "0";

        console.log("Starting sidecar with:", { dataDir, catalogPath, ffmpegPath });

        const sidecar = Command.sidecar("bin/melody-api", [], {
          env: {
            PYTHONUNBUFFERED: "1",
            APP_ENV: "production",
            API_HOST: "127.0.0.1",
            API_PORT: apiPort,
            MELODY_API_TOKEN: apiToken,
            MELODY_DATA_DIR: dataDir,
            MELODY_CATALOG_PATH: catalogPath,
            FFMPEG_BINARY_PATH: ffmpegPath,
          }
        });

        const handleOutput = (line: string, source: "STDOUT" | "STDERR") => {
          console.log(`[API ${source}]:`, line);
          const match = line.match(/(?:https?:\/\/)?(?:127\.0\.0\.1|localhost|0\.0\.0\.0):(\d+)/) || line.match(/port\s+(\d+)/i);
          if (match && isMounted) {
            const port = match[1];
            if (port && port !== "0") {
              const url = `http://127.0.0.1:${port}`;
              console.log(`Resolved local API port from ${source}: ${port}`);
              probeHealth(url);
            }
          }
        };

        sidecar.stdout.on('data', (line) => handleOutput(line, "STDOUT"));
        sidecar.stderr.on('data', (line) => handleOutput(line, "STDERR"));

        sidecarProcess = await sidecar.spawn();
      } catch (err: any) {
        console.error("Failed to bootstrap Tauri sidecar", err);
        if (isMounted) {
          setError(err.toString());
        }
      }
    }

    bootstrap();

    return () => {
      isMounted = false;
      if (sidecarProcess) {
        sidecarProcess.kill();
      }
    };
  }, []);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center p-8 text-destructive text-center flex-col gap-4">
        <h2 className="text-xl font-bold">Failed to start local API</h2>
        <p className="font-mono text-sm">{error}</p>
      </div>
    );
  }

  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center bg-background flex-col gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-muted-foreground text-sm font-medium">Starting local environment...</p>
      </div>
    );
  }

  return <>{children}</>;
}
