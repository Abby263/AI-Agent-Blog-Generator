"use client";

import type { ReactNode, HTMLAttributes, ButtonHTMLAttributes } from "react";

type Variant = "primary" | "accent" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "md" | "sm";
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
};

const variantClass: Record<Variant, string> = {
  primary: "btn-primary",
  accent: "btn-accent",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
};

export function Button({
  variant = "secondary",
  size = "md",
  leadingIcon,
  trailingIcon,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      className={[
        "btn",
        variantClass[variant],
        size === "sm" ? "btn-sm" : "",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {leadingIcon}
      {children}
      {trailingIcon}
    </button>
  );
}

export function Card({
  className,
  children,
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div {...rest} className={`surface p-5 md:p-6 ${className ?? ""}`}>
      {children}
    </div>
  );
}

export function CardHeader({
  eyebrow,
  title,
  description,
  trailing,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  trailing?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        {eyebrow && (
          <p className="eyebrow eyebrow-accent mb-1.5">{eyebrow}</p>
        )}
        <h2 className="text-xl md:text-2xl font-medium tracking-tight">
          {title}
        </h2>
        {description && (
          <p className="mt-1.5 max-w-prose text-sm text-[var(--color-ink-500)]">
            {description}
          </p>
        )}
      </div>
      {trailing && (
        <div className="flex flex-wrap items-center gap-2">{trailing}</div>
      )}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  trailing,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  trailing?: ReactNode;
}) {
  return (
    <header className="mb-8 flex flex-col gap-4 border-b border-[var(--color-border)] pb-6 md:flex-row md:items-end md:justify-between">
      <div className="max-w-2xl">
        {eyebrow && (
          <p className="eyebrow eyebrow-accent mb-2">{eyebrow}</p>
        )}
        <h1 className="text-3xl font-medium tracking-tight md:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-base text-[var(--color-ink-500)]">
            {description}
          </p>
        )}
      </div>
      {trailing && (
        <div className="flex flex-wrap items-center gap-2">{trailing}</div>
      )}
    </header>
  );
}

export function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="font-medium text-[var(--color-ink-800)]">
          {label}
          {required && <span className="ml-1 text-[var(--color-accent)]">*</span>}
        </span>
        {hint && (
          <span className="text-xs text-[var(--color-ink-400)]">{hint}</span>
        )}
      </div>
      {children}
    </label>
  );
}

export function Toggle({
  label,
  description,
  checked,
  disabled = false,
  onChange,
}: {
  label: string;
  description?: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label
      className={`flex items-start gap-3 rounded-[10px] border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-3 text-sm transition hover:border-[var(--color-border-strong)] ${
        disabled ? "opacity-60" : "cursor-pointer"
      }`}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`mt-0.5 inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full border transition ${
          checked
            ? "border-[var(--color-ink-900)] bg-[var(--color-ink-900)]"
            : "border-[var(--color-border-strong)] bg-[var(--color-surface-2)]"
        }`}
      >
        <span
          className={`h-3.5 w-3.5 transform rounded-full bg-white shadow transition ${
            checked ? "translate-x-[18px]" : "translate-x-[3px]"
          }`}
        />
      </button>
      <span className="flex-1">
        <span className="block font-medium text-[var(--color-ink-800)]">
          {label}
        </span>
        {description && (
          <span className="mt-0.5 block text-xs text-[var(--color-ink-500)]">
            {description}
          </span>
        )}
      </span>
    </label>
  );
}

export function Badge({
  tone = "neutral",
  children,
  withDot = false,
}: {
  tone?: "neutral" | "success" | "info" | "warn" | "danger" | "accent";
  children: ReactNode;
  withDot?: boolean;
}) {
  const cls =
    tone === "success"
      ? "badge-success"
      : tone === "info"
        ? "badge-info"
        : tone === "warn"
          ? "badge-warn"
          : tone === "danger"
            ? "badge-danger"
            : tone === "accent"
              ? "badge-accent"
              : "badge-neutral";
  return (
    <span className={`badge ${cls}`}>
      {withDot && <span className="dot" />}
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status?: string }) {
  if (!status) return <Badge tone="neutral">unknown</Badge>;
  const lower = status.toLowerCase();
  if (lower.includes("complete") || lower === "approved") {
    return <Badge tone="success" withDot>{status}</Badge>;
  }
  if (lower.includes("fail") || lower === "rejected") {
    return <Badge tone="danger" withDot>{status}</Badge>;
  }
  if (lower.includes("running") || lower.includes("pending") || lower.includes("queued") || lower.includes("progress")) {
    return <Badge tone="info" withDot>{status}</Badge>;
  }
  if (lower.includes("change") || lower.includes("notes") || lower.includes("review")) {
    return <Badge tone="warn" withDot>{status}</Badge>;
  }
  return <Badge tone="neutral" withDot>{status}</Badge>;
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-[var(--color-border-strong)] bg-[var(--color-canvas)] px-6 py-10 text-center">
      <p className="text-sm font-medium text-[var(--color-ink-700)]">{title}</p>
      {description && (
        <p className="mt-1 max-w-md text-sm text-[var(--color-ink-500)]">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function MetricTile({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "neutral" | "dark" | "accent";
}) {
  const base =
    tone === "dark"
      ? "surface-dark p-5"
      : tone === "accent"
        ? "surface p-5 border-[var(--color-accent-soft)]"
        : "surface p-5";
  const labelTone =
    tone === "dark"
      ? "text-[#d8cfb6]"
      : "text-[var(--color-ink-500)]";
  const hintTone =
    tone === "dark"
      ? "text-feature-muted"
      : "text-[var(--color-ink-400)]";
  return (
    <div className={base}>
      <p className={`text-[11px] font-medium uppercase tracking-[0.14em] ${labelTone}`}>
        {label}
      </p>
      <p className="mt-2 truncate font-display text-2xl font-medium tracking-tight">
        {value}
      </p>
      {hint && (
        <p className={`mt-1 line-clamp-2 text-xs ${hintTone}`}>{hint}</p>
      )}
    </div>
  );
}

export function KeyValue({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <span className="text-sm text-[var(--color-ink-500)]">{label}</span>
      <span className="text-sm font-medium text-[var(--color-ink-800)] truncate">
        {children}
      </span>
    </div>
  );
}

export function HelpText({ children }: { children: ReactNode }) {
  return (
    <p className="text-xs leading-relaxed text-[var(--color-ink-500)]">{children}</p>
  );
}
