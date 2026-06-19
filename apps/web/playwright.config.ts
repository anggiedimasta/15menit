import { defineConfig, devices } from "@playwright/test";

const WEB_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: WEB_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    actionTimeout: 15_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"] },
    },
  ],
  webServer: process.env.CI
    ? undefined
    : [
        {
          command: "bun run dev",
          url: WEB_URL,
          reuseExistingServer: !process.env.PLAYWRIGHT_FRESH_SERVER,
          timeout: 120_000,
        },
        {
          command: "cd ../api && uvicorn app.main:app --port 8000",
          url: "http://localhost:8000/meta/city",
          reuseExistingServer: !process.env.PLAYWRIGHT_FRESH_SERVER,
          timeout: 120_000,
        },
      ],
});
