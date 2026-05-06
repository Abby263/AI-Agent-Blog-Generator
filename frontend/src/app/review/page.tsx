"use client";

import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Field,
  KeyValue,
  PageHeader,
  StatusBadge,
} from "@/components/ui";
import {
  CheckIcon,
  CloseIcon,
  RefreshIcon,
  ReviewIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import {
  APPROVAL_OPTIONS,
  type BlogArtifactsResponse,
} from "@/lib/api";

export default function ReviewPage() {
  const { fetchJson, runWithBusy } = useApp();
  const [partId, setPartId] = useState("Part-1-introduction");
  const [data, setData] = useState<BlogArtifactsResponse | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [decision, setDecision] = useState<string>("approved");
  const [reviewer, setReviewer] = useState("editor");
  const [comments, setComments] = useState("");

  async function loadPart() {
    const result = await runWithBusy("Load chapter", () =>
      fetchJson<BlogArtifactsResponse>(
        `/blogs/${encodeURIComponent(partId)}`,
      ),
    );
    if (result) setData(result);
    setLoaded(true);
  }

  async function submit() {
    const result = await runWithBusy("Submit approval", () =>
      fetchJson<BlogArtifactsResponse>(
        `/approval/${encodeURIComponent(partId)}`,
        {
          method: "POST",
          body: JSON.stringify({
            status: decision,
            reviewer_name: reviewer,
            comments,
          }),
        },
      ),
    );
    if (result) setData(result);
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Review"
        title="Approval workbench"
        description="Inspect a chapter's artifacts, evaluation, and current approval state — then issue an editorial decision."
      />

      <Card>
        <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <Field label="Chapter / part ID" hint="Examples: Part-1-introduction">
            <input
              className="input font-mono"
              value={partId}
              onChange={(event) => setPartId(event.target.value)}
            />
          </Field>
          <Button
            variant="primary"
            onClick={loadPart}
            leadingIcon={<RefreshIcon className="h-4 w-4" />}
          >
            Load chapter
          </Button>
        </div>
      </Card>

      {data ? (
        <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <Card>
            <CardHeader
              eyebrow="Artifacts"
              title="Chapter artifacts"
              description="Drafts, reviews, finals, and asset plans produced for this chapter."
            />
            {data.artifacts.length ? (
              <ul className="divide-y divide-border">
                {data.artifacts.map((artifact) => (
                  <li
                    key={`${artifact.artifact_type}-${artifact.path}`}
                    className="flex flex-wrap items-center gap-3 py-2.5"
                  >
                    <Badge tone="accent">
                      {artifact.artifact_type ?? "artifact"}
                    </Badge>
                    <span className="font-mono text-xs text-ink-600 break-all">
                      {artifact.path}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                title="No artifacts"
                description="The chapter has not produced inspectable artifacts yet."
              />
            )}
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader
                eyebrow="Quality"
                title="Evaluation"
                description="Automated reviewer scores, including skill adherence."
              />
              <div>
                <KeyValue label="Approval status">
                  <StatusBadge status={data.approval?.status ?? "not submitted"} />
                </KeyValue>
                <KeyValue label="Reviewer">
                  {data.approval?.reviewer_name ?? "—"}
                </KeyValue>
                <KeyValue label="Overall score">
                  {data.evaluation?.overall_score !== undefined
                    ? `${data.evaluation.overall_score} / 10`
                    : "—"}
                </KeyValue>
                <KeyValue label="Skill adherence">
                  {data.evaluation?.skill_adherence_score !== undefined
                    ? `${data.evaluation.skill_adherence_score} / 10`
                    : "—"}
                </KeyValue>
              </div>
              {data.evaluation?.summary && (
                <div className="mt-4 rounded-md border border-border bg-canvas p-3 text-sm leading-relaxed text-ink-700">
                  {data.evaluation.summary}
                </div>
              )}
              {data.approval?.comments && (
                <div className="mt-3 rounded-md border border-border bg-canvas p-3 text-sm leading-relaxed text-ink-700">
                  <p className="eyebrow mb-1.5">Reviewer comments</p>
                  {data.approval.comments}
                </div>
              )}
            </Card>

            <Card>
              <CardHeader
                eyebrow="Decision"
                title="Issue an approval"
                description="Production runs require an approval before publish-ready."
              />
              <div className="space-y-4">
                <Field label="Decision">
                  <div className="grid gap-2 sm:grid-cols-2">
                    {APPROVAL_OPTIONS.map((option) => {
                      const active = decision === option;
                      const isPositive = option.startsWith("approved");
                      return (
                        <button
                          type="button"
                          key={option}
                          onClick={() => setDecision(option)}
                          className={`flex items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition ${
                            active
                              ? isPositive
                                ? "border-success bg-success-soft text-success"
                                : "border-danger bg-danger-soft text-danger"
                              : "border-border bg-surface text-ink-700 hover:border-border-strong"
                          }`}
                        >
                          {isPositive ? (
                            <CheckIcon className="h-4 w-4" />
                          ) : (
                            <CloseIcon className="h-4 w-4" />
                          )}
                          <span className="capitalize">
                            {option.replace(/_/g, " ")}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </Field>
                <Field label="Reviewer">
                  <input
                    className="input"
                    value={reviewer}
                    onChange={(event) => setReviewer(event.target.value)}
                  />
                </Field>
                <Field label="Comments">
                  <textarea
                    className="input"
                    placeholder="Notes for the author / next iteration…"
                    value={comments}
                    onChange={(event) => setComments(event.target.value)}
                  />
                </Field>
                <Button
                  variant="accent"
                  onClick={submit}
                  leadingIcon={<ReviewIcon className="h-4 w-4" />}
                >
                  Submit decision
                </Button>
              </div>
            </Card>
          </div>
        </section>
      ) : (
        <EmptyState
          title={loaded ? "Chapter not found" : "Load a chapter to begin"}
          description={
            loaded
              ? "The provided part ID didn't return any artifacts. Confirm the ID and try again."
              : "Enter the part ID for the chapter you want to inspect, then load its artifacts and evaluation."
          }
        />
      )}
    </div>
  );
}
