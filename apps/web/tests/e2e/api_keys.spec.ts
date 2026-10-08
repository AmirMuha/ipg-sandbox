/**
 * API keys UI (007-api-key-auth).
 *
 * The engine has its own integration tests for the routes; these cover the browser
 * client, which is where the round-trip actually broke. All engine calls are mocked so
 * the suite needs a dev server but no engine or database.
 *
 * The middleware only checks that an `ipg_session` cookie exists, so a fake one is
 * enough to reach the page.
 */

import { test, expect, Page } from "@playwright/test";

const BASE_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const PAGE_URL = `${BASE_URL}/en/settings/api-keys`;

async function withSession(page: Page) {
  await page.context().addCookies([{ name: "ipg_session", value: "e2e-fake", url: BASE_URL }]);
}

const TOKEN = "ipg_key_e2e0000000000000000000000000000";
const ROW = {
  id: "key-1",
  name: "E2E Key",
  last_four: TOKEN.slice(-4),
  created_at: "2026-10-08T09:00:00+00:00",
  last_used_at: null,
};

test.describe("API keys", () => {
  test("empty state offers creation, table renders styled rows", async ({ page }) => {
    await withSession(page);
    await page.route("**/api/v1/auth/api-keys", (route) =>
      route.fulfill({ status: 200, json: { data: [] } })
    );

    await page.goto(PAGE_URL);

    await expect(page.getByText("You have no API keys yet.")).toBeVisible();
    await page.getByTestId("show-create-key-modal").click();
    await expect(page.getByTestId("create-key-modal")).toBeVisible();
  });

  test("creating a key reveals the token exactly once", async ({ page }) => {
    await withSession(page);

    let created = false;
    await page.route("**/api/v1/auth/api-keys", async (route) => {
      if (route.request().method() === "POST") {
        created = true;
        await route.fulfill({ status: 201, json: { data: { ...ROW, token: TOKEN } } });
      } else {
        await route.fulfill({ status: 200, json: { data: created ? [ROW] : [] } });
      }
    });

    await page.goto(PAGE_URL);
    await page.getByTestId("show-create-key-modal").click();
    await page.getByTestId("api-key-name-input").fill("E2E Key");
    await page.getByTestId("create-api-key-btn").click();

    // Full secret, shown once.
    await expect(page.getByTestId("api-key-token")).toHaveValue(TOKEN);

    // After dismissing, the list shows only the masked tail — never the secret.
    await page.getByTestId("api-key-done").click();
    await expect(page.getByTestId("api-key-row-key-1")).toBeVisible();
    await expect(page.getByText(TOKEN)).toHaveCount(0);
    await expect(page.getByText("••••0000")).toBeVisible();
  });

  test("the table lays out in columns rather than collapsing", async ({ page }) => {
    await withSession(page);
    await page.route("**/api/v1/auth/api-keys", (route) =>
      route.fulfill({ status: 200, json: { data: [ROW] } })
    );

    await page.goto(PAGE_URL);

    const headers = page.locator('[data-testid="api-keys-table"] thead th');
    await expect(headers).toHaveCount(5);

    // The bug this guards: unstyled cells sit flush against each other. Distinct x
    // positions mean the stylesheet's padding and table layout actually applied.
    const xs: number[] = [];
    for (let i = 0; i < 4; i++) {
      const box = await headers.nth(i).boundingBox();
      xs.push(box!.x);
    }
    for (let i = 1; i < xs.length; i++) {
      expect(xs[i], `header ${i} overlaps header ${i - 1}`).toBeGreaterThan(xs[i - 1] + 8);
    }
  });

  test("revoking a key confirms inline, then empties the list", async ({ page }) => {
    await withSession(page);

    let revoked = false;
    await page.route("**/api/v1/auth/api-keys", (route) =>
      route.fulfill({ status: 200, json: { data: revoked ? [] : [ROW] } })
    );
    await page.route("**/api/v1/auth/api-keys/key-1", async (route) => {
      if (route.request().method() === "DELETE") {
        revoked = true;
        await route.fulfill({ status: 204, body: "" });
      } else {
        await route.fallback();
      }
    });

    await page.goto(PAGE_URL);
    await expect(page.getByTestId("api-key-row-key-1")).toBeVisible();

    await page.getByTestId("revoke-key-key-1").click();
    await page.getByTestId("revoke-key-confirm-key-1").click();

    await expect(page.getByText("You have no API keys yet.")).toBeVisible();
  });
});
