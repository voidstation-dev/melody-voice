import { getVersion } from "@tauri-apps/api/app";

export async function getRuntimeVersion(): Promise<string> {
  if (
    typeof window === "undefined" ||
    !(window as Window & { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__
  ) {
    return "dev";
  }

  return getVersion();
}
