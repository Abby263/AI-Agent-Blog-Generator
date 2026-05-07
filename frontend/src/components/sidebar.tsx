"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useApp } from "@/lib/context";
import { GITHUB_REPOSITORY_URL } from "@/lib/api";
import { ThemeToggle } from "./theme-toggle";
import {
  ComposeIcon,
  DashboardIcon,
  GithubIcon,
  HomeIcon,
  LibraryIcon,
  MemoryIcon,
  MenuIcon,
  ReviewIcon,
  SettingsIcon,
  CloseIcon,
} from "./icons";

const NAV_GROUPS: Array<{
  label: string;
  items: Array<{
    href: string;
    label: string;
    icon: typeof HomeIcon;
    description: string;
  }>;
}> = [
  {
    label: "Overview",
    items: [
      {
        href: "/",
        label: "Home",
        icon: HomeIcon,
        description: "Product overview and the agent process.",
      },
      {
        href: "/dashboard",
        label: "Dashboard",
        icon: DashboardIcon,
        description: "Active task and recent runs.",
      },
    ],
  },
  {
    label: "Workflow",
    items: [
      {
        href: "/compose",
        label: "Compose",
        icon: ComposeIcon,
        description: "Launch a new manuscript or series.",
      },
      {
        href: "/library",
        label: "Library",
        icon: LibraryIcon,
        description: "All manuscripts and artifacts.",
      },
      {
        href: "/review",
        label: "Review",
        icon: ReviewIcon,
        description: "Approval workbench for chapters.",
      },
    ],
  },
  {
    label: "Knowledge",
    items: [
      {
        href: "/memory",
        label: "Memory",
        icon: MemoryIcon,
        description: "Skills, feedback, retrieval preview.",
      },
      {
        href: "/settings",
        label: "Settings",
        icon: SettingsIcon,
        description: "API endpoint and preferences.",
      },
    ],
  },
];

function isActive(currentPath: string, href: string) {
  if (href === "/") return currentPath === "/";
  return currentPath === href || currentPath.startsWith(href + "/");
}

export function Sidebar() {
  const pathname = usePathname() ?? "/";
  const { apiHealth, apiBase } = useApp();
  const [open, setOpen] = useState(false);

  const apiOrigin = (() => {
    try {
      return new URL(apiBase).host;
    } catch {
      return apiBase;
    }
  })();

  return (
    <>
      {/* Mobile bar */}
      <div className="sticky top-0 z-40 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-canvas)]/90 px-4 py-3 backdrop-blur md:hidden">
        <Link href="/" className="flex items-center gap-2.5">
          <Brandmark />
          <span className="font-display text-base font-medium tracking-tight">
            Atlas
          </span>
        </Link>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <a
            href={GITHUB_REPOSITORY_URL}
            target="_blank"
            rel="noreferrer"
            aria-label="View source on GitHub"
            className="btn btn-ghost btn-sm"
          >
            <GithubIcon className="h-4 w-4" />
          </a>
          <button
            type="button"
            aria-label="Open navigation"
            onClick={() => setOpen(true)}
            className="btn btn-ghost btn-sm"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Drawer for mobile */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-[var(--color-ink-900)]/40"
            onClick={() => setOpen(false)}
          />
          <aside className="relative ml-auto flex h-full w-72 flex-col gap-4 border-l border-[var(--color-border)] bg-[var(--color-canvas)] px-4 py-5">
            <div className="flex items-center justify-between">
              <Link
                href="/"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5"
              >
                <Brandmark />
                <span className="font-display text-base font-medium tracking-tight">
                  Atlas
                </span>
              </Link>
              <button
                type="button"
                aria-label="Close navigation"
                onClick={() => setOpen(false)}
                className="btn btn-ghost btn-sm"
              >
                <CloseIcon className="h-5 w-5" />
              </button>
            </div>
            <NavBody pathname={pathname} onNavigate={() => setOpen(false)} />
            <SidebarFooter
              apiHealth={apiHealth}
              apiOrigin={apiOrigin}
            />
          </aside>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-[var(--color-border)] bg-[var(--color-canvas)] md:flex md:flex-col">
        <div className="flex items-center gap-2.5 border-b border-[var(--color-border)] px-5 py-5">
          <Brandmark />
          <div>
            <p className="font-display text-base font-medium tracking-tight">
              Atlas
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--color-ink-400)]">
              Editorial Agent
            </p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <NavBody pathname={pathname} />
        </div>
        <SidebarFooter apiHealth={apiHealth} apiOrigin={apiOrigin} />
      </aside>
    </>
  );
}

function NavBody({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-5">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[var(--color-ink-400)]">
            {group.label}
          </p>
          <div className="flex flex-col gap-0.5">
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  data-active={isActive(pathname, item.href)}
                  className="nav-link"
                >
                  <Icon />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function SidebarFooter({
  apiHealth,
  apiOrigin,
}: {
  apiHealth: "unknown" | "ok" | "error" | "unconfigured";
  apiOrigin: string;
}) {
  const tone =
    apiHealth === "ok"
      ? "text-success"
      : apiHealth === "error"
        ? "text-danger"
        : apiHealth === "unconfigured"
          ? "text-warning"
          : "text-ink-400";
  const label =
    apiHealth === "ok"
      ? "API connected"
      : apiHealth === "error"
        ? "API unreachable"
        : apiHealth === "unconfigured"
          ? "Backend not set"
          : "Checking API";
  const hint =
    apiHealth === "unconfigured"
      ? "Open settings to point the UI at your FastAPI backend."
      : null;
  return (
    <div className="border-t border-border px-4 py-4">
      <Link
        href="/settings"
        className="group block rounded-lg border border-border bg-surface p-3 transition hover:border-border-strong"
      >
        <div className="flex items-center justify-between text-xs font-medium">
          <span className={tone}>
            <span className="dot mr-1.5 inline-block" /> {label}
          </span>
        </div>
        <p className="mt-1 truncate font-mono text-[11px] text-ink-500">
          {apiOrigin}
        </p>
        {hint && (
          <p className="mt-1.5 text-[11px] leading-snug text-ink-500">{hint}</p>
        )}
      </Link>
    </div>
  );
}

function Brandmark() {
  return (
    <span className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--color-ink-900)] text-on-primary shadow-sm">
      <svg
        viewBox="0 0 24 24"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M5 5h14v14H5z" />
        <path d="M9 5v14M15 5v14M5 9h14M5 15h14" />
      </svg>
    </span>
  );
}
