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

const EMPTY_LIST = { data: [] };

async function withSession(page: Page) {
  await page.context().addCookies([
    { name: "ipg_session", value: "e2e-fake", url: BASE_URL },
  ]);
}

test.describe("API keys", () => {
  test("empty state offers creation", async ({ page }) => {
    await withSession(page);
    await page.route("**/api/v1/auth/api-keys", (route) =>
      route.fulfill({ status: 200, json: EMPTY_LIST })
    );

    await page.goto(PAGE_URL);

    await expect(page.getByText("You don't have any active API keys")).toBeVisible();
    await page.getByTestId("show-create-key-modal").click();
    await expect(page.getByText("Create New API Key")).toBeVisible();
  });

  test("creating a key reveals the token exactly once", async ({ page }) => {
    await withSession(page);

    const TOKEN = "ipg_key_e2e0000000000000000000000000000";
    const row = {
      id: "key-1",
      name: "E2E Key",
      last_four: TOKEN.slice(-4),
      created_at: new Date().toISOString(),
      last_used_at: null,
    };

    let created = false;
    await page.route("**/api/v1/auth/api-keys", async (route) => {
      if (route.request().method() === "POST") {
        created = true;
        await route.fulfill({ status: 201, json: { data: { ...row, token: TOKEN } } });
      } else {
        await route.fulfill({ status: 200, json: { data: created ? [row] : [] } });
      }
    });

    await page.goto(PAGE_URL);
    await page.getByTestId("show-create-key-modal").click();
    await page.getByTestId("api-key-name-input").fill("E2E Key");
    await page.getByTestId("create-api-key-btn").click();

    // Full secret shown once.
    await expect(page.getByText(TOKEN)).toBeVisible();

    // After dismissing, the list shows only metadata — never the secret.
    await page.getByRole("button", { name: "Done" }).click();
    await expect(page.getByTestId("api-key-row-key-1")).toBeVisible();
    await expect(page.getByText(TOKEN)).toHaveCount(0);
  });

  test("revoking a key empties the list", async ({ page }) => {
    await withSession(page);

    const row = {
      id: "key-2",
      name: "Doomed Key",
      last_four: "4321",
      created_at: new Date().toISOString(),
      last_used_at: null,
    };

    let revoked = false;
    await page.route("**/api/v1/auth/api-keys", (route) =>
      route.fulfill({ status: 200, json: { data: revoked ? [] : [row] } })
    );
    await page.route("**/api/v1/auth/api-keys/key-2", async (route) => {
      if (route.request().method() === "DELETE") {
        revoked = true;
        await route.fulfill({ status: 204, body: "" });
      } else {
        await route.fallback();
      }
    });

    page.on("dialog", (dialog) => void dialog.accept());

    await page.goto(PAGE_URL);
    await expect(page.getByTestId("api-key-row-key-2")).toBeVisible();

    await page.getByTestId("revoke-key-key-2").click();

    await expect(page.getByText("You don't have any active API keys")).toBeVisible();
  });
});
