"use client";

import { useEffect, useMemo, useState } from "react";
import type { FormEvent, ReactNode } from "react";

const DEFAULT_API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type ArtifactRecord = {
  artifact_id?: string;
  artifact_type?: string;
  path: string;
  part_number?: number | null;
  created_at?: string;
};

type RunManifest = {
  run_id: string;
  topic: string;
  target_audience: string;
  num_parts: number;
  status: string;
  artifacts: ArtifactRecord[];
  selected_parts?: number[];
  part_statuses?: Record<string, string>;
};

type TaskSummary = {
  task_id: string;
  status: string;
  message?: string;
  created_at?: string;
  completed_at?: string | null;
  error?: string | null;
};

type SeriesLatestResponse = {
  latest_outline_path?: string | null;
  latest_manifest?: RunManifest | null;
  latest_series_evaluation?: { overall_score?: number; summary?: string } | null;
};

type BlogArtifactsResponse = {
  part_id: string;
  artifacts: ArtifactRecord[];
  approval?: ApprovalRecord | null;
  evaluation?: { overall_score?: number; skill_adherence_score?: number; summary?: string } | null;
};

type ApprovalRecord = {
  status: string;
  comments?: string;
  reviewer_name?: string;
  timestamp?: string;
};

type Skill = {
  id: string;
  title: string;
  category?: string;
  guidance_text: string;
  status: string;
  active: boolean;
  usage_count?: number;
};

type MemorySkillsResponse = {
  candidate_skills: Skill[];
  approved_skills: Skill[];
};

type FeedbackItem = {
  feedback_id: string;
  raw_feedback: string;
  normalized_issue_type: string;
  severity: string;
  reviewer: string;
  source_artifact: string;
};

type RetrievalPreviewResponse = {
  retrieval: {
    retrieved_skill_ids: string[];
    retrieved_guidance: string[];
    retrieval_notes: string[];
  };
};

type LaunchForm = {
  topic: string;
  audience: string;
  parts: number;
  selectedParts: string;
  part: number;
  minWords: number;
  maxWords: number;
  runMode: "dev" | "review" | "production";
  approvalRequired: boolean;
  useMemory: boolean;
  webSearch: boolean;
};

const initialForm: LaunchForm = {
  topic: "ML System Design",
  audience: "intermediate",
  parts: 12,
  selectedParts: "1,2,3",
  part: 1,
  minWords: 2000,
  maxWords: 3000,
  runMode: "dev",
  approvalRequired: false,
  useMemory: true,
  webSearch: true,
};

const approvalOptions = [
  "approved",
  "approved_with_notes",
  "changes_requested",
  "rejected",
];

const inspirationCards = [
  {
    title: "Workflow canvas",
    source: "Dify / Flowise",
    detail: "Show the agent pipeline as a visible staged system, not a hidden form submit.",
  },
  {
    title: "Trace + eval mindset",
    source: "LangSmith",
    detail: "Put run health, scores, feedback, and quality signals next to artifacts.",
  },
  {
    title: "Research to publish",
    source: "StoryDesk / Jasper",
    detail: "Treat chapters as source-backed content packages that require approval before release.",
  },
];

const workflowStages = [
  "Research",
  "Series Plan",
  "Draft",
  "Review",
  "Improve",
  "Assets",
  "Approval",
  "Publish",
];

