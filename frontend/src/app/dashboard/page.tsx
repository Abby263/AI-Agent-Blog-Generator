"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  KeyValue,
  MetricTile,
  PageHeader,
  StatusBadge,
} from "@/components/ui";
import {
  ArrowRightIcon,
  ComposeIcon,
  RefreshIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import {
  type SeriesLatestResponse,
  type TaskSummary,
  WORKFLOW_STAGES,
} from "@/lib/api";

export default function DashboardPage() {
  const { fetchJson, runWithBusy } = useApp();
  const [latest, setLatest] = useState<SeriesLatestResponse | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loaded, setLoaded] = useState(false);

  const refreshAll = useCallback(async () => {
    const [latestResult, tasksResult] = await Promise.all([
      runWithBusy("Latest run", () =>
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
    refreshAll();
  }, [refreshAll]);

  const manifest = latest?.latest_manifest ?? null;
  const seriesScore = latest?.latest_series_evaluation?.overall_score;
  const recentTasks = useMemo(
    () =>
      [...tasks]
        .sort((a, b) =>
          (b.created_at ?? "").localeCompare(a.created_at ?? ""),
        )
        .slice(0, 6),
    [tasks],
  );
  const activeTask = useMemo(
    () =>
      tasks.find((task) =>
        ["pending", "running", "in_progress", "queued"].includes(
          task.status.toLowerCase(),
        ),
      ),
    [tasks],
  );

  const artifactCount = manifest?.artifacts.length ?? 0;
  const artifactByType = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const artifact of manifest?.artifacts ?? []) {
      const key = artifact.artifact_type ?? "artifact";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [manifest?.artifacts]);

  const completed = manifest?.status === "completed";
  const running = activeTask !== undefined;
  const activeIndex = completed
    ? WORKFLOW_STAGES.length - 1
    : running
      ? 2
      : 0;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Operations"
        title="Dashboard"
        description="At-a-glance status of the agent pipeline, the most recent manuscript, and queued background tasks."
        trailing={
          <>
            <Button
              size="sm"
              variant="secondary"
              onClick={refreshAll}
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

      <section className="grid gap-4 md:grid-cols-3">
        <MetricTile
          label="Active task"
          value={activeTask?.task_id ?? "—"}
          hint={activeTask ? `status: ${activeTask.status}` : "Pipeline idle"}
          tone={activeTask ? "dark" : "neutral"}
        />
        <MetricTile
          label="Latest manuscript"
          value={manifest?.topic ?? "No manuscripts yet"}
          hint={
            manifest
              ? `${manifest.num_parts} parts · ${manifest.target_audience} · ${manifest.status}`
              : "Compose your first run to see it here."
          }
        />
        <MetricTile
          label="Series evaluation"
          value={seriesScore !== undefined ? `${seriesScore} / 10` : "—"}
          hint={
            latest?.latest_series_evaluation?.summary ??
            "No evaluation captured yet."
          }
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader
            eyebrow="Pipeline"
            title="Workflow status"
            description="Each stage produces an inspectable artifact. The active stage is highlighted."
          />
          <div className="workflow-track">
            {WORKFLOW_STAGES.map((stage, index) => {
              const state =
                completed || index < activeIndex
                  ? "done"
                  : index === activeIndex
                    ? "active"
                    : "queued";
              return (
                <div
                  key={stage.name}
                  className={`workflow-cell workflow-cell-${state}`}
                >
                  <span className="font-mono text-[11px] opacity-70">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <strong>{stage.name}</strong>
                  <span className="text-[11px] opacity-80">
                    {state === "done"
                      ? "Complete"
                      : state === "active"
                        ? "In motion"
                        : "Queued"}
                  </span>
                </div>
              );
            })}
          </div>
        </Card>

        <Card>
          <CardHeader
            eyebrow="Manifest"
            title="Latest manuscript"
            description="The most recently produced run on the configured backend."
          />
          {manifest ? (
            <div className="space-y-1">
              <KeyValue label="Run ID">
                <span className="font-mono text-xs">{manifest.run_id}</span>
              </KeyValue>
              <KeyValue label="Topic">{manifest.topic}</KeyValue>
              <KeyValue label="Audience">{manifest.target_audience}</KeyValue>
              <KeyValue label="Parts">{manifest.num_parts}</KeyValue>
              <KeyValue label="Status">
                <StatusBadge status={manifest.status} />
              </KeyValue>
              <KeyValue label="Artifacts">{artifactCount}</KeyValue>
              {Object.keys(artifactByType).length > 0 && (
                <div className="hairline-top mt-3 flex flex-wrap gap-1.5 pt-3">
                  {Object.entries(artifactByType).map(([key, value]) => (
                    <Badge key={key} tone="neutral">
                      {key} · {value}
                    </Badge>
                  ))}
                </div>
              )}
              <div className="mt-4">
                <Link
                  href={`/library/${encodeURIComponent(manifest.run_id)}`}
                  className="btn btn-secondary btn-sm"
                >
                  Open manuscript
                  <ArrowRightIcon className="h-4 w-4" />
                </Link>
              </div>
            </div>
          ) : (
            <EmptyState
              title={loaded ? "No runs yet" : "Loading…"}
              description={
                loaded
                  ? "Compose a brief and launch the agent pipeline to see your first manuscript here."
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
      </section>

      <Card>
        <CardHeader
          eyebrow="Background tasks"
          title="Recent activity"
          description="Async runs and outline jobs from the FastAPI backend."
        />
        {recentTasks.length ? (
          <div className="overflow-hidden rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-left text-[11px] uppercase tracking-[0.12em] text-ink-500">
                <tr>
                  <th className="px-4 py-2.5">Task ID</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Created</th>
                  <th className="px-4 py-2.5">Completed</th>
                  <th className="px-4 py-2.5">Notes</th>
                </tr>
              </thead>
              <tbody>
                {recentTasks.map((task, idx) => (
                  <tr
                    key={task.task_id}
                    className={
                      idx === 0
                        ? ""
                        : "border-t border-border"
                    }
                  >
                    <td className="px-4 py-2.5">
                      <span className="font-mono text-xs text-ink-700">
                        {task.task_id}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={task.status} />
                    </td>
                    <td className="px-4 py-2.5 text-ink-500">
                      <FormattedTime value={task.created_at} />
                    </td>
                    <td className="px-4 py-2.5 text-ink-500">
                      <FormattedTime value={task.completed_at ?? undefined} />
                    </td>
                    <td className="px-4 py-2.5 text-ink-500">
                      {task.error
                        ? <span className="text-danger">{task.error}</span>
                        : task.message ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title={loaded ? "No tasks recorded" : "Loading…"}
            description={
              loaded
                ? "Tasks created via the compose flow will appear here once submitted."
                : undefined
            }
          />
        )}
      </Card>
    </div>
  );
}

function FormattedTime({ value }: { value?: string }) {
  if (!value) return <>—</>;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return <>{value}</>;
  const formatted = date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  return <span className="tabular-nums">{formatted}</span>;
}
