/**
 * Node native smoke test (Node 18+ built-in test runner)
 * Verifies SSR output, RTL direction, locale switching, and control API parity.
 */

import test from "node:test";
import assert from "node:assert";

const DASHBOARD_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8080";

test("1. Root redirect and Persian RTL layout", async () => {
  // Test redirect from /
  const rootRes = await fetch(`${DASHBOARD_URL}/`, { redirect: "manual" });
  assert.ok(
    rootRes.status === 307 || rootRes.status === 308 || rootRes.status === 302,
    `Expected redirect status, got ${rootRes.status}`
  );
  const location = rootRes.headers.get("location");
  assert.ok(
    location && (location.includes("/fa") || location.includes("/transactions")),
    `Expected location to contain /fa or /transactions, got ${location}`
  );

  // Test /fa/transactions
  const faRes = await fetch(`${DASHBOARD_URL}/fa/transactions`);
  assert.strictEqual(faRes.status, 200);
  const faHtml = await faRes.text();

  assert.ok(faHtml.includes('dir="rtl"'), 'Expected dir="rtl" on /fa/transactions');
  assert.ok(faHtml.includes('lang="fa"'), 'Expected lang="fa" on /fa/transactions');
  assert.ok(
    faHtml.includes('data-testid="transactions-table"'),
    "Expected transactions-table in HTML"
  );
  assert.ok(
    faHtml.includes('data-testid="locale-switch"'),
    "Expected locale-switch link in HTML"
  );
});

test("2. English LTR layout", async () => {
  const enRes = await fetch(`${DASHBOARD_URL}/en/transactions`);
  assert.strictEqual(enRes.status, 200);
  const enHtml = await enRes.text();

  assert.ok(enHtml.includes('dir="ltr"'), 'Expected dir="ltr" on /en/transactions');
  assert.ok(enHtml.includes('lang="en"'), 'Expected lang="en" on /en/transactions');
  assert.ok(
    enHtml.includes('data-testid="transactions-table"'),
    "Expected transactions-table in HTML"
  );
});

test("3. Webhooks view renders table", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/webhooks`);
  assert.strictEqual(res.status, 200);
  const html = await res.text();

  assert.ok(
    html.includes('data-testid="deliveries-table"'),
    "Expected deliveries-table in HTML"
  );
});

test("4. Settings view renders adapter cards", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/settings`);
  assert.strictEqual(res.status, 200);
  const html = await res.text();

  assert.ok(
    html.includes("data-testid=\"adapter-card-zarinpal\"") || html.includes("zarinpal"),
    "Expected Zarinpal adapter card in HTML"
  );
});

test("5. Force decline affects next payment (SC-006 check 2)", async () => {
  // 1. Force decline via project PATCH
  const patchRes = await fetch(`${ENGINE_URL}/api/v1/project`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ default_scenario: "decline" }),
  });
  assert.strictEqual(patchRes.status, 200);
  const project = await patchRes.json();
  assert.strictEqual(project.default_scenario, "decline");

  // 2. Initiate payment without explicit scenario header
  const initRes = await fetch(`${ENGINE_URL}/zarinpal/request/payment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      // T080: the engine validates credential values, not just their presence, so the
      // smoke test has to send the merchant it seeds.
      merchant_id: "sandbox-merchant",
      amount: 45000,
      return_url: "http://localhost:3000/return",
    }),
  });
  assert.strictEqual(initRes.status, 200);
  const initData = await initRes.json();
  assert.ok(initData.authority, "Expected authority");

  // 3. Checkout confirm
  await fetch(`${ENGINE_URL}/zarinpal/checkout/${initData.authority}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: "action=confirm",
    redirect: "manual",
  });

  // 4. Verify payment -> declines with code -51
  const verifyRes = await fetch(`${ENGINE_URL}/zarinpal/payment/verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ authority: initData.authority }),
  });
  assert.strictEqual(verifyRes.status, 200);
  const verifyData = await verifyRes.json();
  assert.strictEqual(verifyData.code, -51, "Expected -51 for decline outcome");

  // 5. Check transaction appears as declined
  const txRes = await fetch(`${ENGINE_URL}/api/v1/transactions`);
  assert.strictEqual(txRes.status, 200);
  const txList = await txRes.json();
  const matched = txList.items.find((t) => t.authority === initData.authority);
  assert.ok(matched, "Expected matched transaction");
  assert.strictEqual(matched.status, "declined");

  // Restore default
  await fetch(`${ENGINE_URL}/api/v1/project`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ default_scenario: "approve" }),
  });
});
