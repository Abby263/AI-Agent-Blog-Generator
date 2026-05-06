"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Field,
  PageHeader,
} from "@/components/ui";
import {
  CheckIcon,
  CloseIcon,
  RefreshIcon,
  SparkIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import {
  type FeedbackItem,
  type MemorySkillsResponse,
  type RetrievalPreviewResponse,
  type Skill,
} from "@/lib/api";

export default function MemoryPage() {
  const { fetchJson, runWithBusy, draft, setDraft } = useApp();
  const [skills, setSkills] = useState<MemorySkillsResponse | null>(null);
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [retrieval, setRetrieval] = useState<RetrievalPreviewResponse | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const [skillsResult, feedbackResult] = await Promise.all([
      runWithBusy("Skill memory", () =>
        fetchJson<MemorySkillsResponse>("/memory/skills"),
      ),
      runWithBusy("Feedback", () =>
        fetchJson<{ feedback: FeedbackItem[] }>("/feedback"),
      ),
    ]);
    if (skillsResult) setSkills(skillsResult);
    if (feedbackResult) setFeedback(feedbackResult.feedback);
    setLoaded(true);
  }, [fetchJson, runWithBusy]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function previewRetrieval() {
    const params = new URLSearchParams({
      topic: draft.topic,
      audience: draft.audience,
      part_number: String(draft.part),
      artifact_type: "draft",
    });
    const result = await runWithBusy("Retrieval preview", () =>
      fetchJson<RetrievalPreviewResponse>(
        `/memory/retrieval-preview?${params}`,
      ),
    );
    if (result) setRetrieval(result);
  }

  async function updateSkill(skillId: string, action: "approve" | "reject") {
    await runWithBusy(`Skill ${action}`, () =>
      fetchJson(`/memory/${encodeURIComponent(skillId)}/${action}`, {
        method: "POST",
      }),
    );
    refresh();
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Memory"
        title="Skills, feedback & retrieval"
        description="Editorial feedback distills into reusable skills. Approved skills shape future runs; candidates wait for human review."
        trailing={
          <Button
            size="sm"
            variant="secondary"
            onClick={refresh}
            leadingIcon={<RefreshIcon className="h-4 w-4" />}
          >
            Refresh
          </Button>
        }
      />

      <Card>
        <CardHeader
          eyebrow="Retrieval"
          title="Preview which skills the agents would use"
          description="Simulates retrieval against the current brief — useful for verifying memory before launching a run."
        />
        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
          <Field label="Topic">
            <input
              className="input"
              value={draft.topic}
              onChange={(event) => setDraft({ topic: event.target.value })}
            />
          </Field>
          <Field label="Chapter">
            <input
              className="input"
              type="number"
              min={1}
              value={draft.part}
              onChange={(event) =>
                setDraft({ part: Number(event.target.value) })
              }
            />
          </Field>
          <Button
            variant="primary"
            onClick={previewRetrieval}
            leadingIcon={<SparkIcon className="h-4 w-4" />}
          >
            Preview retrieval
          </Button>
        </div>
        {retrieval && (
          <div className="mt-5 surface-dark p-4">
            <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-[#dcc99e]">
              Retrieved skill IDs
            </p>
            <p className="mt-1 font-mono text-xs text-[#fffaf0]">
              {retrieval.retrieval.retrieved_skill_ids.join(", ") || "none"}
            </p>
            {retrieval.retrieval.retrieved_guidance.length > 0 && (
              <ul className="mt-3 space-y-1.5 text-sm text-[#e8dcc4]">
                {retrieval.retrieval.retrieved_guidance.map((guidance) => (
                  <li key={guidance} className="flex items-start gap-2">
                    <CheckIcon className="mt-0.5 h-3.5 w-3.5 text-accent" />
                    <span>{guidance}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Card>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            eyebrow="Approved"
            title="Active skills"
            description="These guide writing, review, and improvement."
          />
          <SkillList
            skills={skills?.approved_skills ?? []}
            loaded={loaded}
            tone="success"
            empty="No approved skills yet."
          />
        </Card>
        <Card>
          <CardHeader
            eyebrow="Candidate"
            title="Pending skills"
            description="Approve or reject distilled skills before they influence future runs."
          />
          <SkillList
            skills={skills?.candidate_skills ?? []}
            loaded={loaded}
            tone="info"
            empty="No candidate skills awaiting decision."
            onApprove={(id) => updateSkill(id, "approve")}
            onReject={(id) => updateSkill(id, "reject")}
          />
        </Card>
      </section>

      <Card>
        <CardHeader
          eyebrow="Feedback"
          title="Raw editorial feedback"
          description="Captured from reviewers and downstream signals; later distilled into skills."
        />
        {feedback.length ? (
          <div className="grid gap-2.5">
            {feedback.slice(0, 12).map((item) => (
              <article
                key={item.feedback_id}
                className="rounded-lg border border-border bg-surface px-4 py-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <Badge tone="info">{item.normalized_issue_type}</Badge>
                    <Badge tone="warn">{item.severity}</Badge>
                    <span className="text-ink-500">by {item.reviewer}</span>
                  </div>
                  <span className="font-mono text-[11px] text-ink-400">
                    {item.source_artifact}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-ink-700">
                  {item.raw_feedback}
                </p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title={loaded ? "No feedback recorded" : "Loading…"}
            description={
              loaded
                ? "Feedback collected during reviews will appear here."
                : undefined
            }
          />
        )}
      </Card>
    </div>
  );
}

function SkillList({
  skills,
  loaded,
  tone,
  empty,
  onApprove,
  onReject,
}: {
  skills: Skill[];
  loaded: boolean;
  tone: "success" | "info";
  empty: string;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}) {
  if (!skills.length) {
    return (
      <EmptyState title={loaded ? empty : "Loading…"} />
    );
  }
  return (
    <div className="space-y-2.5">
      {skills.map((skill) => (
        <article
          key={skill.id}
          className="rounded-lg border border-border bg-surface px-4 py-3"
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-medium text-ink-800">{skill.title}</p>
              <p className="mt-0.5 font-mono text-[11px] text-ink-400">
                {skill.id}
              </p>
            </div>
            <Badge tone={tone}>{skill.status}</Badge>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-ink-600">
            {skill.guidance_text}
          </p>
          {(onApprove || onReject) && (
            <div className="mt-3 flex gap-2">
              {onApprove && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => onApprove(skill.id)}
                  leadingIcon={<CheckIcon className="h-3.5 w-3.5" />}
                >
                  Approve
                </Button>
              )}
              {onReject && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onReject(skill.id)}
                  leadingIcon={<CloseIcon className="h-3.5 w-3.5" />}
                >
                  Reject
                </Button>
              )}
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
