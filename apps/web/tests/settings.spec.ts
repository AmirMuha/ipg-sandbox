import { test, expect } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";

test.describe("Gateways Page Gateway Status (006-admin-ipg-visibility)", () => {
  test("1. Merchant gateways lists only offered adapters, with no availability toggle", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/fa/gateways`);

    // On /gateways, cards have data-testid="adapter-card-<provider>"
    const cards = page.locator('[data-testid^="adapter-card-"]');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Verify that NO adapter toggle checkbox exists (FR-017)
    const toggles = page.locator('[data-testid^="adapter-toggle-"]');
    await expect(toggles).toHaveCount(0);

    // Providers the platform admin withdrew are not offered to the project, so they are
    // filtered out of this page rather than rendered locked. The previous version of this
    // test asserted they WERE visible, but guarded that behind `if (count > 0)` — so it
    // stayed green either way and never actually pinned the behaviour. This asserts it.
    await expect(page.locator('[data-testid^="adapter-withdrawn-badge-"]')).toHaveCount(0);
    await expect(page.locator('[data-testid^="adapter-withdrawn-notice-"]')).toHaveCount(0);

    // Credentials input and save button remain available (FR-018)
    const credsInput = page.locator('[data-testid^="credentials-input-"]').first();
    const saveBtn = page.locator('[data-testid^="save-credentials-btn-"]').first();
    await expect(credsInput).toBeVisible();
    await expect(saveBtn).toBeVisible();
  });
});
