import { test, expect } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";

const SUBSCRIPTION = (tier: string, status: string) =>
  JSON.stringify({
    tier,
    status,
    amount_toman: tier === "team" ? 199000 : 0,
    started_at: tier === "team" ? "2026-01-01T00:00:00Z" : null,
    expires_at: tier === "team" ? "2027-01-01T00:00:00Z" : null,
    entitlements: {
      daily_requests_limit: tier === "team" ? "unlimited" : 100,
      active_adapters_limit: tier === "team" ? "all" : 2,
      history_retention_days: tier === "team" ? 30 : 1,
    },
  });

test.describe("Pricing downgrade guard (007-plan-deactivation)", () => {
  test("team subscriber gets no upgrade CTA", async ({ page }) => {
    await page.route("**/api/v1/billing/subscription", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: SUBSCRIPTION("team", "active"),
      })
    );
    await page.goto(`${BASE_URL}/fa/pricing`);

    await expect(page.getByTestId("upgrade-active-team")).toBeVisible();
    await expect(page.getByTestId("upgrade-button")).toHaveCount(0);
  });

  test("free user still gets the upgrade CTA", async ({ page }) => {
    await page.route("**/api/v1/billing/subscription", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: SUBSCRIPTION("developer", "free"),
      })
    );
    await page.goto(`${BASE_URL}/fa/pricing`);

    await expect(page.getByTestId("upgrade-button")).toBeEnabled();
    await expect(page.getByTestId("upgrade-active-team")).toHaveCount(0);
  });
});
