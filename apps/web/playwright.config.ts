import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  use: {
    baseURL: process.env.DASHBOARD_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
});
