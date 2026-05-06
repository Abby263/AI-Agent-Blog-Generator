export const DEFAULT_API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const GITHUB_REPOSITORY_URL =
  "https://github.com/Abby263/ai-agent-blog-generator";

/* ---------- Domain types (mirroring the FastAPI surface) ---------- */

export type ArtifactRecord = {
  artifact_id?: string;
  artifact_type?: string;
  path: string;
  part_number?: number | null;
  created_at?: string;
};

export type RunManifest = {
  run_id: string;
  topic: string;
  target_audience: string;
  num_parts: number;
  status: string;
  artifacts: ArtifactRecord[];
  selected_parts?: number[];
  part_statuses?: Record<string, string>;
};

export type TaskSummary = {
  task_id: string;
  status: string;
  message?: string;
  created_at?: string;
  completed_at?: string | null;
  error?: string | null;
};

export type SeriesEvaluation = {
  overall_score?: number;
  summary?: string;
};

export type BlogEvaluation = {
  overall_score?: number;
  skill_adherence_score?: number;
  summary?: string;
};

export type SeriesLatestResponse = {
  latest_outline_path?: string | null;
  latest_manifest?: RunManifest | null;
  latest_series_evaluation?: SeriesEvaluation | null;
};

export type ApprovalRecord = {
  status: string;
  comments?: string;
  reviewer_name?: string;
  timestamp?: string;
};

export type BlogArtifactsResponse = {
  part_id: string;
  artifacts: ArtifactRecord[];
  approval?: ApprovalRecord | null;
  evaluation?: BlogEvaluation | null;
};

export type Skill = {
  id: string;
  title: string;
  category?: string;
  guidance_text: string;
  status: string;
  active: boolean;
  usage_count?: number;
};

export type MemorySkillsResponse = {
  candidate_skills: Skill[];
  approved_skills: Skill[];
};

export type FeedbackItem = {
  feedback_id: string;
  raw_feedback: string;
  normalized_issue_type: string;
  severity: string;
  reviewer: string;
  source_artifact: string;
};

export type RetrievalPreviewResponse = {
  retrieval: {
    retrieved_skill_ids: string[];
    retrieved_guidance: string[];
    retrieval_notes: string[];
  };
};

/* ---------- Run-launch payload ---------- */

export type RunMode = "dev" | "review" | "production";
export type ContentFormat = "series" | "report" | "research" | "tutorial";

export type LaunchSettings = {
  topic: string;
  audience: string;
  parts: number;
  selectedParts: number[];
  part: number;
  minWords: number;
  maxWords: number;
  runMode: RunMode;
  approvalRequired: boolean;
  useMemory: boolean;
  webSearch: boolean;
  format: ContentFormat;
};

export const defaultLaunchSettings: LaunchSettings = {
  topic: "ML System Design",
  audience: "intermediate",
  parts: 12,
  selectedParts: [1, 2, 3],
  part: 1,
  minWords: 2000,
  maxWords: 3000,
  runMode: "dev",
  approvalRequired: false,
  useMemory: true,
  webSearch: true,
  format: "series",
};

export function buildSeriesPayload(form: LaunchSettings) {
  const approvalRequired =
    form.runMode === "production" ? true : form.approvalRequired;
  return {
    topic: form.topic,
    target_audience: form.audience,
    num_parts: form.parts,
    selected_parts: form.selectedParts,
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

export function buildOutlinePayload(form: LaunchSettings) {
  return {
    topic: form.topic,
    target_audience: form.audience,
    num_parts: form.parts,
    enable_web_search: form.webSearch,
  };
}

export function buildBlogPayload(form: LaunchSettings) {
  return {
    topic: form.topic,
    target_audience: form.audience,
    num_parts: form.parts,
    part: form.part,
    enable_web_search: form.webSearch,
  };
}

/* ---------- Fetch helper ---------- */

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  apiBase: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const base = (apiBase || DEFAULT_API_BASE).replace(/\/$/, "");
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText}${text ? ": " + text : ""}`,
    );
  }
  return (await response.json()) as T;
}

export const APPROVAL_OPTIONS = [
  "approved",
  "approved_with_notes",
  "changes_requested",
  "rejected",
] as const;

export const WORKFLOW_STAGES: Array<{ name: string; detail: string }> = [
  { name: "Research", detail: "Grounded sources gathered for the topic." },
  { name: "Series Plan", detail: "Architecture and table of contents drafted." },
  { name: "Draft", detail: "Each chapter written with examples and structure." },
  { name: "Review", detail: "Automated quality, lint, and skill-adherence checks." },
  { name: "Improve", detail: "Reviewer feedback applied; revisions issued." },
  { name: "Assets", detail: "Source list, visuals, and code blocks finalised." },
  { name: "Approval", detail: "Human reviewer decides go/no-go." },
  { name: "Publish", detail: "Manuscripts ready for distribution." },
];
