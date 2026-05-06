"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  KeyValue,
  PageHeader,
  StatusBadge,
} from "@/components/ui";
import {
  ArrowRightIcon,
  RefreshIcon,
  ReviewIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import {
  type ArtifactRecord,
  type RunManifest,
} from "@/lib/api";

type RunDetail = RunManifest & {
  message?: string;
};

export default function ManuscriptDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = use(params);
  const { fetchJson, runWithBusy } = useApp();
  const [manifest, setManifest] = useState<RunDetail | null>(null);
  const [artifactsResponse, setArtifactsResponse] =
    useState<{ artifacts: ArtifactRecord[] } | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const [manifestResult, artifactsResult] = await Promise.all([
      runWithBusy("Manuscript", () =>
        fetchJson<RunDetail>(`/runs/${encodeURIComponent(runId)}`),
      ),
      runWithBusy("Artifacts", () =>
        fetchJson<{ artifacts: ArtifactRecord[] }>(
          `/runs/${encodeURIComponent(runId)}/artifacts`,
        ),
      ),
    ]);
    if (manifestResult) setManifest(manifestResult);
    if (artifactsResult) setArtifactsResponse(artifactsResult);
    setLoaded(true);
  }, [fetchJson, runWithBusy, runId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const artifacts = useMemo(
    () => artifactsResponse?.artifacts ?? manifest?.artifacts ?? [],
    [artifactsResponse?.artifacts, manifest?.artifacts],
  );

  const partsList = useMemo(() => {
    const parts = new Map<number, ArtifactRecord[]>();
    for (const artifact of artifacts) {
      const part = artifact.part_number ?? 0;
      if (!parts.has(part)) parts.set(part, []);
      parts.get(part)!.push(artifact);
    }
    return Array.from(parts.entries()).sort(([a], [b]) => a - b);
  }, [artifacts]);

  const partStatuses = manifest?.part_statuses ?? {};

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Manuscript"
        title={manifest?.topic ?? runId}
        description={
          manifest
            ? `Run ID ${manifest.run_id} · ${manifest.num_parts} parts · ${manifest.target_audience} audience`
            : `Run ID ${runId}`
        }
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
            <Link href="/review">
              <Button
                size="sm"
                variant="accent"
                leadingIcon={<ReviewIcon className="h-4 w-4" />}
              >
                Open review
              </Button>
            </Link>
          </>
        }
      />

      {!loaded && <p className="text-sm text-ink-500">Loading manuscript…</p>}

      {manifest && (
        <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <Card>
            <CardHeader
              eyebrow="Overview"
              title="Manifest"
              description="Top-level metadata captured for this run."
            />
            <div>
              <KeyValue label="Status">
                <StatusBadge status={manifest.status} />
              </KeyValue>
              <KeyValue label="Topic">{manifest.topic}</KeyValue>
              <KeyValue label="Audience">{manifest.target_audience}</KeyValue>
              <KeyValue label="Total parts">{manifest.num_parts}</KeyValue>
              <KeyValue label="Selected parts">
                {(manifest.selected_parts ?? []).join(", ") || "—"}
              </KeyValue>
              <KeyValue label="Total artifacts">{artifacts.length}</KeyValue>
            </div>
          </Card>

          <Card>
            <CardHeader
              eyebrow="Quality"
              title="Part status"
              description="Current state for each chapter in the series."
            />
            {Object.keys(partStatuses).length ? (
              <div className="grid gap-1.5">
                {Object.entries(partStatuses).map(([part, status]) => (
                  <div
                    key={part}
                    className="flex items-center justify-between rounded-md border border-border bg-canvas px-3 py-2 text-sm"
                  >
                    <span className="font-medium text-ink-800">
                      Part {part}
                    </span>
                    <StatusBadge status={status} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No per-part status reported"
                description="Status is populated as each chapter completes the pipeline."
              />
            )}
          </Card>
        </section>
      )}

      <Card>
        <CardHeader
          eyebrow="Artifacts"
          title="Chapters & deliverables"
          description="Drill into each part to see drafts, reviews, finals, and asset plans produced by the agents."
        />
        {partsList.length ? (
          <div className="space-y-4">
            {partsList.map(([part, items]) => (
              <PartGroup key={part} part={part} artifacts={items} />
            ))}
          </div>
        ) : (
          <EmptyState
            title={loaded ? "No artifacts found" : "Loading…"}
            description={
              loaded
                ? "Once the pipeline produces drafts, reviews, and finals, they'll be listed here."
                : undefined
            }
          />
        )}
      </Card>
    </div>
  );
}

function PartGroup({
  part,
  artifacts,
}: {
  part: number;
  artifacts: ArtifactRecord[];
}) {
  return (
    <div className="rounded-xl border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <p className="eyebrow eyebrow-accent">
            {part === 0 ? "Series-wide" : `Chapter ${part}`}
          </p>
          <p className="font-display text-lg font-medium tracking-tight">
            {artifacts.length} artifact{artifacts.length === 1 ? "" : "s"}
          </p>
        </div>
        <Link href="/review" className="btn btn-ghost btn-sm">
          Review <ArrowRightIcon className="h-3.5 w-3.5" />
        </Link>
      </div>
      <ul className="divide-y divide-border">
        {artifacts.map((artifact) => (
          <li
            key={`${artifact.artifact_type}-${artifact.path}`}
            className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Badge tone="accent">
                  {artifact.artifact_type ?? "artifact"}
                </Badge>
                {artifact.created_at && (
                  <span className="text-xs text-ink-400">
                    {new Date(artifact.created_at).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                )}
              </div>
              <p className="mt-1 truncate font-mono text-xs text-ink-600">
                {artifact.path}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
