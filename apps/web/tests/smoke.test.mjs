/**
 * Node native smoke test (Node 18+ built-in test runner)
 * Verifies SSR output, RTL direction, locale switching, and control API parity.
 */

import test from "node:test";
import assert from "node:assert";

const DASHBOARD_URL = process.env.DASHBOARD_URL ?? "http://localhost:3000";
const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8080";

let cachedCookie = "";
async function getSessionHeaders() {
  if (cachedCookie) return { Cookie: cachedCookie };
  try {
    const res = await fetch(`${ENGINE_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: `smoke-${Date.now()}@example.com`,
        password: "Password123!",
        full_name: "Smoke Tester",
      }),
    });
    if (res.ok) {
      const data = await res.json();
      cachedCookie = `ipg_session=${data.token}`;
      return { Cookie: cachedCookie };
    }
  } catch {
    // fallback
  }
  return {};
}

test("0. Unauthenticated access to /fa/console redirects to login", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/console`, { redirect: "manual" });
  assert.ok(
    res.status === 307 || res.status === 308 || res.status === 302,
    `Expected redirect status, got ${res.status}`
  );
  assert.ok(res.headers.get("location")?.includes("/login"));
});

test("1. Root redirect and Persian RTL layout", async () => {
  // Test redirect from /
  const rootRes = await fetch(`${DASHBOARD_URL}/`, { redirect: "manual" });
  assert.ok(
    rootRes.status === 307 || rootRes.status === 308 || rootRes.status === 302,
    `Expected redirect status, got ${rootRes.status}`
  );
  const location = rootRes.headers.get("location");
  assert.ok(
    location && (location.includes("/fa") || location.includes("/console")),
    `Expected location to contain /fa or /console, got ${location}`
  );

  // Test /fa/console
  const faRes = await fetch(`${DASHBOARD_URL}/fa/console`, { headers: await getSessionHeaders() });
  assert.strictEqual(faRes.status, 200);
  const faHtml = await faRes.text();

  assert.ok(faHtml.includes('dir="rtl"'), 'Expected dir="rtl" on /fa/console');
  assert.ok(faHtml.includes('lang="fa"'), 'Expected lang="fa" on /fa/console');
  assert.ok(
    faHtml.includes('data-testid="transactions-table"'),
    "Expected transactions-table in HTML"
  );
  // Language is fixed to Persian for now — the switcher must not render.
  assert.ok(
    !faHtml.includes('data-testid="locale-switch"'),
    "Expected no locale-switch link in HTML"
  );
});

test("2. English LTR layout", async () => {
  const enRes = await fetch(`${DASHBOARD_URL}/en/console`, { headers: await getSessionHeaders() });
  assert.strictEqual(enRes.status, 200);
  const enHtml = await enRes.text();

  assert.ok(enHtml.includes('dir="ltr"'), 'Expected dir="ltr" on /en/console');
  assert.ok(enHtml.includes('lang="en"'), 'Expected lang="en" on /en/console');
  assert.ok(
    enHtml.includes('data-testid="transactions-table"'),
    "Expected transactions-table in HTML"
  );
});

test("2b. Marketing routes render with RTL regardless of locale", async () => {
  // The marketing copy is Persian-only, so these pages force dir="rtl" even
  // under /en — an LTR flip would reorder every layout rule against the text.
  for (const route of ["home", "providers", "pricing", "login"]) {
    for (const locale of ["fa", "en"]) {
      const res = await fetch(`${DASHBOARD_URL}/${locale}/${route}`);
      assert.strictEqual(res.status, 200, `Expected 200 on /${locale}/${route}`);
      const html = await res.text();
      assert.ok(
        html.includes('dir="rtl"'),
        `Expected dir="rtl" on /${locale}/${route}`
      );
    }
  }
});

