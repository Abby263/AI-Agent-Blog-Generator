"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  PageHeader,
  StatusBadge,
} from "@/components/ui";
import {
  ArrowRightIcon,
  ComposeIcon,
  RefreshIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import { type SeriesLatestResponse, type TaskSummary } from "@/lib/api";

export default function LibraryPage() {
  const { fetchJson, runWithBusy } = useApp();
  const [latest, setLatest] = useState<SeriesLatestResponse | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [filter, setFilter] = useState<"all" | "running" | "completed" | "failed">("all");
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const [latestResult, tasksResult] = await Promise.all([
      runWithBusy("Latest manuscript", () =>
        fetchJson<SeriesLatestResponse>("/series/latest"),
      ),
      runWithBusy("Tasks", () =>
        fetchJson<{ tasks: TaskSummary[] }>("/tasks"),
      ),
    ]);
    if (latestResult) setLatest(latestResult);
    if (tasksResult) setTasks(tasksResult.tasks);
    setLoaded(true);
  }, [fetchJson, runWithBusy]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const filtered = useMemo(() => {
    return tasks.filter((task) => {
      if (filter === "all") return true;
      const status = task.status.toLowerCase();
      if (filter === "running") {
        return ["running", "pending", "in_progress", "queued"].includes(status);
      }
      if (filter === "completed") return status === "completed";
      if (filter === "failed") return status === "failed";
      return true;
    });
  }, [tasks, filter]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Library"
        title="Manuscripts & runs"
        description="Every run produces a manifest of artifacts. Open a run to inspect drafts, reviews, evaluations, and approvals."
        trailing={
          <>
            <Button
              size="sm"
              variant="secondary"
              onClick={refresh}
              leadingIcon={<RefreshIcon className="h-4 w-4" />}
            >
              Refresh
            </Button>
            <Link href="/compose">
              <Button
                size="sm"
                variant="accent"
                leadingIcon={<ComposeIcon className="h-4 w-4" />}
              >
                New manuscript
              </Button>
            </Link>
          </>
        }
      />

      {latest?.latest_manifest && (
        <Card className="border-accent-soft">
          <div className="flex flex-col items-start justify-between gap-4 lg:flex-row lg:items-center">
            <div>
              <p className="eyebrow eyebrow-accent">Most recent</p>
              <h2 className="mt-1.5 font-display text-2xl font-medium tracking-tight">
                {latest.latest_manifest.topic}
              </h2>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-ink-500">
                <Badge tone="neutral">
                  {latest.latest_manifest.num_parts} parts
                </Badge>
                <Badge tone="neutral">
                  {latest.latest_manifest.target_audience} audience
                </Badge>
                <StatusBadge status={latest.latest_manifest.status} />
                {latest.latest_series_evaluation?.overall_score !== undefined && (
                  <Badge tone="success">
                    Score {latest.latest_series_evaluation.overall_score}/10
                  </Badge>
                )}
              </div>
            </div>
            <Link
              href={`/library/${encodeURIComponent(latest.latest_manifest.run_id)}`}
            >
              <Button
                variant="primary"
                trailingIcon={<ArrowRightIcon className="h-4 w-4" />}
              >
                Open manuscript
              </Button>
            </Link>
          </div>
        </Card>
      )}

      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="eyebrow eyebrow-accent">Run history</p>
            <h2 className="mt-1 font-display text-xl font-medium tracking-tight">
              All background tasks
            </h2>
          </div>
          <div className="flex flex-wrap gap-1.5 rounded-lg border border-border bg-canvas p-1">
            {(["all", "running", "completed", "failed"] as const).map(
              (option) => (
                <button
                  type="button"
                  key={option}
                  onClick={() => setFilter(option)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition ${
                    filter === option
                      ? "bg-surface text-ink-900 shadow-sm"
                      : "text-ink-500 hover:text-ink-800"
                  }`}
                >
                  {option}
                </button>
              ),
            )}
          </div>
        </div>

        {filtered.length ? (
          <div className="grid gap-2.5">
            {filtered.map((task) => (
              <article
                key={task.task_id}
                className="rounded-lg border border-border bg-surface px-4 py-3.5 transition hover:border-border-strong"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-mono text-xs text-ink-500">
                      {task.task_id}
                    </p>
                    <p className="mt-0.5 truncate text-sm font-medium text-ink-800">
                      {task.message ?? "Background run"}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <StatusBadge status={task.status} />
                    {task.created_at && (
                      <span className="text-xs text-ink-500 tabular-nums">
                        {formatDate(task.created_at)}
                      </span>
                    )}
                    {task.completed_at && (
                      <Badge tone="neutral">
                        Done {formatDate(task.completed_at)}
                      </Badge>
                    )}
                  </div>
                </div>
                {task.error && (
                  <p className="mt-2 rounded border border-danger/20 bg-danger-soft px-3 py-2 text-xs text-danger">
                    {task.error}
                  </p>
                )}
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title={loaded ? "No runs match this filter" : "Loading…"}
            description={
              loaded
                ? "Adjust the filter or compose a new manuscript to populate the library."
                : undefined
            }
            action={
              loaded ? (
                <Link href="/compose">
                  <Button variant="accent">Compose a brief</Button>
                </Link>
              ) : undefined
            }
          />
        )}
      </Card>
    </div>
  );
}

function formatDate(value: string) {
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}
