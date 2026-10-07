"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { retryDelivery } from "../lib/api";

export function RetryButton({ deliveryId }: { deliveryId: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  // T073: hardcoded English under /fa/.
  const tCommon = useTranslations("common");

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
      className="btn btn--secondary btn--sm"
      data-testid={`retry-btn-${deliveryId}`}
    >
      {loading ? "..." : tCommon("retry")}
    </button>
  );
}
