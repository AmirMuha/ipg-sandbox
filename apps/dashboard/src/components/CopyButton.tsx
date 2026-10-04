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
      className="shrink-0 p-1 rounded-sm text-muted hover:text-text hover:bg-surface-subtle transition-colors duration-fast ease-standard"
      data-testid={testId}
    >
      <svg
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <rect x="9" y="9" width="13" height="13" rx="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </svg>
      <span className="sr-only">{copied ? "Copied" : label}</span>
    </button>
  );
}