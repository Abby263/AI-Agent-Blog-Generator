"use client";

import { GITHUB_REPOSITORY_URL } from "@/lib/api";
import { GithubIcon } from "./icons";
import { ThemeToggle } from "./theme-toggle";

export function Topbar() {
  return (
    <div className="hairline-bottom sticky top-0 z-30 hidden h-12 items-center justify-end gap-1.5 bg-canvas/85 px-6 backdrop-blur md:flex">
      <ThemeToggle />
      <a
        href={GITHUB_REPOSITORY_URL}
        target="_blank"
        rel="noreferrer"
        aria-label="View source on GitHub"
        className="btn btn-ghost btn-sm"
      >
        <GithubIcon className="h-4 w-4" />
        <span className="text-xs font-medium">GitHub</span>
      </a>
    </div>
  );
}
