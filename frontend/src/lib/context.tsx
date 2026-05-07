"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";
import {
  DEFAULT_API_BASE,
  apiFetch,
  type LaunchSettings,
  defaultLaunchSettings,
} from "./api";

type ToastTone = "info" | "success" | "error";

type Toast = {
  id: string;
  tone: ToastTone;
  message: string;
};

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

type AppContextValue = {
  apiBase: string;
  setApiBase: (value: string) => void;
  draft: LaunchSettings;
  setDraft: (
    update: Partial<LaunchSettings> | ((prev: LaunchSettings) => LaunchSettings),
  ) => void;
  resetDraft: () => void;
  fetchJson: <T>(path: string, init?: RequestInit) => Promise<T>;
  toasts: Toast[];
  pushToast: (tone: ToastTone, message: string) => void;
  dismissToast: (id: string) => void;
  busy: string | null;
  runWithBusy: <T>(label: string, action: () => Promise<T>) => Promise<T | null>;
  apiHealth: "unknown" | "ok" | "error" | "unconfigured";
  refreshHealth: () => Promise<void>;
  themePreference: ThemePreference;
  resolvedTheme: ResolvedTheme;
  setThemePreference: (value: ThemePreference) => void;
};

const AppContext = createContext<AppContextValue | null>(null);

const STORAGE_KEY_API = "blog-series-api-base";
const STORAGE_KEY_DRAFT = "blog-series-draft";
const STORAGE_KEY_THEME = "blog-series-theme";

function readSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [apiBase, setApiBaseState] = useState<string>(DEFAULT_API_BASE);
  const [draft, setDraftState] = useState<LaunchSettings>(defaultLaunchSettings);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [apiHealth, setApiHealth] = useState<
    "unknown" | "ok" | "error" | "unconfigured"
  >("unknown");
  const [themePreference, setThemePreferenceState] =
    useState<ThemePreference>("system");
  const [systemTheme, setSystemTheme] = useState<ResolvedTheme>("light");
  const hydrated = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedBase = window.localStorage.getItem(STORAGE_KEY_API);
    if (storedBase) setApiBaseState(storedBase);
    const storedDraft = window.localStorage.getItem(STORAGE_KEY_DRAFT);
    if (storedDraft) {
      try {
        const parsed = JSON.parse(storedDraft) as Partial<LaunchSettings>;
        setDraftState((prev) => ({ ...prev, ...parsed }));
      } catch {
        /* ignore */
      }
    }
    const storedTheme = window.localStorage.getItem(
      STORAGE_KEY_THEME,
    ) as ThemePreference | null;
    if (storedTheme === "light" || storedTheme === "dark" || storedTheme === "system") {
      setThemePreferenceState(storedTheme);
    }
    setSystemTheme(readSystemTheme());
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event: MediaQueryListEvent) =>
      setSystemTheme(event.matches ? "dark" : "light");
    media.addEventListener("change", onChange);
    hydrated.current = true;
    return () => media.removeEventListener("change", onChange);
  }, []);

  const resolvedTheme: ResolvedTheme =
    themePreference === "system" ? systemTheme : themePreference;

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [resolvedTheme]);

  useEffect(() => {
    if (!hydrated.current) return;
    window.localStorage.setItem(STORAGE_KEY_THEME, themePreference);
  }, [themePreference]);

  const setThemePreference = useCallback(
    (value: ThemePreference) => setThemePreferenceState(value),
    [],
  );

  useEffect(() => {
    if (!hydrated.current) return;
    window.localStorage.setItem(STORAGE_KEY_API, apiBase);
  }, [apiBase]);

  useEffect(() => {
    if (!hydrated.current) return;
    window.localStorage.setItem(STORAGE_KEY_DRAFT, JSON.stringify(draft));
  }, [draft]);

  const setApiBase = useCallback((value: string) => setApiBaseState(value), []);

  const setDraft = useCallback<AppContextValue["setDraft"]>((update) => {
    setDraftState((prev) =>
      typeof update === "function" ? update(prev) : { ...prev, ...update },
    );
  }, []);

  const resetDraft = useCallback(
    () => setDraftState(defaultLaunchSettings),
    [],
  );

  const fetchJson = useCallback(
    <T,>(path: string, init?: RequestInit) =>
      apiFetch<T>(apiBase, path, init),
    [apiBase],
  );

  const pushToast = useCallback((tone: ToastTone, message: string) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setToasts((prev) => [...prev, { id, tone, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const runWithBusy = useCallback(
    async <T,>(label: string, action: () => Promise<T>): Promise<T | null> => {
      setBusy(label);
      try {
        const result = await action();
        pushToast("success", `${label} complete.`);
        return result;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : `${label} failed.`;
        pushToast("error", message);
        return null;
      } finally {
        setBusy(null);
      }
    },
    [pushToast],
  );

  const refreshHealth = useCallback(async () => {
    const looksLikeLocalDefault =
      typeof window !== "undefined" &&
      apiBase.includes("localhost") &&
      window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1";
    if (looksLikeLocalDefault) {
      setApiHealth("unconfigured");
      return;
    }
    try {
      await apiFetch(apiBase, "/api/health");
      setApiHealth("ok");
    } catch {
      try {
        await apiFetch(apiBase, "/health");
        setApiHealth("ok");
      } catch {
        setApiHealth("error");
      }
    }
  }, [apiBase]);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  const value = useMemo<AppContextValue>(
    () => ({
      apiBase,
      setApiBase,
      draft,
      setDraft,
      resetDraft,
      fetchJson,
      toasts,
      pushToast,
      dismissToast,
      busy,
      runWithBusy,
      apiHealth,
      refreshHealth,
      themePreference,
      resolvedTheme,
      setThemePreference,
    }),
    [
      apiBase,
      setApiBase,
      draft,
      setDraft,
      resetDraft,
      fetchJson,
      toasts,
      pushToast,
      dismissToast,
      busy,
      runWithBusy,
      apiHealth,
      refreshHealth,
      themePreference,
      resolvedTheme,
      setThemePreference,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within <AppProvider>.");
  return ctx;
}
