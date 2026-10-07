"use client";

import { useState } from "react";

const TABS = [
  { key: "request", en: "Request", fa: "درخواست" },
  { key: "callback", en: "Callback", fa: "پاسخ درگاه/کال‌بک" },
  { key: "verify", en: "Verify", fa: "اعتبارسنجی" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export function JsonTabs({
  rawRequest,
  callbackPayload,
  rawResponse,
  locale = "fa",
}: {
  rawRequest?: Record<string, unknown>;
  callbackPayload?: Record<string, unknown>;
  rawResponse?: Record<string, unknown>;
  locale?: string;
}) {
  const fa = locale !== "en";
  const data: Record<TabKey, Record<string, unknown> | undefined> = {
    request: rawRequest,
    callback: callbackPayload,
    verify: rawResponse,
  };
  const [active, setActive] = useState<TabKey>("request");
  const [copied, setCopied] = useState(false);

  const text = JSON.stringify(data[active] ?? {}, null, 2);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Clipboard blocked (insecure origin / permission denied) — nothing to do but skip the flash.
    }
  }

  return (
    <div className="stack-sm" data-testid="json-tabs">
      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            onClick={() => setActive(tab.key)}
            aria-selected={active === tab.key}
            className="tab"
            data-testid={`json-tab-${tab.key}`}
          >
            {fa ? tab.fa : tab.en}
          </button>
        ))}
      </div>

      {/* The payload is a plain JSON.stringify today, so the body stays plain text — no
          syntax-highlight spans in here until something actually tokenises it. */}
      <div className="term">
        <div className="term__bar">
          <span className="term__dots" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span className="term__file">{active}.json</span>
          <button
            type="button"
            onClick={copy}
            className="copy"
            data-copied={copied}
            data-testid="json-copy"
          >
            <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            {copied ? (fa ? "کپی شد!" : "Copied!") : fa ? "کپی" : "Copy"}
          </button>
        </div>
        <div className="term__body">
          <pre dir="ltr" data-testid={`json-panel-${active}`}>
            {text}
          </pre>
        </div>
      </div>
    </div>
  );
}