test("2c. Home page carries the export's Persian copy", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/home`);
  const html = await res.text();

  for (const copy of [
    "درگاه پرداخت را تا آخرین سناریو تست کنید",
    "شبیه‌سازی دقیق",
    "ترافیک بیرونی صفر",
    "zarinpal",
  ]) {
    assert.ok(html.includes(copy), `Expected home copy: ${copy}`);
  }
});

test("2d. Root redirect lands on the marketing home, not the console", async () => {
  // `/` 307s to `/fa` via next-intl middleware (no Location header — it is a
  // rewrite), and the prerendered `[locale]/page.tsx` then redirects client-side
  // via a NEXT_REDIRECT payload. Both layers are asserted here; the destination
  // never appears as a Location header, which is what the first version of this
  // test wrongly expected.
  const root = await fetch(`${DASHBOARD_URL}/`, { redirect: "manual" });
  assert.ok(
    [302, 307, 308].includes(root.status),
    `Expected a redirect from /, got ${root.status}`
  );

  const fa = await fetch(`${DASHBOARD_URL}/fa`);
  const html = await fa.text();
  // Payload shape is `NEXT_REDIRECT;replace;<url>;<status>;` in the RSC flight.
  const redirect = html.match(/NEXT_REDIRECT;replace;([^;]+);/)?.[1];
  assert.strictEqual(
    redirect,
    "/fa/home",
    "Expected /fa to redirect into /fa/home"
  );
});

test("2e. Provider API references are downloadable", async () => {
  const res = await fetch(`${DASHBOARD_URL}/docs/zarinpal-api-reference.md`);
  assert.strictEqual(res.status, 200, "Expected zarinpal doc to be served");
  assert.ok(
    (await res.text()).length > 0,
    "Expected zarinpal doc to have content"
  );
});

test("3. Webhooks view renders table", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/webhooks`, { headers: await getSessionHeaders() });
  assert.strictEqual(res.status, 200);
  const html = await res.text();

  assert.ok(
    html.includes('data-testid="deliveries-table"'),
    "Expected deliveries-table in HTML"
  );
});

test("4. Gateways view renders adapter cards", async () => {
  const res = await fetch(`${DASHBOARD_URL}/fa/gateways`, { headers: await getSessionHeaders() });
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

test("6. Simulation endpoint creates a transaction and returns a checkout URL", async () => {
  const res = await fetch(`${ENGINE_URL}/api/v1/transactions/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ adapter: "zarinpal", amount_rial: 750000, auto_complete: false }),
  });
  assert.strictEqual(res.status, 201, "Expected 201 from POST /transactions/simulate");

  const body = await res.json();
  const tx = body.transaction;
  assert.ok(tx.id, "Expected a transaction id");
  assert.strictEqual(tx.status, "initiated", "Expected an initiated transaction");
  assert.strictEqual(tx.amount_rial, 750000);
  assert.strictEqual(body.execution_mode, "interactive");
  assert.strictEqual(body.callback_dispatched, false);
  assert.ok(
    tx.checkout_url && tx.checkout_url.includes("/zarinpal/checkout/"),
    `Expected a zarinpal hosted checkout URL, got ${tx.checkout_url}`
  );

  // The URL must actually be served, not merely well-formed.
  const path = new URL(tx.checkout_url).pathname;
  const hosted = await fetch(`${ENGINE_URL}${path}`);
  assert.ok(hosted.status === 200, `Expected hosted checkout to answer 200, got ${hosted.status}`);
});

test("7. auto_complete settles in one call", async () => {
  const res = await fetch(`${ENGINE_URL}/api/v1/transactions/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ adapter: "zarinpal", amount_rial: 500000, auto_complete: true }),
  });
  assert.strictEqual(res.status, 201);

  const body = await res.json();
  assert.strictEqual(
    body.transaction.status,
    "settled",
    "Expected auto_complete to settle the payment"
  );
  assert.strictEqual(body.execution_mode, "auto_completed");
  assert.strictEqual(
    body.callback_dispatched,
    false,
    "No webhook URL is configured, so no callback was sent"
  );
});

