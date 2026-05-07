"use client";

import { useApp } from "@/lib/context";
import { CloseIcon } from "./icons";

export function ToastViewport() {
  const { toasts, dismissToast, busy } = useApp();
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {busy && (
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-ink-900 px-4 py-3 text-sm text-feature shadow-lg">
          <span className="pulse dot bg-[var(--color-warning)]" />
          <span>{busy}…</span>
        </div>
      )}
      {toasts.map((toast) => {
        const tone =
          toast.tone === "error"
            ? "border-[color-mix(in_srgb,var(--color-danger)_30%,var(--color-border))] bg-[var(--color-danger-soft)] text-[var(--color-danger)]"
            : toast.tone === "success"
              ? "border-[color-mix(in_srgb,var(--color-success)_25%,var(--color-border))] bg-[var(--color-success-soft)] text-[var(--color-success)]"
              : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-ink-900)]";
        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg ${tone}`}
          >
            <span className="mt-0.5 flex-1 leading-relaxed">{toast.message}</span>
            <button
              type="button"
              aria-label="Dismiss"
              onClick={() => dismissToast(toast.id)}
              className="opacity-70 transition hover:opacity-100"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
