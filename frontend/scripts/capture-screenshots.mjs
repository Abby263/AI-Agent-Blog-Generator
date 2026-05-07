/**
 * Capture UI screenshots used in the README.
 *
 * Usage:
 *   1. npm run build && PORT=4321 npm run start &
 *   2. node scripts/capture-screenshots.mjs
 *
 * Requires playwright. Install once with `npm i -D playwright` and
 * `npx playwright install chromium`.
 */

import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const BASE = process.env.SCREENSHOT_BASE ?? "http://127.0.0.1:4321";
const OUT = resolve(
  process.env.SCREENSHOT_OUT ?? "../docs/assets",
);

const PAGES = [
  { path: "/", name: "ui-home" },
  { path: "/dashboard", name: "ui-dashboard" },
  { path: "/compose", name: "ui-compose" },
  { path: "/library", name: "ui-library" },
  { path: "/review", name: "ui-review" },
  { path: "/memory", name: "ui-memory" },
  { path: "/settings", name: "ui-settings" },
];

const VIEWPORT = { width: 1600, height: 1100 };
const DPR = 2;

async function capture(theme) {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: DPR,
    colorScheme: theme === "dark" ? "dark" : "light",
  });
  await context.addInitScript((themeArg) => {
    try {
      window.localStorage.setItem("blog-series-theme", themeArg);
    } catch {
      /* ignore */
    }
  }, theme);
  const page = await context.newPage();

  for (const { path: p, name } of PAGES) {
    const url = BASE + p;
    const file = theme === "dark" ? `${name}-dark.png` : `${name}.png`;
    process.stdout.write(`[${theme}] ${url} -> ${file}\n`);
    await page
      .goto(url, { waitUntil: "networkidle", timeout: 30_000 })
      .catch(() => {});
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${OUT}/${file}`, fullPage: false });
  }
  await browser.close();
}

await mkdir(OUT, { recursive: true });
await capture("light");
await capture("dark");
process.stdout.write("done\n");
