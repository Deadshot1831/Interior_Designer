"use client";

import { STYLES, type Style } from "@/lib/types";

export function StylePicker({
  value,
  onChange,
}: {
  value: Style | null;
  onChange: (s: Style) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {STYLES.map((s) => {
        const selected = value === s.value;
        return (
          <button
            key={s.value}
            type="button"
            onClick={() => onChange(s.value)}
            className={`flex items-center gap-2 rounded-lg border p-2.5 text-left text-sm transition ${
              selected
                ? "border-brand ring-2 ring-brand/30"
                : "border-black/10 hover:border-black/30"
            }`}
            aria-pressed={selected}
          >
            <span
              className="h-6 w-6 shrink-0 rounded-full border border-black/10"
              style={{ backgroundColor: s.swatch }}
            />
            <span className="font-medium">{s.label}</span>
          </button>
        );
      })}
    </div>
  );
}
