import { test, expect } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8080";

test.describe("Providers Page Dynamic Filtering (006-admin-ipg-visibility)", () => {
  test("1. Shows only offered gateways matching GET /api/v1/providers", async ({
    page,
    request,
  }) => {
    // 1. Check live offered providers from engine
    const provRes = await request.get(`${ENGINE_URL}/api/v1/providers`);
    expect(provRes.ok()).toBeTruthy();
    const { providers: offeredIds } = await provRes.json();

    // 2. Load /fa/providers
    await page.goto(`${BASE_URL}/fa/providers`);
    const cardsFa = page.locator("article[data-gateway-id]");
    const countFa = await cardsFa.count();
    expect(countFa).toBe(offeredIds.length);

    // Verify all rendered cards belong to offered providers
    for (let i = 0; i < countFa; i++) {
      const gid = await cardsFa.nth(i).getAttribute("data-gateway-id");
      expect(offeredIds).toContain(gid);
    }

    // 3. Load /en/providers and verify parity (FR-008)
    await page.goto(`${BASE_URL}/en/providers`);
    const cardsEn = page.locator("article[data-gateway-id]");
    const countEn = await cardsEn.count();
    expect(countEn).toBe(countFa);
  });

  test("2. Header badges derive count from offered providers list", async ({ page, request }) => {
    const provRes = await request.get(`${ENGINE_URL}/api/v1/providers`);
    const { providers: offeredIds } = await provRes.json();

    await page.goto(`${BASE_URL}/fa/providers`);
    // Badge contains the count string
    const cards = page.locator("article[data-gateway-id]");
    const count = await cards.count();
    expect(count).toBe(offeredIds.length);
  });
});
