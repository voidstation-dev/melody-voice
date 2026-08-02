import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    exclude: ["tests/e2e.spec.ts", "node_modules/**"],
  },
})