export default function Home() {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [form, setForm] = useState<LaunchForm>(initialForm);
  const [activeTask, setActiveTask] = useState<TaskSummary | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [latest, setLatest] = useState<SeriesLatestResponse | null>(null);
  const [blogPartId, setBlogPartId] = useState("Part-1-introduction");
  const [blogArtifacts, setBlogArtifacts] = useState<BlogArtifactsResponse | null>(null);
  const [memory, setMemory] = useState<MemorySkillsResponse | null>(null);
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [retrieval, setRetrieval] = useState<RetrievalPreviewResponse | null>(null);
  const [approvalStatus, setApprovalStatus] = useState("approved");
  const [approvalReviewer, setApprovalReviewer] = useState("editor");
  const [approvalComments, setApprovalComments] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    const stored = window.localStorage.getItem("blog-series-api-base");
    if (stored) setApiBase(stored);
  }, []);

  useEffect(() => {
    window.localStorage.setItem("blog-series-api-base", apiBase);
  }, [apiBase]);

  const selectedParts = useMemo(() => {
    return form.selectedParts
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isInteger(item) && item > 0);
  }, [form.selectedParts]);

  const manifest = latest?.latest_manifest ?? null;
  const artifactCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const artifact of manifest?.artifacts ?? []) {
      const key = artifact.artifact_type ?? "artifact";
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, [manifest?.artifacts]);

  async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const base = apiBase.replace(/\/$/, "");
    const response = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`);
    }
    return (await response.json()) as T;
  }

  async function runAction<T>(label: string, action: () => Promise<T>): Promise<T | null> {
    setBusy(label);
    setError("");
    setNotice("");
    try {
      const result = await action();
      setNotice(`${label} completed.`);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : `${label} failed.`);
      return null;
    } finally {
      setBusy("");
    }
  }

  function requestPayload() {
    const approvalRequired = form.runMode === "production" ? true : form.approvalRequired;
    return {
      topic: form.topic,
      target_audience: form.audience,
      num_parts: form.parts,
      selected_parts: selectedParts,
      min_word_count: form.minWords,
      max_word_count: form.maxWords,
      run_mode: form.runMode,
      approval_required: approvalRequired,
      enable_human_approval: approvalRequired,
      enable_review: true,
      enable_improve: true,
      enable_asset_plan: true,
      enable_evaluation: true,
      enable_memory: true,
      use_memory: form.useMemory,
      enable_web_search: form.webSearch,
    };
  }

  async function launchSeries(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await runAction("Series run", () =>
      apiFetch<TaskSummary>("/runs/series/async", {
        method: "POST",
        body: JSON.stringify(requestPayload()),
      }),
    );
    if (result) {
      setActiveTask(result);
      pollTask(result.task_id);
    }
  }

  async function launchOutline() {
    const result = await runAction("Outline run", () =>
      apiFetch<TaskSummary>("/runs/outline/async", {
        method: "POST",
        body: JSON.stringify({
          topic: form.topic,
          target_audience: form.audience,
          num_parts: form.parts,
          enable_web_search: form.webSearch,
        }),
      }),
    );
    if (result) {
      setActiveTask(result);
      pollTask(result.task_id);
    }
  }

  async function launchBlog() {
    const result = await runAction("Blog run", () =>
      apiFetch<TaskSummary>("/runs/blog/async", {
        method: "POST",
        body: JSON.stringify({
          topic: form.topic,
          target_audience: form.audience,
          num_parts: form.parts,
          part: form.part,
          enable_web_search: form.webSearch,
        }),
      }),
    );
    if (result) {
      setActiveTask(result);
      pollTask(result.task_id);
    }
  }

  async function pollTask(taskId: string) {
    const poll = async () => {
      const result = await apiFetch<TaskSummary>(`/tasks/${taskId}`);
      setActiveTask(result);
      await refreshTasks(false);
      if (result.status === "completed") {
        await refreshLatest(false);
        return;
      }
      if (result.status === "failed") return;
      window.setTimeout(poll, 3000);
    };
    poll().catch((err) => setError(err instanceof Error ? err.message : "Task polling failed."));
  }

  async function refreshLatest(showNotice = true) {
    const result = await runAction("Latest series refresh", () =>
      apiFetch<SeriesLatestResponse>("/series/latest"),
    );
    if (result) {
      setLatest(result);
      if (!showNotice) setNotice("");
    }
  }

  async function refreshTasks(showNotice = true) {
    const result = await runAction("Task refresh", () =>
      apiFetch<{ tasks: TaskSummary[] }>("/tasks"),
    );
    if (result) {
      setTasks(result.tasks);
      if (!showNotice) setNotice("");
    }
  }

  async function loadBlogArtifacts() {
    const result = await runAction("Blog artifact lookup", () =>
      apiFetch<BlogArtifactsResponse>(`/blogs/${encodeURIComponent(blogPartId)}`),
    );
    if (result) setBlogArtifacts(result);
  }

  async function submitApproval() {
    const result = await runAction("Approval submission", () =>
      apiFetch<BlogArtifactsResponse>(`/approval/${encodeURIComponent(blogPartId)}`, {
        method: "POST",
        body: JSON.stringify({
          status: approvalStatus,
          reviewer_name: approvalReviewer,
          comments: approvalComments,
        }),
      }),
    );
    if (result) setBlogArtifacts(result);
  }

  async function refreshMemory() {
    const [skills, feedbackResult] = await Promise.all([
      runAction("Skill memory refresh", () => apiFetch<MemorySkillsResponse>("/memory/skills")),
      runAction("Feedback refresh", () => apiFetch<{ feedback: FeedbackItem[] }>("/feedback")),
    ]);
    if (skills) setMemory(skills);
    if (feedbackResult) setFeedback(feedbackResult.feedback);
  }

  async function previewRetrieval() {
    const params = new URLSearchParams({
      topic: form.topic,
      audience: form.audience,
      part_number: String(form.part),
      artifact_type: "draft",
    });
    const result = await runAction("Retrieval preview", () =>
      apiFetch<RetrievalPreviewResponse>(`/memory/retrieval-preview?${params}`),
    );
    if (result) setRetrieval(result);
  }

  async function updateSkill(skillId: string, action: "approve" | "reject") {
    await runAction(`Skill ${action}`, () =>
      apiFetch(`/memory/${encodeURIComponent(skillId)}/${action}`, { method: "POST" }),
    );
    await refreshMemory();
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[var(--background)] text-[#211d18]">
      <div className="pointer-events-none fixed inset-0 opacity-90">
        <div className="absolute left-[-12%] top-[-18%] h-[560px] w-[560px] rounded-full bg-[#df5d36]/24 blur-3xl" />
        <div className="absolute bottom-[-24%] right-[-12%] h-[680px] w-[680px] rounded-full bg-[#0d615d]/22 blur-3xl" />
        <div className="absolute left-[28%] top-[18%] h-[430px] w-[430px] rounded-full bg-[#efb749]/24 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-6 sm:px-8 lg:px-10">
        <nav className="flex flex-wrap items-center justify-between gap-4 rounded-full border border-[#211d18]/10 bg-[#fffaf0]/70 px-5 py-3 shadow-[0_16px_50px_rgba(33,29,24,0.08)] backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-full bg-[#211d18] text-sm font-black text-[#fffaf0]">
              BG
            </div>
            <div>
              <p className="text-sm font-black">Agentic Blog Generator</p>
              <p className="text-xs text-[#74695d]">LangGraph · DeepAgents · Human gates</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-black uppercase tracking-[0.18em] text-[#6b5f52]">
            <span className="rounded-full bg-[#125d58]/10 px-3 py-2 text-[#125d58]">Research-backed</span>
            <span className="rounded-full bg-[#e6693f]/10 px-3 py-2 text-[#9b442c]">Approval-first</span>
            <span className="rounded-full bg-[#f2bd52]/20 px-3 py-2 text-[#765113]">Memory-visible</span>
          </div>
        </nav>

        <header className="hero-shell grid gap-6 p-6 md:grid-cols-[1.35fr_0.65fr] md:p-8">
          <div>
            <p className="mb-5 inline-flex rounded-full border border-[#211d18]/15 bg-[#fffaf0]/70 px-4 py-1 text-xs font-black uppercase tracking-[0.24em] text-[#9b442c]">
              Content operations cockpit
            </p>
            <h1 className="max-w-4xl text-4xl font-black tracking-[-0.055em] text-[#211d18] sm:text-6xl">
              Generate book-like technical series with visible agent work.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-[#5f554a]">
              Inspired by workflow builders, observability tools, and content operation
              platforms: launch a run, inspect every artifact, evaluate quality, apply
              reusable skills, then approve chapters for publishing.
            </p>
            <div className="mt-7 grid gap-3 md:grid-cols-3">
              {inspirationCards.map((card) => (
                <InspirationCard key={card.title} {...card} />
              ))}
            </div>
          </div>
          <div className="space-y-4">
            <ApiEndpointCard apiBase={apiBase} setApiBase={setApiBase} />
            <ContractCard />
          </div>
        </header>

        {(error || notice || busy) && (
          <section className="grid gap-3 md:grid-cols-3">
            {busy && <StatusPill tone="amber" label="Working" value={busy} />}
            {notice && <StatusPill tone="green" label="Last event" value={notice} />}
            {error && <StatusPill tone="red" label="Error" value={error} />}
          </section>
        )}

        <section className="grid gap-6 lg:grid-cols-[1fr_390px]">
          <WorkflowMap activeTask={activeTask} manifest={manifest} />
          <ReadinessPanel
            manifest={manifest}
            latest={latest}
            blogArtifacts={blogArtifacts}
            memory={memory}
            feedbackCount={feedback.length}
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-[420px_1fr]">
          <Panel title="Start a Run" eyebrow="Generation">
            <form onSubmit={launchSeries} className="space-y-4">
              <Field label="Topic">
                <input
                  className="input"
                  value={form.topic}
                  onChange={(event) => setForm({ ...form, topic: event.target.value })}
                />
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Audience">
                  <select
                    className="input"
                    value={form.audience}
                    onChange={(event) => setForm({ ...form, audience: event.target.value })}
                  >
                    <option>beginner</option>
                    <option>intermediate</option>
                    <option>advanced</option>
                  </select>
                </Field>
                <Field label="Parts">
                  <input
                    className="input"
                    type="number"
                    min={1}
                    max={20}
                    value={form.parts}
                    onChange={(event) => setForm({ ...form, parts: Number(event.target.value) })}
                  />
                </Field>
              </div>
              <Field label="Selected parts for series run">
                <input
                  className="input font-mono"
                  placeholder="1,2,3"
                  value={form.selectedParts}
                  onChange={(event) => setForm({ ...form, selectedParts: event.target.value })}
                />
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Min words">
                  <input
                    className="input"
                    type="number"
                    min={300}
                    value={form.minWords}
                    onChange={(event) => setForm({ ...form, minWords: Number(event.target.value) })}
                  />
                </Field>
                <Field label="Max words">
                  <input
                    className="input"
                    type="number"
                    min={form.minWords}
                    value={form.maxWords}
                    onChange={(event) => setForm({ ...form, maxWords: Number(event.target.value) })}
                  />
                </Field>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Run mode">
                  <select
                    className="input"
                    value={form.runMode}
                    onChange={(event) =>
                      setForm({ ...form, runMode: event.target.value as LaunchForm["runMode"] })
                    }
                  >
                    <option value="dev">dev</option>
                    <option value="review">review</option>
                    <option value="production">production</option>
                  </select>
                </Field>
                <Field label="Single blog part">
                  <input
                    className="input"
                    type="number"
                    min={1}
                    value={form.part}
                    onChange={(event) => setForm({ ...form, part: Number(event.target.value) })}
                  />
                </Field>
              </div>
              <div className="grid gap-3 text-sm sm:grid-cols-3">
                <Toggle
                  label="Use memory"
                  checked={form.useMemory}
                  onChange={(checked) => setForm({ ...form, useMemory: checked })}
                />
                <Toggle
                  label="Web search"
                  checked={form.webSearch}
                  onChange={(checked) => setForm({ ...form, webSearch: checked })}
                />
                <Toggle
                  label="Approval gate"
                  checked={form.approvalRequired || form.runMode === "production"}
                  disabled={form.runMode === "production"}
                  onChange={(checked) => setForm({ ...form, approvalRequired: checked })}
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <button className="button-primary" type="submit">
                  Series
                </button>
                <button className="button-secondary" type="button" onClick={launchOutline}>
                  Outline
                </button>
                <button className="button-secondary" type="button" onClick={launchBlog}>
                  Blog
                </button>
              </div>
            </form>
          </Panel>

          <div className="grid gap-6">
            <section className="grid gap-6 xl:grid-cols-3">
              <MetricCard label="Active task" value={activeTask?.task_id ?? "none"} detail={activeTask?.status ?? "idle"} />
              <MetricCard label="Latest run" value={manifest?.run_id ?? "none"} detail={manifest?.status ?? "not loaded"} />
              <MetricCard
                label="Artifacts"
                value={String(manifest?.artifacts?.length ?? 0)}
                detail={Object.entries(artifactCounts)
                  .map(([key, value]) => `${key}: ${value}`)
                  .join(" / ") || "no manifest"}
              />
            </section>

            <Panel title="Run & Artifact Inspector" eyebrow="Operations">
              <div className="mb-4 flex flex-wrap gap-3">
                <button className="button-secondary" type="button" onClick={() => refreshLatest()}>
                  Refresh latest
                </button>
                <button className="button-secondary" type="button" onClick={() => refreshTasks()}>
                  Refresh tasks
                </button>
              </div>
              <div className="grid gap-5 xl:grid-cols-2">
                <div className="rounded-3xl bg-[#fffaf0] p-4">
                  <h3 className="section-title">Latest Manifest</h3>
                  {manifest ? (
                    <div className="space-y-2 text-sm text-[#5f554a]">
                      <p><strong>Topic:</strong> {manifest.topic}</p>
                      <p><strong>Audience:</strong> {manifest.target_audience}</p>
                      <p><strong>Parts:</strong> {manifest.num_parts}</p>
                      <p><strong>Outline:</strong> {latest?.latest_outline_path ?? "not available"}</p>
                      {latest?.latest_series_evaluation?.overall_score !== undefined && (
                        <p>
                          <strong>Series score:</strong>{" "}
                          {latest.latest_series_evaluation.overall_score}/10
                        </p>
                      )}
                    </div>
                  ) : (
                    <EmptyState text="No latest manifest loaded." />
                  )}
                </div>
                <div className="rounded-3xl bg-[#fffaf0] p-4">
                  <h3 className="section-title">Recent Tasks</h3>
                  {tasks.length ? (
                    <div className="max-h-56 space-y-2 overflow-y-auto pr-2">
                      {tasks.map((task) => (
                        <div key={task.task_id} className="rounded-2xl border border-[#211d18]/10 p-3 text-sm">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-mono text-xs">{task.task_id}</span>
                            <span className="rounded-full bg-[#125d58]/10 px-2 py-1 text-xs font-bold text-[#125d58]">
                              {task.status}
                            </span>
                          </div>
                          {task.error && <p className="mt-2 text-[#b5362b]">{task.error}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState text="No background tasks loaded." />
                  )}
                </div>
              </div>
            </Panel>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_420px]">
          <Panel title="Blog Approval Workbench" eyebrow="Human in the loop">
            <div className="grid gap-4 md:grid-cols-[1fr_auto]">
              <Field label="Part ID">
                <input
                  className="input font-mono"
                  value={blogPartId}
                  onChange={(event) => setBlogPartId(event.target.value)}
                />
              </Field>
              <button className="button-secondary self-end" type="button" onClick={loadBlogArtifacts}>
                Load blog
              </button>
            </div>
            {blogArtifacts ? (
              <div className="mt-5 grid gap-5 xl:grid-cols-2">
                <div>
                  <h3 className="section-title">Artifacts</h3>
                  <ArtifactList artifacts={blogArtifacts.artifacts} />
                </div>
                <div className="space-y-4">
                  <h3 className="section-title">Approval</h3>
                  <div className="rounded-3xl bg-[#fffaf0] p-4 text-sm text-[#5f554a]">
                    <p><strong>Current status:</strong> {blogArtifacts.approval?.status ?? "not submitted"}</p>
                    {blogArtifacts.evaluation && (
                      <p className="mt-2">
                        <strong>Evaluation:</strong> {blogArtifacts.evaluation.overall_score ?? "n/a"}/10,
                        skill adherence {blogArtifacts.evaluation.skill_adherence_score ?? "n/a"}/10
                      </p>
                    )}
                  </div>
                  <div className="grid gap-3">
                    <Field label="Decision">
                      <select
                        className="input"
                        value={approvalStatus}
                        onChange={(event) => setApprovalStatus(event.target.value)}
                      >
                        {approvalOptions.map((option) => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </Field>
                    <Field label="Reviewer">
                      <input
                        className="input"
                        value={approvalReviewer}
                        onChange={(event) => setApprovalReviewer(event.target.value)}
                      />
                    </Field>
                    <Field label="Comments">
                      <textarea
                        className="input min-h-24"
                        value={approvalComments}
                        onChange={(event) => setApprovalComments(event.target.value)}
                      />
                    </Field>
                    <button className="button-primary" type="button" onClick={submitApproval}>
                      Submit approval
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState text="Load a part ID to inspect artifacts and submit an approval decision." />
            )}
          </Panel>

          <Panel title="Memory & Skills" eyebrow="Learning loop">
            <div className="mb-4 flex flex-wrap gap-3">
              <button className="button-secondary" type="button" onClick={refreshMemory}>
                Refresh memory
              </button>
              <button className="button-secondary" type="button" onClick={previewRetrieval}>
                Preview retrieval
              </button>
            </div>

            {retrieval && (
              <div className="mb-4 rounded-3xl bg-[#125d58] p-4 text-sm text-white">
                <p className="font-bold">Retrieved skills</p>
                <p className="mt-2 font-mono text-xs">{retrieval.retrieval.retrieved_skill_ids.join(", ") || "none"}</p>
                <ul className="mt-3 list-inside list-disc space-y-1 text-[#d8eee9]">
                  {retrieval.retrieval.retrieved_guidance.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="space-y-4">
              <SkillGroup
                title="Approved skills"
                skills={memory?.approved_skills ?? []}
              />
              <SkillGroup
                title="Candidate skills"
                skills={memory?.candidate_skills ?? []}
                onApprove={(skillId) => updateSkill(skillId, "approve")}
                onReject={(skillId) => updateSkill(skillId, "reject")}
              />
              <div>
                <h3 className="section-title">Raw feedback</h3>
                {feedback.length ? (
                  <div className="max-h-72 space-y-2 overflow-y-auto pr-2">
                    {feedback.slice(0, 8).map((item) => (
                      <div key={item.feedback_id} className="rounded-2xl border border-[#211d18]/10 bg-[#fffaf0] p-3 text-sm">
                        <p className="font-bold">{item.normalized_issue_type} · {item.severity}</p>
                        <p className="mt-1 text-[#5f554a]">{item.raw_feedback}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState text="No feedback loaded." />
                )}
              </div>
            </div>
          </Panel>
        </section>
      </div>
    </main>
  );
}

function ApiEndpointCard({
  apiBase,
  setApiBase,
}: {
  apiBase: string;
  setApiBase: (value: string) => void;
}) {
  return (
    <div className="rounded-[1.5rem] bg-[#211d18] p-5 text-[#fffaf0] shadow-[0_20px_60px_rgba(33,29,24,0.22)]">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-[#f2bd52]">
        API Endpoint
      </p>
      <label className="mt-4 block text-sm text-[#efe4cf]">
        FastAPI base URL
        <input
          className="mt-2 w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 font-mono text-sm text-white outline-none ring-[#f2bd52] focus:ring-2"
          value={apiBase}
          onChange={(event) => setApiBase(event.target.value)}
        />
      </label>
      <p className="mt-3 text-xs leading-5 text-[#cfc4ad]">
        For local use, run `uv run python -m blog_series_agent api`. For deployed
        use, point this at a hosted FastAPI backend.
      </p>
    </div>
  );
}

function ContractCard() {
  const items = [
    "Clickable sources per section",
    "Draft, review, final, assets",
    "Evaluation and skill adherence",
    "Human approval before publishing",
  ];
  return (
    <div className="rounded-[1.5rem] border border-[#211d18]/10 bg-[#fffaf0]/78 p-5 shadow-[0_18px_50px_rgba(33,29,24,0.10)]">
      <p className="text-xs font-black uppercase tracking-[0.2em] text-[#9b442c]">
        Artifact contract
      </p>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={item} className="flex items-center gap-3 text-sm font-bold text-[#463d34]">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-[#125d58] text-xs text-white">
              ✓
            </span>
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function InspirationCard({
  title,
  source,
  detail,
}: {
  title: string;
  source: string;
  detail: string;
}) {
  return (
    <div className="rounded-3xl border border-[#211d18]/10 bg-[#fffaf0]/72 p-4 shadow-[0_12px_35px_rgba(33,29,24,0.08)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[#9b442c]">{source}</p>
      <p className="mt-2 text-base font-black text-[#211d18]">{title}</p>
      <p className="mt-2 text-sm leading-6 text-[#63584d]">{detail}</p>
    </div>
  );
}

function WorkflowMap({
  activeTask,
  manifest,
}: {
  activeTask: TaskSummary | null;
  manifest: RunManifest | null;
}) {
  const completed = manifest?.status === "completed";
  const running = activeTask && !["completed", "failed"].includes(activeTask.status);
  const activeIndex = completed ? workflowStages.length - 1 : running ? 2 : 0;

  return (
    <section className="workflow-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.24em] text-[#9b442c]">
            Agent workflow
          </p>
          <h2 className="mt-2 text-2xl font-black tracking-[-0.03em]">
            From grounded research to publish-ready chapter
          </h2>
        </div>
        <span className="rounded-full bg-[#211d18] px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-[#fffaf0]">
          {activeTask?.status ?? manifest?.status ?? "idle"}
        </span>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        {workflowStages.map((stage, index) => {
          const state = completed || index < activeIndex ? "done" : index === activeIndex ? "active" : "queued";
          return (
            <div key={stage} className={`workflow-node workflow-node-${state}`}>
              <span className="font-mono text-xs">{String(index + 1).padStart(2, "0")}</span>
              <p className="mt-2 font-black">{stage}</p>
              <p className="mt-1 text-xs">
                {state === "done" ? "Complete" : state === "active" ? "In motion" : "Queued"}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function ReadinessPanel({
  manifest,
  latest,
  blogArtifacts,
  memory,
  feedbackCount,
}: {
  manifest: RunManifest | null;
  latest: SeriesLatestResponse | null;
  blogArtifacts: BlogArtifactsResponse | null;
  memory: MemorySkillsResponse | null;
  feedbackCount: number;
}) {
  const approvedSkills = memory?.approved_skills.length ?? 0;
  const candidateSkills = memory?.candidate_skills.length ?? 0;
  const approvalStatus = blogArtifacts?.approval?.status ?? "not loaded";
  const seriesScore = latest?.latest_series_evaluation?.overall_score;
  const blogScore = blogArtifacts?.evaluation?.overall_score;

  return (
    <section className="rounded-[2rem] border border-[#211d18]/10 bg-[#211d18] p-5 text-[#fffaf0] shadow-[0_24px_70px_rgba(33,29,24,0.18)]">
      <p className="text-xs font-black uppercase tracking-[0.24em] text-[#f2bd52]">
        Release readiness
      </p>
      <h2 className="mt-2 text-2xl font-black tracking-[-0.03em]">Quality cockpit</h2>
      <div className="mt-5 grid gap-3">
        <ReadinessItem label="Run state" value={manifest?.status ?? "No manifest"} />
        <ReadinessItem label="Series eval" value={seriesScore === undefined ? "Not loaded" : `${seriesScore}/10`} />
        <ReadinessItem label="Blog eval" value={blogScore === undefined ? "Not loaded" : `${blogScore}/10`} />
        <ReadinessItem label="Approval" value={approvalStatus} />
        <ReadinessItem label="Approved skills" value={String(approvedSkills)} />
        <ReadinessItem label="Candidate skills" value={String(candidateSkills)} />
        <ReadinessItem label="Raw feedback" value={String(feedbackCount)} />
      </div>
    </section>
  );
}

function ReadinessItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/10 bg-white/[0.08] px-4 py-3 text-sm">
      <span className="text-[#d9cfbb]">{label}</span>
      <span className="font-mono font-black text-[#fffaf0]">{value}</span>
    </div>
  );
}

function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-[#211d18]/10 bg-white/65 p-5 shadow-[0_18px_70px_rgba(33,29,24,0.10)] backdrop-blur md:p-6">
      <p className="text-xs font-black uppercase tracking-[0.24em] text-[#9b442c]">{eyebrow}</p>
      <h2 className="mb-5 mt-2 text-2xl font-black tracking-[-0.03em]">{title}</h2>
      {children}
    </section>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-bold text-[#463d34]">
      {label}
      <div className="mt-2">{children}</div>
    </label>
  );
}

function Toggle({
  label,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex items-center justify-between rounded-2xl border border-[#211d18]/10 bg-[#fffaf0] px-3 py-2 font-bold text-[#463d34]">
      {label}
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-[1.75rem] border border-[#211d18]/10 bg-[#211d18] p-5 text-[#fffaf0] shadow-xl">
      <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#f2bd52]">{label}</p>
      <p className="mt-3 truncate font-mono text-xl font-bold">{value}</p>
      <p className="mt-2 line-clamp-2 text-sm text-[#d8d0c2]">{detail}</p>
    </div>
  );
}

function StatusPill({ tone, label, value }: { tone: "amber" | "green" | "red"; label: string; value: string }) {
  const classes = {
    amber: "border-[#f2bd52]/50 bg-[#f2bd52]/20 text-[#6c4912]",
    green: "border-[#125d58]/30 bg-[#125d58]/10 text-[#125d58]",
    red: "border-[#b5362b]/30 bg-[#b5362b]/10 text-[#8f251d]",
  };
  return (
    <div className={`rounded-2xl border px-4 py-3 text-sm ${classes[tone]}`}>
      <strong>{label}:</strong> {value}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-[#211d18]/20 bg-[#fffaf0]/60 p-5 text-center text-sm text-[#7a6f62]">
      {text}
    </div>
  );
}

function ArtifactList({ artifacts }: { artifacts: ArtifactRecord[] }) {
  if (!artifacts.length) return <EmptyState text="No artifacts found for this part." />;
  return (
    <div className="max-h-96 space-y-2 overflow-y-auto pr-2">
      {artifacts.map((artifact) => (
        <div key={`${artifact.artifact_type}-${artifact.path}`} className="rounded-2xl border border-[#211d18]/10 bg-[#fffaf0] p-3 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="rounded-full bg-[#e6693f]/10 px-2 py-1 text-xs font-black uppercase text-[#9b442c]">
              {artifact.artifact_type ?? "artifact"}
            </span>
            {artifact.part_number && <span className="text-xs text-[#7a6f62]">Part {artifact.part_number}</span>}
          </div>
          <p className="mt-2 break-all font-mono text-xs text-[#5f554a]">{artifact.path}</p>
        </div>
      ))}
    </div>
  );
}

function SkillGroup({
  title,
  skills,
  onApprove,
  onReject,
}: {
  title: string;
  skills: Skill[];
  onApprove?: (skillId: string) => void;
  onReject?: (skillId: string) => void;
}) {
  return (
    <div>
      <h3 className="section-title">{title}</h3>
      {skills.length ? (
        <div className="max-h-80 space-y-2 overflow-y-auto pr-2">
          {skills.map((skill) => (
            <div key={skill.id} className="rounded-2xl border border-[#211d18]/10 bg-[#fffaf0] p-3 text-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-black">{skill.title}</p>
                  <p className="mt-1 font-mono text-xs text-[#7a6f62]">{skill.id}</p>
                </div>
                <span className="rounded-full bg-[#125d58]/10 px-2 py-1 text-xs font-bold text-[#125d58]">
                  {skill.status}
                </span>
              </div>
              <p className="mt-2 text-[#5f554a]">{skill.guidance_text}</p>
              {(onApprove || onReject) && (
                <div className="mt-3 flex gap-2">
                  {onApprove && (
                    <button className="mini-button" type="button" onClick={() => onApprove(skill.id)}>
                      Approve
                    </button>
                  )}
                  {onReject && (
                    <button className="mini-button" type="button" onClick={() => onReject(skill.id)}>
                      Reject
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState text={`No ${title.toLowerCase()} loaded.`} />
      )}
    </div>
  );
}
