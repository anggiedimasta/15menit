import { useEffect, useState } from "react";

import { checkApiHealth } from "@/lib/api";

const DEFAULT_INTERVAL_MS = 30_000;

export function useApiHealth(intervalMs = DEFAULT_INTERVAL_MS) {
  const [isHealthy, setIsHealthy] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      const ok = await checkApiHealth();
      if (!cancelled) setIsHealthy(ok);
    };

    poll();
    const id = window.setInterval(poll, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [intervalMs]);

  return isHealthy;
}
