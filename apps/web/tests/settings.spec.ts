import { test, expect } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";

test.describe("Settings Page Gateway Status (006-admin-ipg-visibility)", () => {
  test("1. Merchant settings shows locked withdrawn state and no toggle", async ({ page }) => {
    await page.goto(`${BASE_URL}/fa/settings`);

    // In settings, cards have data-testid="adapter-card-<provider>"
    const cards = page.locator('[data-testid^="adapter-card-"]');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Verify that NO adapter toggle checkbox exists (FR-017)
    const toggles = page.locator('[data-testid^="adapter-toggle-"]');
    await expect(toggles).toHaveCount(0);

    // If an adapter is withdrawn (withdrawn_by_operator), it shows withdrawn badge & notice
    const withdrawnBadge = page.locator('[data-testid^="adapter-withdrawn-badge-"]');
    const count = await withdrawnBadge.count();
    if (count > 0) {
      await expect(withdrawnBadge.first()).toBeVisible();
      const notice = page.locator('[data-testid^="adapter-withdrawn-notice-"]').first();
      await expect(notice).toBeVisible();
    }

    // Credentials input and save button remain available (FR-018)
    const credsInput = page.locator('[data-testid^="credentials-input-"]').first();
    const saveBtn = page.locator('[data-testid^="save-credentials-btn-"]').first();
    await expect(credsInput).toBeVisible();
    await expect(saveBtn).toBeVisible();
  });
});
