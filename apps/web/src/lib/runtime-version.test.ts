import { afterEach, describe, expect, it, vi } from "vitest";

const getVersion = vi.fn();

vi.mock("@tauri-apps/api/app", () => ({ getVersion }));

describe("getRuntimeVersion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    getVersion.mockReset();
  });

  it("uses dev in a browser without the Tauri runtime", async () => {
    vi.stubGlobal("window", {});
    const { getRuntimeVersion } = await import("./runtime-version");

    await expect(getRuntimeVersion()).resolves.toBe("dev");
    expect(getVersion).not.toHaveBeenCalled();
  });

  it("uses dev when the browser exposes an unavailable Tauri marker", async () => {
    vi.stubGlobal("window", { __TAURI_INTERNALS__: undefined });
    const { getRuntimeVersion } = await import("./runtime-version");

    await expect(getRuntimeVersion()).resolves.toBe("dev");
    expect(getVersion).not.toHaveBeenCalled();
  });

  it("returns the Tauri application version in the desktop runtime", async () => {
    vi.stubGlobal("window", { __TAURI_INTERNALS__: {} });
    getVersion.mockResolvedValue("0.2.0");
    const { getRuntimeVersion } = await import("./runtime-version");

    await expect(getRuntimeVersion()).resolves.toBe("0.2.0");
  });
});
