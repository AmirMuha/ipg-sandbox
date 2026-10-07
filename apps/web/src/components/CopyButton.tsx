"use client";

import { useState } from "react";

/**
 * Clipboard copy for an authority / endpoint. `navigator.clipboard` is the only
 * mechanism worth having here: the value is always something the user just read off
 * this page and will paste into a terminal or a config file.
 */
export function CopyButton({
  value,
  label = "Copy",
  testId,
}: {
  value: string;
  label?: string;
  testId?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      // The label reverts on its own; no effect, no state to leak on unmount.
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard blocked (insecure origin, denied permission) — the value is
      // selectable text right next to this button, so failing silently is enough.
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      title={copied ? "Copied" : label}
      aria-label={copied ? "Copied" : label}
      className="copy shrink-0"
      data-copied={copied}
      data-testid={testId}
    >
      <svg className="ic" viewBox="0 0 24 24" aria-hidden="true">
        <rect x="9" y="9" width="13" height="13" rx="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </svg>
      <span className="sr-only">{copied ? "Copied" : label}</span>
    </button>
  );
}