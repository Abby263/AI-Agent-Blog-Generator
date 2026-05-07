"use client";

import { useApp } from "@/lib/context";
import type { ThemePreference } from "@/lib/context";
import { MonitorIcon, MoonIcon, SunIcon } from "./icons";

const ORDER: ThemePreference[] = ["light", "dark", "system"];

const META: Record<
  ThemePreference,
  { label: string; icon: typeof SunIcon; nextHint: string }
> = {
  light: { label: "Light", icon: SunIcon, nextHint: "Switch to dark" },
  dark: { label: "Dark", icon: MoonIcon, nextHint: "Switch to system" },
  system: { label: "System", icon: MonitorIcon, nextHint: "Switch to light" },
};

export function ThemeToggle({ compact = true }: { compact?: boolean }) {
  const { themePreference, setThemePreference } = useApp();
  const current = META[themePreference];
  const Icon = current.icon;

  function cycle() {
    const idx = ORDER.indexOf(themePreference);
    const next = ORDER[(idx + 1) % ORDER.length];
    setThemePreference(next);
  }

  if (compact) {
    return (
      <button
        type="button"
        onClick={cycle}
        aria-label={`Theme: ${current.label}. ${current.nextHint}`}
        title={`Theme: ${current.label}. ${current.nextHint}.`}
        className="btn btn-ghost btn-sm"
      >
        <Icon className="h-4 w-4" />
        <span className="sr-only">{current.label}</span>
      </button>
    );
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex rounded-lg border border-border bg-canvas p-1"
    >
      {ORDER.map((option) => {
        const OptionIcon = META[option].icon;
        const active = themePreference === option;
        return (
          <button
            key={option}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => setThemePreference(option)}
            className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition ${
              active
                ? "bg-surface text-ink-900 shadow-sm"
                : "text-ink-500 hover:text-ink-800"
            }`}
          >
            <OptionIcon className="h-3.5 w-3.5" />
            {META[option].label}
          </button>
        );
      })}
    </div>
  );
}
