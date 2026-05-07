"use client";

import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Field,
  HelpText,
  PageHeader,
} from "@/components/ui";
import { CheckIcon, RefreshIcon, ServerIcon } from "@/components/icons";
import { ThemeToggle } from "@/components/theme-toggle";
import { useApp } from "@/lib/context";
import { DEFAULT_API_BASE } from "@/lib/api";

export default function SettingsPage() {
  const { apiBase, setApiBase, apiHealth, refreshHealth, resetDraft } =
    useApp();
  const [draftBase, setDraftBase] = useState(apiBase);

  useEffect(() => {
    setDraftBase(apiBase);
  }, [apiBase]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Settings"
        title="Configuration"
        description="Point the UI at the FastAPI backend and manage local preferences."
      />

      <Card>
        <CardHeader
          eyebrow="API endpoint"
          title="FastAPI backend"
          description="Compose and dashboard pages call this base URL. Run the backend locally with `uv run python -m blog_series_agent api`, or point this at a hosted deployment."
          trailing={
            <Badge
              tone={
                apiHealth === "ok"
                  ? "success"
                  : apiHealth === "error"
                    ? "danger"
                    : "neutral"
              }
              withDot
            >
              {apiHealth === "ok"
                ? "Connected"
                : apiHealth === "error"
                  ? "Unreachable"
                  : "Checking"}
            </Badge>
          }
        />
        <div className="space-y-4">
          <Field
            label="Base URL"
            hint="Saved to localStorage on this device"
          >
            <div className="flex flex-wrap gap-2">
              <input
                className="input flex-1 font-mono"
                value={draftBase}
                onChange={(event) => setDraftBase(event.target.value)}
                placeholder="http://localhost:8000"
              />
              <Button
                variant="primary"
                onClick={() => {
                  setApiBase(draftBase.trim() || DEFAULT_API_BASE);
                  refreshHealth();
                }}
                leadingIcon={<CheckIcon className="h-4 w-4" />}
              >
                Save
              </Button>
              <Button
                variant="secondary"
                onClick={refreshHealth}
                leadingIcon={<RefreshIcon className="h-4 w-4" />}
              >
                Test connection
              </Button>
            </div>
          </Field>
          <HelpText>
            The connection check pings <span className="kbd">/api/health</span>{" "}
            then <span className="kbd">/health</span> to support either router
            mounting style.
          </HelpText>
        </div>
      </Card>

      <Card>
        <CardHeader
          eyebrow="Appearance"
          title="Theme"
          description="Switch between light, dark, or follow your system preference."
        />
        <ThemeToggle compact={false} />
      </Card>

      <Card>
        <CardHeader
          eyebrow="Defaults"
          title="Compose draft"
          description="Reset the saved compose-wizard inputs back to the recommended defaults."
        />
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            onClick={() => resetDraft()}
            leadingIcon={<RefreshIcon className="h-4 w-4" />}
          >
            Reset compose draft
          </Button>
          <HelpText>
            This clears your in-progress brief on this device only — it does
            not affect any backend state.
          </HelpText>
        </div>
      </Card>

      <Card>
        <CardHeader
          eyebrow="About"
          title="Atlas editorial agent"
          description="Built on LangGraph and DeepAgents. The frontend is a Next.js 16 client app; the backend is a FastAPI service."
          trailing={<ServerIcon className="h-5 w-5 text-ink-400" />}
        />
        <ul className="grid gap-2 text-sm text-ink-600 md:grid-cols-2">
          <li>· Multi-agent pipeline: research → outline → draft → review → improve → assets → approval</li>
          <li>· Run modes: dev, review, production (production locks approval gate on)</li>
          <li>· Skill memory accumulates from approved feedback</li>
          <li>· Manifests track every artifact for audit and resumability</li>
        </ul>
      </Card>
    </div>
  );
}
