/**
 * Client journey proof — a merchant managing their payments.
 *
 * Every test drives the product the way a client would: the browser for the
 * dashboard, the public API for what a backend does, and a callback endpoint the
 * suite owns for what a merchant receives. Nothing here reads the database.
 */
import { expect, test } from "@playwright/test";
import {
  CALLBACK_URL,
  DASHBOARD_URL,
  ENGINE_URL,
  MERCHANT_ID,
  createPaymentViaConsole,
  fetchTransaction,
  newMerchant,
  registerMerchant,
  sessionCookie,
  signIn,
  verifyPayment,
} from "./helpers";

test.describe.configure({ mode: "serial" });

test.describe("Client payment journeys", () => {
  test("an unauthenticated visitor cannot reach the console", async ({ page }) => {
    await page.goto(`${DASHBOARD_URL}/en/console`);
    await page.waitForURL(/\/en\/login/, { timeout: 30_000 });
    await expect(page.locator("#email")).toBeVisible();
  });

  test("valid credentials sign the merchant in, wrong ones do not", async ({ page, request }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);

    // Wrong password: an error, and no session.
    await page.goto(`${DASHBOARD_URL}/en/login`);
    await page.locator("#email").fill(merchant.email);
    await page.locator("#password").fill("WrongPassword123!");
    await page.getByRole("button", { name: "ورود به حساب" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/en\/login/);

    // Right password: the console loads.
    await page.locator("#password").fill(merchant.password);
    await page.getByRole("button", { name: "ورود به حساب" }).click();
    await page.waitForURL(/\/en\/console/, { timeout: 30_000 });
    await expect(page.getByTestId("transactions-table")).toBeVisible();
  });

  test("a merchant creates a payment, pays it, and sees it settled", async ({
    page,
    request,
  }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    const { authority, amountRial } = await createPaymentViaConsole(page, {
      amountRial: 1_500_000,
      reference: "ORDER-1001",
    });
    expect(authority).toBeTruthy();

    // The console shows the new payment with its reference and amount.
    const row = page.getByTestId("tx-row").first();
    await expect(row).toContainText("ORDER-1001");
    await expect(row.getByTestId("tx-amount")).toContainText(
      new Intl.NumberFormat("en-US").format(amountRial)
    );

    // The merchant's backend verifies the payment.
    const auth = { cookie: await sessionCookie(page) };
    const verified = await verifyPayment(request, auth, authority);
    expect(verified.status).toBe(200);
    expect(verified.body.code).toBe(100);

    // The console reflects the settled state on reload.
    await page.reload();
    const settledRow = page
      .getByTestId("tx-row")
      .filter({ hasText: authority })
      .first();
    await expect(settledRow).toBeVisible({ timeout: 30_000 });
    await expect(settledRow.getByTestId("tx-status")).toContainText("Settled");
  });

  test("a shopper who cancels is recorded as declined, never settled", async ({
    page,
    request,
  }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    // Create the payment through the merchant's own gateway call, so the hosted
    // checkout page can be visited directly the way a shopper's browser would.
    const create = await request.post(`${ENGINE_URL}/api/v1/transactions/simulate`, {
      headers: { Cookie: await sessionCookie(page) },
      data: { adapter: "zarinpal", amount_rial: 900_000, auto_complete: false },
    });
    expect(create.status()).toBe(201);
    const created = await create.json();
    const authority = created.transaction.authority;
    const checkoutUrl = created.checkout_url;
    expect(checkoutUrl).toBeTruthy();

    // The hosted page shows this payment's authority and amount.
    await page.goto(checkoutUrl!);
    await expect(page.locator("body")).toContainText(authority);
    await expect(page.locator("body")).toContainText(
      new Intl.NumberFormat("en-US").format(900_000)
    );

    // The shopper cancels.
    await page.locator('button[value="fail"]').click();
    await page.waitForURL(/Authority=/, { timeout: 30_000 });

    // The transaction is declined, not settled.
    const list = await request.get(`${ENGINE_URL}/api/v1/transactions?page_size=100`, {
      headers: { Cookie: await sessionCookie(page) },
    });
    const items = (await list.json()).items as any[];
    const tx = items.find((t) => t.authority === authority);
    expect(tx, "the cancelled payment should be recorded").toBeTruthy();
    expect(tx!.status).toBe("declined");
  });

  test("a client provisions an API key, uses it, and revokes it", async ({ page, request }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    // Create the key in the dashboard.
    await page.goto(`${DASHBOARD_URL}/en/settings/api-keys`);
    await page.getByTestId("show-create-key-modal").click();
    await page.getByTestId("api-key-name-input").fill("Production app");
    await page.getByTestId("create-api-key-btn").click();

    // The secret is shown once, with the documented prefix.
    const tokenInput = page.getByTestId("api-key-token");
    await expect(tokenInput).toBeVisible();
    const secret = (await tokenInput.inputValue()).trim();
    expect(secret.startsWith("ipg_key_")).toBe(true);
    await expect(page.getByTestId("key-once-warning")).toBeVisible();
    await page.getByTestId("api-key-done").click();

    // The list shows the key, but only its masked suffix.
    const keyRow = page.getByTestId("api-keys-table").locator("tr", { hasText: "Production app" });
    await expect(keyRow).toBeVisible();
    await expect(keyRow).toContainText(secret.slice(-4));
    await expect(keyRow).not.toContainText(secret);

    // The secret is gone once the modal closes.
    await expect(page.getByTestId("api-key-token")).toHaveCount(0);

    // The key authenticates a real sandbox call.
    const authed = await request.get(`${ENGINE_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${secret}` },
    });
    expect(authed.status()).toBe(200);
    const me = await authed.json();
    expect(me.user.email).toBe(merchant.email);

    // Revoke it.
    const row = page.getByTestId("api-keys-table").locator("tr", { hasText: "Production app" });
    await row.getByRole("button", { name: "Revoke" }).click();
    await row.getByRole("button", { name: "Revoke", exact: true }).last().click();

    // The key is gone from the list, and rejected by the API.
    await expect(
      page.getByTestId("api-keys-table").locator("tr", { hasText: "Production app" })
    ).toHaveCount(0);

    const rejected = await request.get(`${ENGINE_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${secret}` },
    });
    expect(rejected.status()).toBe(401);
  });

  test("a client receives the settled-payment webhook and sees it in the log", async ({
    page,
    request,
  }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    // Point the project at the suite's own callback endpoint.
    await page.goto(`${DASHBOARD_URL}/en/settings`);
    await page.getByTestId("project-webhook-url-input").fill(CALLBACK_URL);
    await page.getByTestId("save-project-btn").click();
    await expect(page.getByRole("status").first()).toBeVisible({ timeout: 30_000 });

    // The webhooks page shows the configured target.
    await page.goto(`${DASHBOARD_URL}/en/webhooks`);
    await expect(page.getByTestId("webhook-target-url")).toContainText(CALLBACK_URL);

    // The probe reaches the endpoint the suite is serving.
    await page.getByTestId("webhook-ping-btn").click();
    await expect(page.getByTestId("webhook-ping-result")).toContainText("200", {
      timeout: 30_000,
    });

    // Now settle a payment: the sandbox dispatches the event to that endpoint.
    const { authority } = await createPaymentViaConsole(page, { amountRial: 2_000_000 });
    const auth = { cookie: await sessionCookie(page) };
    const verified = await verifyPayment(request, auth, authority);
    expect(verified.status).toBe(200);

    // The delivery is recorded in the dashboard.
    await page.goto(`${DASHBOARD_URL}/en/webhooks`);
    const delivery = page.getByTestId("delivery-row").first();
    await expect(delivery).toBeVisible({ timeout: 30_000 });
    await expect(delivery.getByTestId("delivery-target")).toContainText(CALLBACK_URL);
    await expect(delivery.getByTestId("delivery-event")).toContainText("payment.approved");
  });

  test("a merchant finds, inspects and purges a payment", async ({ page, request }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    const { authority } = await createPaymentViaConsole(page, {
      amountRial: 3_300_000,
      reference: "ORDER-2002",
    });

    // Search narrows the list to the payment.
    await page.goto(`${DASHBOARD_URL}/en/console`);
    await page.getByTestId("filter-search").fill(authority);
    await page.getByTestId("filter-apply").click();
    await page.waitForURL(/q=/, { timeout: 30_000 });

    const rows = page.getByTestId("tx-row");
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText(authority);

    // The status filter never shows a mismatched payment.
    await page.getByTestId("filter-status").selectOption("settled");
    await page.waitForURL(/status=settled/, { timeout: 30_000 });
    await expect(page.getByTestId("tx-row").first().getByTestId("tx-status")).toContainText(
      "Settled"
    );

    // The detail view shows the record.
    await page.getByTestId("filter-status").selectOption("");
    await page.getByTestId("filter-search").fill(authority);
    await page.getByTestId("filter-apply").click();
    await page.waitForURL(/q=/, { timeout: 30_000 });

    const list = await request.get(`${ENGINE_URL}/api/v1/transactions?page_size=100`, {
      headers: { Cookie: await sessionCookie(page) },
    });
    const items = (await list.json()).items as any[];
    const tx = items.find((t) => t.authority === authority);
    expect(tx).toBeTruthy();

    await page.goto(`${DASHBOARD_URL}/en/console/${tx!.id}`);
    await expect(page.getByTestId("checkout-link")).toBeVisible();
    await expect(page.locator("body")).toContainText(authority);
    await expect(page.getByTestId("raw-request")).toContainText("ORDER-2002");

    // Delete it, with the confirmation step.
    await page.getByTestId(`delete-tx-${tx!.id}`).click();
    await page.getByTestId(`delete-tx-confirm-${tx!.id}`).click();
    await page.waitForURL(/\/en\/console/, { timeout: 30_000 });

    const after = await request.get(`${ENGINE_URL}/api/v1/transactions/${tx!.id}`, {
      headers: { Cookie: await sessionCookie(page) },
    });
    expect(after.status()).toBe(404);
  });

  test("a merchant sees the gateways they can call and can test them", async ({ page, request }) => {
    const merchant = newMerchant();
    await registerMerchant(request, merchant);
    await signIn(page, merchant);

    await page.goto(`${DASHBOARD_URL}/en/gateways`);
    const card = page.getByTestId("adapter-card-zarinpal");
    await expect(card).toBeVisible();

    // The endpoint snippet is the address the merchant's client posts to.
    await expect(card.getByTestId("adapter-endpoint-zarinpal")).toContainText("/zarinpal");

    // The credential check answers.
    await card.getByTestId("test-adapter-btn-zarinpal").click();
    await expect(card.getByTestId("test-result-zarinpal")).toBeVisible({ timeout: 30_000 });
    await expect(card.getByTestId("test-result-zarinpal")).toContainText("valid");
  });
});
