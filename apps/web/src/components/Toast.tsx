"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

export type ToastType = "success" | "danger" | "info" | "warning";

interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
  showToast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3200);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toasts pointer-events-none" aria-live="polite">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            // The design reveals a toast with a [data-show] transition. This
            // container mounts the toast already-visible and animates it in via
            // the `animate-toast` keyframe instead, so data-show is set on mount
            // rather than toggled — without it the toast would stay opacity:0.
            data-show="true"
            onClick={() => removeToast(toast.id)}
            className={`toast toast--${toast.type} animate-toast pointer-events-auto cursor-pointer`}
          >
            <ToastIcon type={toast.type} />
            <span className="toast__text">{toast.message}</span>
            <button
              type="button"
              className="muted"
              aria-label="Dismiss"
              onClick={(e) => {
                e.stopPropagation();
                removeToast(toast.id);
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastIcon({ type }: { type: ToastType }) {
  const common = { className: "ic", viewBox: "0 0 24 24", "aria-hidden": true } as const;
  if (type === "success")
    return (
      <svg {...common}>
        <path d="M20 6L9 17l-5-5" />
      </svg>
    );
  if (type === "danger")
    return (
      <svg {...common}>
        <path d="M18 6L6 18M6 6l12 12" />
      </svg>
    );
  if (type === "warning")
    return (
      <svg {...common}>
        <path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
        <path d="M12 9v4M12 17h.01" />
      </svg>
    );
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4M12 8h.01" />
    </svg>
  );
}
