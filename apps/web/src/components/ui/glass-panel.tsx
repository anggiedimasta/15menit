import type { ReactNode } from "react";

import type { MapTheme } from "@/lib/mapStyles";
import { cn } from "@/lib/utils";

type GlassPanelProps = {
  children: ReactNode;
  className?: string;
  mapTheme?: MapTheme;
  "data-testid"?: string;
};

const MAP_THEME_CLASSES: Record<MapTheme, string> = {
  light: "border-black/10 bg-white/90 text-zinc-900 shadow-black/10",
  dark: "border-white/15 bg-zinc-900/90 text-zinc-50 shadow-black/30",
};

export function GlassPanel({
  children,
  className,
  mapTheme = "light",
  "data-testid": testId,
}: GlassPanelProps) {
  return (
    <div
      data-testid={testId}
      className={cn(
        "rounded-2xl border shadow-lg backdrop-blur-xl",
        MAP_THEME_CLASSES[mapTheme],
        className,
      )}
    >
      {children}
    </div>
  );
}
