import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration.
 *
 * BASE_URL points at a running frontend (default http://localhost:3000).
 * The Phase-1 release-gate journey (login → load → … → payment) is added
 * incrementally as the business modules land; Phase 0 ships a smoke test only.
 */
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
});