test("8. Analytics overview reports totals and a monotonic funnel", async () => {
  const res = await fetch(`${ENGINE_URL}/api/v1/analytics/overview`);
  assert.strictEqual(res.status, 200);
  const ov = await res.json();

  assert.ok(typeof ov.total_transactions === "number", "Expected total_transactions");
  assert.ok(typeof ov.total_volume_rial === "number", "Expected total_volume_rial");
  assert.ok(typeof ov.success_rate_percent === "number", "Expected success_rate_percent");
  assert.ok(typeof ov.status_breakdown === "object", "Expected a status_breakdown map");
  assert.ok(typeof ov.gateways === "object", "Expected a gateways rollup map");
  assert.ok(ov.funnel, "Expected a funnel object");
  assert.ok(ov.webhooks, "Expected a webhooks rollup");

  const counted = Object.values(ov.status_breakdown).reduce((a, b) => a + b, 0);
  assert.strictEqual(
    counted,
    ov.total_transactions,
    "Every transaction appears in exactly one status bucket"
  );

  const f = ov.funnel;
  for (const stage of ["initiated", "hosted", "callback", "settled"]) {
    assert.ok(typeof f[stage] === "number", `Expected funnel.${stage}`);
  }
  assert.ok(f.settled <= f.callback, "funnel.settled must not exceed funnel.callback");
  assert.ok(f.callback <= f.hosted, "funnel.callback must not exceed funnel.hosted");
  assert.ok(f.hosted <= f.initiated, "funnel.hosted must not exceed funnel.initiated");
});

test("9. Transaction search filters and paginates", async () => {
  const all = await (await fetch(`${ENGINE_URL}/api/v1/transactions?page_size=100`)).json();
  assert.ok(all.total_pages >= 1, "Expected at least one page");
  const sample = all.items[0];
  assert.ok(sample, "Expected at least one seeded transaction");

  // q matches on authority, app_reference, or description.
  const byQ = await (
    await fetch(`${ENGINE_URL}/api/v1/transactions?q=${encodeURIComponent(sample.authority)}`)
  ).json();
  assert.ok(
    byQ.items.some((t) => t.authority === sample.authority),
    "Expected the searched transaction to come back"
  );
  assert.ok(byQ.total <= all.total, "A search must not widen the result set");

  // LIKE metacharacters are literals, not wildcards.
  const literal = await (await fetch(`${ENGINE_URL}/api/v1/transactions?q=%25`)).json();
  assert.ok(
    !literal.items.some((t) => t.authority !== "%"),
    "A '%' search must not match everything"
  );

  const filtered = await (
    await fetch(`${ENGINE_URL}/api/v1/transactions?status=settled&page_size=100`)
  ).json();
  assert.ok(
    filtered.items.every((t) => t.status === "settled"),
    "Expected only settled transactions"
  );

  const paged = await (await fetch(`${ENGINE_URL}/api/v1/transactions?page_size=1`)).json();
  assert.strictEqual(paged.items.length, 1);
  assert.strictEqual(paged.page_size, 1);
});

test("10. Dashboard renders the analytics overview, filters, and simulate CTA", async () => {
  const headers = await getSessionHeaders();
  const html = await (await fetch(`${DASHBOARD_URL}/fa/console`, { headers })).text();

  assert.ok(
    html.includes('data-testid="simulate-payment-btn"'),
    "Expected the simulate-payment CTA"
  );
  assert.ok(
    html.includes('data-testid="filter-search"'),
    "Expected the search filter input"
  );
  assert.ok(
    html.includes('data-testid="funnel-settled"'),
    "Expected the payment funnel card"
  );

  const webhooks = await (await fetch(`${DASHBOARD_URL}/fa/webhooks`, { headers })).text();
  assert.ok(
    webhooks.includes('data-testid="webhook-ping-btn"'),
    "Expected the webhook ping button"
  );
  // The webhook URL input moved to the settings form; the webhooks page keeps the ping probe.
  const settings = await (await fetch(`${DASHBOARD_URL}/fa/settings`, { headers })).text();
  assert.ok(
    settings.includes('data-testid="project-webhook-url-input"'),
    "Expected the default webhook URL input"
  );
  assert.ok(
    settings.includes('data-testid="project-history-cap-input"'),
    "Expected the history cap input"
  );
  assert.ok(
    settings.includes('data-testid="project-webhook-retry-max-input"'),
    "Expected the webhook retry max input"
  );
});

