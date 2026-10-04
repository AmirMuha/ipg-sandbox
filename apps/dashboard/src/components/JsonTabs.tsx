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
    <div className="flex flex-col gap-2" data-testid="json-tabs">
      <div className="flex items-center gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActive(tab.key)}
            aria-pressed={active === tab.key}
            className={`px-2.5 py-1 rounded-sm text-xs font-medium transition-colors ${
              active === tab.key
                ? "bg-surface-elevated border border-border text-text"
                : "text-muted border border-transparent hover:text-text"
            }`}
            data-testid={`json-tab-${tab.key}`}
          >
            {fa ? tab.fa : tab.en}
          </button>
        ))}
        <button
          type="button"
          onClick={copy}
          className="ms-auto px-2.5 py-1 rounded-sm text-xs font-medium bg-surface-2 border border-border text-text-2 hover:text-text transition-colors"
          data-testid="json-copy"
        >
          {copied ? (fa ? "کپی شد!" : "Copied!") : fa ? "کپی" : "Copy"}
        </button>
      </div>
      <pre className="code-block" dir="ltr" data-testid={`json-panel-${active}`}>
        {text}
      </pre>
    </div>
  );
}