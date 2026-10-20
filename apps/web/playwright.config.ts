import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 30_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.DASHBOARD_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    // The emulated checkout is a real page the shopper completes, so a click that
    // navigates has to be allowed to finish before the next assertion.
    actionTimeout: 30_000,
  },
});