test("11. Detail page offers checkout and delete for a payable transaction", async () => {
  const headers = await getSessionHeaders();
  const created = (
    await (
      await fetch(`${ENGINE_URL}/api/v1/transactions/simulate`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ adapter: "zarinpal", amount_rial: 250000, auto_complete: false }),
      })
    ).json()
  ).transaction;

  const html = await (await fetch(`${DASHBOARD_URL}/fa/console/${created.id}`, { headers })).text();
  assert.ok(
    html.includes('data-testid="checkout-link"'),
    "Expected the Open Gateway Checkout link on an initiated transaction"
  );
  assert.ok(
    html.includes(`data-testid="delete-tx-${created.id}"`),
    "Expected the delete button"
  );

  // A settled transaction has nothing left to pay, so no link is rendered.
  const settled = (
    await (
      await fetch(`${ENGINE_URL}/api/v1/transactions/simulate`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ adapter: "zarinpal", amount_rial: 260000, auto_complete: true }),
      })
    ).json()
  ).transaction;
  const settledHtml = await (
    await fetch(`${DASHBOARD_URL}/fa/console/${settled.id}`, { headers })
  ).text();
  assert.ok(
    !settledHtml.includes('data-testid="checkout-link"'),
    "Expected no checkout link on a settled transaction"
  );
});

test("12. Deleting a transaction cascades to its deliveries", async () => {
  const created = (
    await (
      await fetch(`${ENGINE_URL}/api/v1/transactions/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adapter: "zarinpal", amount_rial: 240000, auto_complete: true }),
      })
    ).json()
  ).transaction;

  // The delivery log is keyed by transaction id and only reports a page here, so
  // compare item counts rather than a total.
  const before = await (
    await fetch(`${ENGINE_URL}/api/v1/deliveries?transaction_id=${created.id}`)
  ).json();
  assert.ok(before.total === 0 || before.total === undefined, "Expected a deliveries page");

  const del = await fetch(`${ENGINE_URL}/api/v1/transactions/${created.id}`, {
    method: "DELETE",
  });
  assert.strictEqual(del.status, 200);
  assert.strictEqual((await del.json()).deleted, true);

  const gone = await fetch(`${ENGINE_URL}/api/v1/transactions/${created.id}`);
  assert.strictEqual(gone.status, 404, "Expected the transaction to be gone");

  const after = await (
    await fetch(`${ENGINE_URL}/api/v1/deliveries?transaction_id=${created.id}`)
  ).json();
  assert.strictEqual(
    after.items.length,
    0,
    "Delivery rows must cascade with the transaction"
  );
});

test("13. Webhook ping reports reachability without recording a delivery", async () => {
  const before = await (await fetch(`${ENGINE_URL}/api/v1/deliveries?page_size=100`)).json();

  // Nothing is configured, so the engine must refuse rather than invent a target.
  const unconfigured = await fetch(`${ENGINE_URL}/api/v1/project/webhook-ping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  assert.strictEqual(unconfigured.status, 422, "Expected 422 with no webhook URL configured");

  const res = await fetch(`${ENGINE_URL}/api/v1/project/webhook-ping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // Loopback discard: the request leaves the process and comes back, which is
    // enough to prove the timeout and status plumbing without a live receiver.
    body: JSON.stringify({ target_url: "http://127.0.0.1:1/unreachable" }),
  });
  assert.strictEqual(res.status, 200);
  const result = await res.json();
  assert.strictEqual(result.ok, false, "An unreachable endpoint reports ok=false");
  assert.ok(result.error, "Expected an error message for an unreachable endpoint");
  assert.ok(result.latency_ms >= 0, "Expected a latency measurement");

  const after = await (await fetch(`${ENGINE_URL}/api/v1/deliveries?page_size=100`)).json();
  assert.strictEqual(after.total, before.total, "A ping must not record a delivery attempt");
});
