/**
 * Shared helpers for the client-journey E2E suite.
 *
 * Everything here talks to the product the way a client would: the browser, the
 * public API, and a callback endpoint the suite owns. Nothing reads the database.
 */
import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8088";
export const DASHBOARD_URL = process.env.DASHBOARD_URL ?? "http://localhost:3088";
export const CALLBACK_PORT = Number(process.env.E2E_CALLBACK_PORT ?? 3099);
export const CALLBACK_URL = `http://127.0.0.1:${CALLBACK_PORT}/callback`;

/** The one gateway a fresh project ships enabled. */
export const PROVIDER = "zarinpal";
/** Zarinpal's seeded sandbox merchant id — the engine rejects anything else. */
export const MERCHANT_ID = "sandbox-merchant";

export type Merchant = {
  email: string;
  password: string;
  fullName: string;
};

/** A unique merchant per run, so a rerun never collides with the last one. */
export function newMerchant(): Merchant {
  const stamp = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  return {
    email: `e2e-${stamp}@example.com`,
    password: "Password123!",
    fullName: "E2E Merchant",
  };
}

/**
 * Create the merchant account through the public registration API, then sign in
 * through the interface.
 *
 * Registration itself needs an emailed one-time code, and this environment has no
 * mail service; the engine accepts a registration without a verification token, so
 * the account is created here and the *sign-in* is still exercised through the UI.
 */
export async function registerMerchant(
  request: APIRequestContext,
  merchant: Merchant
): Promise<void> {
  const res = await request.post(`${ENGINE_URL}/api/v1/auth/register`, {
    data: {
      email: merchant.email,
      password: merchant.password,
      full_name: merchant.fullName,
    },
  });
  expect(res.status(), "merchant registration should succeed").toBe(201);
}

/** Sign in through the real login form. */
export async function signIn(page: Page, merchant: Merchant): Promise<void> {
  await page.goto(`${DASHBOARD_URL}/en/login`);
  await page.locator("#email").fill(merchant.email);
  await page.locator("#password").fill(merchant.password);
  await page.getByRole("button", { name: "ورود به حساب" }).click();
  await page.waitForURL(/\/en\/console/, { timeout: 30_000 });
}

/** The session cookie value, for API calls the browser makes on the merchant's behalf. */
export async function sessionCookie(page: Page): Promise<string> {
  const cookies = await page.context().cookies();
  const session = cookies.find((c) => c.name === "ipg_session");
  expect(session, "the console should hold a session cookie").toBeTruthy();
  return `ipg_session=${session!.value}`;
}

/**
 * Create a payment from the console the way a merchant does, and return the
 * authority the gateway assigned it.
 */
export async function createPaymentViaConsole(
  page: Page,
  opts: { amountRial: number; reference?: string } = { amountRial: 1_000_000 }
): Promise<{ authority: string; amountRial: number }> {
  await page.goto(`${DASHBOARD_URL}/en/console`);
  await page.getByTestId("simulate-payment-btn").click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await page.getByTestId("simulate-amount").fill(String(opts.amountRial));
  if (opts.reference) {
    await page.getByTestId("simulate-reference").fill(opts.reference);
  }
  await page.getByTestId("simulate-next").click();

  // Step 2 is the emulated gateway's own page: the merchant's client would be
  // redirected here. The button settles the payment in one step.
  await expect(page.getByTestId("simulate-gateway-step")).toBeVisible();
  await page.getByTestId("simulate-submit").click();

  await expect(dialog).toBeHidden({ timeout: 30_000 });
  // The console refreshes after the mutation; the new row is the one we made.
  await expect(page.getByTestId("tx-row").first()).toBeVisible({ timeout: 30_000 });

  const row = page.getByTestId("tx-row").first();
  const authority = (await row.locator(".t-id").first().innerText()).trim();
  return { authority, amountRial: opts.amountRial };
}

/**
 * The merchant's backend verifies the payment. Verification is not a dashboard
 * action — it is the client's own call, so the suite makes it as the client.
 */
export async function verifyPayment(
  request: APIRequestContext,
  auth: { cookie?: string; bearer?: string },
  authority: string
): Promise<{ status: number; body: any }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth.cookie) headers["Cookie"] = auth.cookie;
  if (auth.bearer) headers["Authorization"] = `Bearer ${auth.bearer}`;

  const res = await request.post(`${ENGINE_URL}/zarinpal/payment/verification`, {
    headers,
    data: { authority },
  });
  let body: any = null;
  try {
    body = await res.json();
  } catch {
    body = null;
  }
  return { status: res.status(), body };
}

/** The engine's own view of a transaction, for assertions the UI cannot show. */
export async function fetchTransaction(
  request: APIRequestContext,
  auth: { cookie?: string; bearer?: string },
  id: string
): Promise<any> {
  const headers: Record<string, string> = {};
  if (auth.cookie) headers["Cookie"] = auth.cookie;
  if (auth.bearer) headers["Authorization"] = `Bearer ${auth.bearer}`;
  const res = await request.get(`${ENGINE_URL}/api/v1/transactions/${id}`, { headers });
  expect(res.status()).toBe(200);
  return res.json();
}
