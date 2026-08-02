import { describe, expect, it } from "vitest"

import { getBatchLimitError } from "./batch-limits"


describe("getBatchLimitError", () => {
  it("rejects a batch containing more than 50 files", () => {
    const files = Array.from({ length: 51 }, () => ({ text: "a" }))

    expect(getBatchLimitError(files)).toBe("BATCH_FILE_LIMIT_EXCEEDED")
  })

  it("rejects a batch containing more than 500000 characters", () => {
    const files = [{ text: "a".repeat(300_000) }, { text: "b".repeat(200_001) }]

    expect(getBatchLimitError(files)).toBe("BATCH_TEXT_LIMIT_EXCEEDED")
  })

  it("accepts a batch exactly on both limits", () => {
    const files = Array.from({ length: 50 }, () => ({ text: "a".repeat(10_000) }))

    expect(getBatchLimitError(files)).toBeNull()
  })
})
