import { createFileRoute } from "@tanstack/react-router";

import { App } from "@/components/HomePage";

export const Route = createFileRoute("/")({
  // Map + geocode UI are client-only; avoids hydration mismatch after HMR refactors.
  ssr: false,
  validateSearch: (search: Record<string, unknown>) => ({
    a: typeof search.a === "string" ? search.a : undefined,
    b: typeof search.b === "string" ? search.b : undefined,
    mode: typeof search.mode === "string" ? search.mode : undefined,
  }),
  component: App,
});
