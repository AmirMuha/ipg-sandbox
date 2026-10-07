"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Hero "first request" card from home.html.
 *
 * Three real endpoints rotating on a timer, crossfading line by line. The
 * rotation is ambient — it stops on hover and on keyboard focus, because
 * yanking content out from under someone who is reading it is worse than a
 * static card. The tabs are the real control.
 */

const PROVIDERS = [
  {
    id: "zarinpal",
    label: "زرین‌پال",
    comment: "# درخواست پرداخت زرین‌پال روی لوکال",
    lines: [
      {
        pre: "curl -X POST ",
        key: "http://localhost:8080/zarinpal/pg/v4/payment/request.json",
        post: " \\",
      },
      { pre: "  -H ", key: '"X-IPG-Scenario: approve"', post: " \\" },
      {
        pre: "  -d ",
        key: '\'{"merchant_id":"00000000-…","amount":2500000}\'',
        post: "",
      },
    ],
  },
  {
    id: "idpay",
    label: "آیدی‌پی",
    comment: "# درخواست پرداخت آیدی‌پی روی لوکال",
    lines: [
      {
        pre: "curl -X POST ",
        key: "http://localhost:8080/idpay/v1.1/payment",
        post: " \\",
      },
      { pre: "  -H ", key: '"X-API-KEY: sandbox-idpay-test-key-9941"', post: " \\" },
      {
        pre: "  -d ",
        key: '\'{"order_id":"9042","amount":2500000}\'',
        post: "",
      },
    ],
  },
  {
    id: "behpardakht",
    label: "به‌پرداخت",
    comment: "# درخواست پرداخت به‌پرداخت ملت روی لوکال",
    lines: [
      {
        pre: "curl -X POST ",
        key: "http://localhost:8080/behpardakht/services/pgw/InitializePay/InitializePay",
        post: " \\",
      },
      { pre: "  -H ", key: '"Content-Type: application/json"', post: " \\" },
      {
        pre: "  -d ",
        key: '\'{"TerminalID":847120,"OrderId":9042,"Amount":2500000}\'',
        post: "",
      },
    ],
  },
] as const;

const CYCLE_MS = 5200;

export function Quickstart() {
  const [index, setIndex] = useState(0);
  const [locked, setLocked] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    // ponytail: no progress bar animation state — the bar is CSS-driven off the
    // same cycle constant; drop it if the timing ever needs to diverge.
    if (locked || document.hidden) return;
    timer.current = setTimeout(() => {
      setIndex((i) => (i + 1) % PROVIDERS.length);
    }, CYCLE_MS);
    return () => clearTimeout(timer.current);
  }, [index, locked]);

  const provider = PROVIDERS[index];

  function pick(next: number) {
    setIndex(((next % PROVIDERS.length) + PROVIDERS.length) % PROVIDERS.length);
  }

  return (
    <div
      className="term"
      onMouseEnter={() => setLocked(true)}
      onMouseLeave={() => setLocked(false)}
      onFocus={() => setLocked(true)}
      onBlur={() => setLocked(false)}
    >
      <div className="term__bar">
        <span className="term__dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <div role="tablist" aria-label="انتخاب درگاه" className="flex gap-1">
          {PROVIDERS.map((p, i) => (
            <button
              key={p.id}
              role="tab"
              type="button"
              aria-selected={i === index}
              aria-controls="qs-panel"
              tabIndex={i === index ? 0 : -1}
              onClick={() => pick(i)}
              onKeyDown={(e) => {
                if (e.key === "ArrowLeft") {
                  e.preventDefault();
                  pick(index + 1);
                } else if (e.key === "ArrowRight") {
                  e.preventDefault();
                  pick(index - 1);
                }
              }}
              className="tab"
            >
              {p.label}
            </button>
          ))}
        </div>
        <span dir="ltr" className="term__file hidden sm:inline">
          POST localhost:8080
        </span>
      </div>

      <div
        id="qs-panel"
        role="tabpanel"
        dir="ltr"
        aria-live="off"
        key={provider.id}
        className="term__body mono text-xs leading-[1.9] animate-in"
      >
        <div className="t-comment">{provider.comment}</div>
        {provider.lines.map((line) => (
          // pre-wrap, not pre: the behpardakht URL is wider than the hero
          // column, and `pre` pushed it under the card edge at 1440px.
          <div key={line.pre + line.key} className="whitespace-pre-wrap break-all">
            {line.pre}
            <span className="t-str">{line.key}</span>
            {line.post}
          </div>
        ))}
      </div>

      {/* Hairline dwell indicator. Animation restarts from the React key change
          on the panel, so it tracks whichever provider is showing. */}
      {!locked && (
        <div className="h-px" aria-hidden="true">
          <span
            key={provider.id}
            className="grad-rule block origin-right"
            style={{
              animation: `qs-fill ${CYCLE_MS}ms linear forwards`,
            }}
          />
        </div>
      )}
    </div>
  );
}
