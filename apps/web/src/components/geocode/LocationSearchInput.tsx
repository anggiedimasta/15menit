import { MapPin } from "@phosphor-icons/react";
import { useEffect, useId, useState } from "react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";
import { useDebounce } from "@/hooks/useDebounce";
import { type GeocodeResult, searchGeocode } from "@/lib/api";
import type { MapTheme } from "@/lib/mapStyles";
import { fetchGeocodeCache } from "@/lib/supabase";
import { cn } from "@/lib/utils";

const PIN_COLORS = {
  green: "text-emerald-500",
  red: "text-red-500",
  indigo: "text-indigo-500",
} as const;

type PinColor = keyof typeof PIN_COLORS;

type LocationSearchInputProps = {
  label: string;
  placeholder?: string;
  value?: string;
  pinColor?: PinColor;
  variant?: "default" | "glass";
  mapTheme?: MapTheme;
  onSelect: (result: GeocodeResult) => void;
  "data-testid"?: string;
};

export function LocationSearchInput({
  label,
  placeholder,
  value = "",
  pinColor = "indigo",
  variant = "default",
  mapTheme = "light",
  onSelect,
  "data-testid": testId,
}: LocationSearchInputProps) {
  const inputId = useId();
  const [query, setQuery] = useState(value);
  const debounced = useDebounce(query, 300);
  const [results, setResults] = useState<GeocodeResult[]>([]);
  const [open, setOpen] = useState(false);
  const isGlass = variant === "glass";

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    if (debounced.length < 2) {
      setResults([]);
      return;
    }
    const queryKey = debounced.trim().toLowerCase();
    fetchGeocodeCache(queryKey)
      .then((cached) => {
        if (cached?.length) {
          setResults(cached);
          setOpen(true);
          return null;
        }
        return searchGeocode(debounced);
      })
      .then((items) => {
        if (items) {
          setResults(items);
          setOpen(items.length > 0);
        }
      })
      .catch((err: Error) => toast.error(err.message));
  }, [debounced]);

  return (
    <div className="relative min-w-0 flex-1" data-testid={testId}>
      <div className="flex items-center gap-2">
        <MapPin
          className={cn("size-4 shrink-0", PIN_COLORS[pinColor])}
          weight="fill"
          aria-hidden
        />
        <Input
          id={inputId}
          placeholder={placeholder ?? label}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => results.length > 0 && setOpen(true)}
          onBlur={() => {
            window.setTimeout(() => setOpen(false), 150);
          }}
          aria-label={label}
          aria-autocomplete="list"
          aria-expanded={open && results.length > 0}
          autoComplete="off"
          className={cn(
            "h-9 border-0 bg-transparent px-0 text-sm shadow-none focus-visible:ring-0",
            isGlass &&
              (mapTheme === "dark"
                ? "text-zinc-50 placeholder:text-zinc-400"
                : "text-zinc-900 placeholder:text-zinc-500"),
          )}
        />
      </div>
      {open && results.length > 0 && (
        <ul
          className={cn(
            "absolute z-50 mt-1 max-h-48 w-full overflow-auto rounded-xl border shadow-lg backdrop-blur-xl",
            isGlass
              ? mapTheme === "dark"
                ? "border-white/20 bg-zinc-900/95 text-zinc-50"
                : "border-zinc-200 bg-white/95 text-zinc-900"
              : "border bg-background",
          )}
        >
          {results.map((item) => (
            <li key={`${item.lat}-${item.lng}-${item.display_name}`}>
              <button
                type="button"
                className={cn(
                  "w-full px-3 py-2 text-left text-sm",
                  isGlass
                    ? mapTheme === "dark"
                      ? "hover:bg-white/10"
                      : "hover:bg-muted"
                    : "hover:bg-muted",
                )}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  onSelect(item);
                  setQuery(item.display_name);
                  setResults([]);
                  setOpen(false);
                }}
              >
                {item.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
