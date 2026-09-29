"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { retryDelivery } from "../lib/api";

export function RetryButton({ deliveryId }: { deliveryId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleRetry() {
    setLoading(true);
    try {
      await retryDelivery(deliveryId);
      router.refresh();
    } catch (err) {
      console.error("Retry failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleRetry}
      disabled={loading}
      className="text-xs bg-surface-2 border border-border hover:border-accent px-2.5 py-1 rounded transition-colors disabled:opacity-50"
      data-testid={`retry-btn-${deliveryId}`}
    >
      {loading ? "..." : "Retry"}
    </button>
  );
}
