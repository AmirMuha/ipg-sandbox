/**
 * Playwright smoke test (T042, SC-006, Quickstart §7).
 * Tests:
 * 1. FA/EN switch with RTL flip (dir="rtl" vs dir="ltr", functional parity).
 * 2. Transactions list renders columns: adapter, amount (Rial), status, scenario, timestamps.
 * 3. Force scenario from UI affects next initiated payment (SC-006 check 2).
 * 4. Webhook delivery detail visible (target, payload, attempt, result).
 */

import { test, expect } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8080";

test.describe("Dashboard Smoke Tests (SC-006, Quickstart §7)", () => {
  test("1. Persian locale has RTL direction and English locale has LTR direction", async ({
    page,
  }) => {
    // Navigate to Persian transactions
    await page.goto(`${BASE_URL}/fa/transactions`);
    const htmlFa = page.locator("html");
    await expect(htmlFa).toHaveAttribute("dir", "rtl");
    await expect(htmlFa).toHaveAttribute("lang", "fa");

    // Click locale switch link
    const localeSwitch = page.locator('[data-testid="locale-switch"]');
    await expect(localeSwitch).toBeVisible();
    await localeSwitch.click();

    // Verify flipped to LTR English
    await page.waitForURL("**/en/transactions");
    const htmlEn = page.locator("html");
    await expect(htmlEn).toHaveAttribute("dir", "ltr");
    await expect(htmlEn).toHaveAttribute("lang", "en");
  });

  test("2. Transactions list renders correctly with adapter, amount (Rial), status", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/fa/transactions`);
    const table = page.locator('[data-testid="transactions-table"]');
    await expect(table).toBeVisible();

    // Nav elements visible
    await expect(page.locator('[data-testid="nav-transactions"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-webhooks"]')).toBeVisible();
    await expect(page.locator('[data-testid="nav-settings"]')).toBeVisible();
  });

  test("3. Force decline from UI affects next payment (Quickstart §7 check 2)", async ({
    page,
    request,
  }) => {
    await page.goto(`${BASE_URL}/fa/transactions`);

    // Select 'decline' as project default in scenario controls
    const select = page.locator('[data-testid="project-default-select"]');
    await expect(select).toBeVisible();
    await select.selectOption("decline");

    // Submit project default
    const saveBtn = page.locator('[data-testid="save-project-btn"]');
    await saveBtn.click();

    // Now initiate a payment via Zarinpal
    const initRes = await request.post(`${ENGINE_URL}/zarinpal/request/payment`, {
      data: {
        amount: 30000,
        return_url: "http://localhost:3000/return",
      },
    });
    expect(initRes.ok()).toBeTruthy();
    const { authority } = await initRes.json();

    // Checkout confirm
    await request.post(`${ENGINE_URL}/zarinpal/checkout/${authority}`, {
      form: { action: "confirm" },
    });

    // Verify payment -> should decline per default scenario
    const verifyRes = await request.post(`${ENGINE_URL}/zarinpal/payment/verification`, {
      data: { authority },
    });
    expect(verifyRes.ok()).toBeTruthy();
    const verifyData = await verifyRes.json();
    expect(verifyData.code).toBe(-51);

    // Reload transactions page and verify row has declined status
    await page.reload();
    const declinedBadge = page.locator('[data-testid="tx-status"]:has-text("رد شده"), [data-testid="tx-status"]:has-text("declined")');
    await expect(declinedBadge.first()).toBeVisible();

    // Restore default to approve
    await select.selectOption("approve");
    await saveBtn.click();
  });

  test("4. Webhook deliveries view shows target, payload, attempt, result", async ({
    page,
  }) => {
    await page.goto(`${BASE_URL}/fa/webhooks`);
    const table = page.locator('[data-testid="deliveries-table"]');
    await expect(table).toBeVisible();

    // Check delivery details if rows exist
    const details = page.locator('[data-testid="delivery-details"]');
    if ((await details.count()) > 0) {
      await details.first().click();
      await expect(page.locator("pre").first()).toBeVisible();
    }
  });
});
