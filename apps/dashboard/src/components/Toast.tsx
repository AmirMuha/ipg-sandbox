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
      <div
        className="fixed bottom-6 end-6 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full px-4"
        aria-live="polite"
      >
        {toasts.map((toast) => {
          let colorClasses = "bg-surface border-border text-text";
          if (toast.type === "success") {
            colorClasses = "bg-success-bg border-success-border text-success-ink";
          } else if (toast.type === "danger") {
            colorClasses = "bg-danger-bg border-danger-border text-danger-ink";
          } else if (toast.type === "warning") {
            colorClasses = "bg-warning-bg border-warning-border text-warning-ink";
          }

          return (
            <div
              key={toast.id}
              onClick={() => removeToast(toast.id)}
              className={`pointer-events-auto p-3.5 rounded-md border shadow-raised text-xs font-medium flex items-center justify-between gap-3 animate-toast cursor-pointer transition-opacity ${colorClasses}`}
            >
              <span>{toast.message}</span>
              <button
                type="button"
                className="opacity-60 hover:opacity-100 text-xs px-1"
                onClick={(e) => {
                  e.stopPropagation();
                  removeToast(toast.id);
                }}
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
