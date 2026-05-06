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
  apiHealth: "unknown" | "ok" | "error";
  refreshHealth: () => Promise<void>;
};

const AppContext = createContext<AppContextValue | null>(null);

const STORAGE_KEY_API = "blog-series-api-base";
const STORAGE_KEY_DRAFT = "blog-series-draft";

export function AppProvider({ children }: { children: ReactNode }) {
  const [apiBase, setApiBaseState] = useState<string>(DEFAULT_API_BASE);
  const [draft, setDraftState] = useState<LaunchSettings>(defaultLaunchSettings);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [apiHealth, setApiHealth] = useState<"unknown" | "ok" | "error">(
    "unknown",
  );
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
    hydrated.current = true;
  }, []);

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
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within <AppProvider>.");
  return ctx;
}
