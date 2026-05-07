"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Badge,
  Button,
  Card,
  Field,
  HelpText,
  KeyValue,
  PageHeader,
  Toggle,
} from "@/components/ui";
import {
  ArrowRightIcon,
  BookOpenIcon,
  CheckIcon,
  FileTextIcon,
  FlaskIcon,
  GraphIcon,
  SparkIcon,
} from "@/components/icons";
import { useApp } from "@/lib/context";
import {
  type ContentFormat,
  type LaunchSettings,
  type TaskSummary,
  buildBlogPayload,
  buildOutlinePayload,
  buildSeriesPayload,
} from "@/lib/api";

type StepId = "format" | "brief" | "structure" | "pipeline" | "review";

const STEPS: Array<{
  id: StepId;
  label: string;
  helper: string;
}> = [
  { id: "format", label: "Format", helper: "What are you publishing?" },
  { id: "brief", label: "Brief", helper: "Topic and audience." },
  { id: "structure", label: "Structure", helper: "Length and parts." },
  { id: "pipeline", label: "Pipeline", helper: "Run mode and gates." },
  { id: "review", label: "Review & launch", helper: "Confirm, then submit." },
];

const FORMAT_OPTIONS: Array<{
  id: ContentFormat;
  label: string;
  description: string;
  icon: typeof BookOpenIcon;
  recommended: { parts: number; minWords: number; maxWords: number };
}> = [
  {
    id: "series",
    label: "Book or blog series",
    description:
      "A 10–14 chapter manuscript with a coherent narrative across parts.",
    icon: BookOpenIcon,
    recommended: { parts: 12, minWords: 2000, maxWords: 3000 },
  },
  {
    id: "report",
    label: "Long-form report",
    description:
      "Sectioned report with grounded citations, ready for distribution.",
    icon: FileTextIcon,
    recommended: { parts: 6, minWords: 1500, maxWords: 2500 },
  },
  {
    id: "research",
    label: "Research paper",
    description:
      "Structured paper with literature, methodology, results, discussion.",
    icon: FlaskIcon,
    recommended: { parts: 5, minWords: 1800, maxWords: 2800 },
  },
  {
    id: "tutorial",
    label: "Technical blog series",
    description:
      "Code-heavy posts with diagrams, examples, and hands-on walkthroughs.",
    icon: GraphIcon,
    recommended: { parts: 8, minWords: 1500, maxWords: 2400 },
  },
];

export default function ComposePage() {
  const router = useRouter();
  const { draft, setDraft, fetchJson, runWithBusy, busy, pushToast } = useApp();
  const [stepIndex, setStepIndex] = useState(0);

  const currentStep = STEPS[stepIndex];

  const selectedFormat = useMemo(
    () => FORMAT_OPTIONS.find((opt) => opt.id === draft.format) ?? FORMAT_OPTIONS[0],
    [draft.format],
  );

  const canAdvance = useMemo(() => {
    if (currentStep.id === "brief") {
      return draft.topic.trim().length > 2;
    }
    if (currentStep.id === "structure") {
      return draft.parts >= 1 && draft.maxWords >= draft.minWords;
    }
    return true;
  }, [currentStep.id, draft.topic, draft.parts, draft.minWords, draft.maxWords]);

  const back = () => setStepIndex((idx) => Math.max(0, idx - 1));
  const next = () =>
    setStepIndex((idx) => Math.min(STEPS.length - 1, idx + 1));

  async function launch(kind: "series" | "outline" | "blog") {
    const path =
      kind === "series"
        ? "/runs/series/async"
        : kind === "outline"
          ? "/runs/outline/async"
          : "/runs/blog/async";
    const body =
      kind === "series"
        ? buildSeriesPayload(draft)
        : kind === "outline"
          ? buildOutlinePayload(draft)
          : buildBlogPayload(draft);
    const result = await runWithBusy(`Launching ${kind} run`, () =>
      fetchJson<TaskSummary>(path, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    );
    if (result) {
      pushToast(
        "info",
        `Task ${result.task_id} queued. Track progress on the dashboard.`,
      );
      router.push("/dashboard");
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Compose"
        title="Brief the agents"
        description="Define what to publish, how it should be structured, and which gates the pipeline should respect."
      />

      <Stepper steps={STEPS} currentIndex={stepIndex} onJump={setStepIndex} />

      <div className="grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start">
        <Card>
          {currentStep.id === "format" && (
            <FormatStep
              draft={draft}
              setDraft={setDraft}
            />
          )}
          {currentStep.id === "brief" && (
            <BriefStep draft={draft} setDraft={setDraft} />
          )}
          {currentStep.id === "structure" && (
            <StructureStep
              draft={draft}
              setDraft={setDraft}
              recommended={selectedFormat.recommended}
            />
          )}
          {currentStep.id === "pipeline" && (
            <PipelineStep draft={draft} setDraft={setDraft} />
          )}
          {currentStep.id === "review" && (
            <ReviewStep
              draft={draft}
              format={selectedFormat}
              busy={Boolean(busy)}
              onLaunch={launch}
            />
          )}

          <div className="hairline-top mt-7 flex flex-wrap items-center justify-between gap-3 pt-5">
            <Button
              variant="ghost"
              onClick={back}
              disabled={stepIndex === 0}
            >
              Back
            </Button>
            <div className="text-xs text-ink-500">
              Step {stepIndex + 1} of {STEPS.length}
            </div>
            {currentStep.id !== "review" ? (
              <Button
                variant="primary"
                onClick={next}
                disabled={!canAdvance}
                trailingIcon={<ArrowRightIcon className="h-4 w-4" />}
              >
                Continue
              </Button>
            ) : (
              <Button
                variant="accent"
                onClick={() => launch("series")}
                disabled={Boolean(busy)}
                trailingIcon={<SparkIcon className="h-4 w-4" />}
              >
                Launch run
              </Button>
            )}
          </div>
        </Card>

        <SummaryRail draft={draft} format={selectedFormat} />
      </div>
    </div>
  );
}

function Stepper({
  steps,
  currentIndex,
  onJump,
}: {
  steps: typeof STEPS;
  currentIndex: number;
  onJump: (index: number) => void;
}) {
  return (
    <ol className="grid gap-2 sm:grid-cols-5">
      {steps.map((step, index) => {
        const state =
          index < currentIndex
            ? "done"
            : index === currentIndex
              ? "active"
              : "queued";
        return (
          <li key={step.id}>
            <button
              type="button"
              onClick={() => onJump(index)}
              className={`flex w-full items-start gap-3 rounded-lg border px-3 py-2.5 text-left transition ${
                state === "active"
                  ? "border-ink-900 bg-surface shadow-sm"
                  : state === "done"
                    ? "border-border bg-surface"
                    : "border-border bg-canvas hover:border-border-strong"
              }`}
            >
              <span
                className={`grid h-6 w-6 shrink-0 place-items-center rounded-full font-mono text-[11px] ${
                  state === "active"
                    ? "bg-ink-900 text-feature"
                    : state === "done"
                      ? "bg-success text-on-accent"
                      : "bg-canvas-2 text-ink-500"
                }`}
              >
                {state === "done" ? (
                  <CheckIcon className="h-3.5 w-3.5" />
                ) : (
                  index + 1
                )}
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-medium text-ink-800">
                  {step.label}
                </span>
                <span className="block truncate text-xs text-ink-500">
                  {step.helper}
                </span>
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function FormatStep({
  draft,
  setDraft,
}: {
  draft: LaunchSettings;
  setDraft: ReturnType<typeof useApp>["setDraft"];
}) {
  return (
    <div>
      <StepHeading
        title="What format are you producing?"
        description="The pipeline supports several long-form formats. Choosing one preloads sensible defaults you can override later."
      />
      <div className="grid gap-3 md:grid-cols-2">
        {FORMAT_OPTIONS.map((option) => {
          const Icon = option.icon;
          const active = draft.format === option.id;
          return (
            <button
              type="button"
              key={option.id}
              onClick={() =>
                setDraft({
                  format: option.id,
                  parts: option.recommended.parts,
                  minWords: option.recommended.minWords,
                  maxWords: option.recommended.maxWords,
                })
              }
              className={`flex items-start gap-4 rounded-xl border p-4 text-left transition ${
                active
                  ? "border-accent bg-accent-soft/40 shadow-sm"
                  : "border-border bg-surface hover:border-border-strong"
              }`}
            >
              <span
                className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${
                  active
                    ? "bg-accent text-feature"
                    : "bg-canvas-2 text-ink-700"
                }`}
              >
                <Icon className="h-5 w-5" />
              </span>
              <span>
                <span className="block font-display text-base font-medium tracking-tight">
                  {option.label}
                </span>
                <span className="mt-1 block text-sm text-ink-500">
                  {option.description}
                </span>
                <span className="mt-2 block text-xs text-ink-400">
                  Default: {option.recommended.parts} parts ·{" "}
                  {option.recommended.minWords}–{option.recommended.maxWords} words each
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function BriefStep({
  draft,
  setDraft,
}: {
  draft: LaunchSettings;
  setDraft: ReturnType<typeof useApp>["setDraft"];
}) {
  return (
    <div>
      <StepHeading
        title="What is the manuscript about?"
        description="A clear topic and target audience let the research and outline agents anchor the rest of the pipeline."
      />
      <div className="space-y-5">
        <Field label="Topic" required hint="One short phrase">
          <input
            className="input"
            placeholder="e.g. ML System Design, Modern RAG architectures…"
            value={draft.topic}
            onChange={(event) => setDraft({ topic: event.target.value })}
          />
        </Field>
        <Field label="Target audience" hint="Sets vocabulary and depth">
          <select
            className="input"
            value={draft.audience}
            onChange={(event) => setDraft({ audience: event.target.value })}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </Field>
        <HelpText>
          Want to compose a single chapter inside a larger series? You can
          target a specific part on the Pipeline step.
        </HelpText>
      </div>
    </div>
  );
}

function StructureStep({
  draft,
  setDraft,
  recommended,
}: {
  draft: LaunchSettings;
  setDraft: ReturnType<typeof useApp>["setDraft"];
  recommended: { parts: number; minWords: number; maxWords: number };
}) {
  return (
    <div>
      <StepHeading
        title="How long should the manuscript be?"
        description="Word counts apply to each chapter; the agents use them as soft targets when drafting and reviewing."
      />
      <div className="space-y-5">
        <Field
          label="Number of parts"
          hint={`Recommended: ${recommended.parts}`}
        >
          <input
            className="input"
            type="number"
            min={1}
            max={20}
            value={draft.parts}
            onChange={(event) =>
              setDraft({ parts: Number(event.target.value) })
            }
          />
        </Field>
        <Field
          label="Selected parts to draft"
          hint="Comma-separated list of chapter numbers"
        >
          <input
            className="input font-mono"
            placeholder="1,2,3"
            value={draft.selectedParts.join(",")}
            onChange={(event) =>
              setDraft({
                selectedParts: event.target.value
                  .split(",")
                  .map((item) => Number(item.trim()))
                  .filter((item) => Number.isInteger(item) && item > 0),
              })
            }
          />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            label="Minimum words per chapter"
            hint={`Recommended: ${recommended.minWords}`}
          >
            <input
              className="input"
              type="number"
              min={300}
              value={draft.minWords}
              onChange={(event) =>
                setDraft({ minWords: Number(event.target.value) })
              }
            />
          </Field>
          <Field
            label="Maximum words per chapter"
            hint={`Recommended: ${recommended.maxWords}`}
          >
            <input
              className="input"
              type="number"
              min={draft.minWords}
              value={draft.maxWords}
              onChange={(event) =>
                setDraft({ maxWords: Number(event.target.value) })
              }
            />
          </Field>
        </div>
        <Field
          label="Single-chapter target (for the blog action)"
          hint="Used when launching just one chapter"
        >
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
      </div>
    </div>
  );
}

function PipelineStep({
  draft,
  setDraft,
}: {
  draft: LaunchSettings;
  setDraft: ReturnType<typeof useApp>["setDraft"];
}) {
  return (
    <div>
      <StepHeading
        title="Choose your pipeline gates"
        description="Run mode controls how strict the system is about review and approval gates before publishing."
      />
      <div className="space-y-5">
        <Field
          label="Run mode"
          hint="Production enforces approval gates"
        >
          <div className="grid gap-2 sm:grid-cols-3">
            {(["dev", "review", "production"] as const).map((mode) => {
              const active = draft.runMode === mode;
              return (
                <button
                  type="button"
                  key={mode}
                  onClick={() => setDraft({ runMode: mode })}
                  className={`rounded-lg border px-3 py-2.5 text-left text-sm transition ${
                    active
                      ? "border-ink-900 bg-surface shadow-sm"
                      : "border-border bg-surface hover:border-border-strong"
                  }`}
                >
                  <span className="block font-medium capitalize text-ink-800">
                    {mode}
                  </span>
                  <span className="mt-0.5 block text-xs text-ink-500">
                    {mode === "dev"
                      ? "Fast iteration; gates relaxed."
                      : mode === "review"
                        ? "Review pass enabled; approval optional."
                        : "Strict gates; approval required."}
                  </span>
                </button>
              );
            })}
          </div>
        </Field>

        <div className="grid gap-3 md:grid-cols-3">
          <Toggle
            label="Use memory"
            description="Apply approved skills retrieved from past runs."
            checked={draft.useMemory}
            onChange={(value) => setDraft({ useMemory: value })}
          />
          <Toggle
            label="Web search"
            description="Allow grounded sources to be fetched."
            checked={draft.webSearch}
            onChange={(value) => setDraft({ webSearch: value })}
          />
          <Toggle
            label="Approval gate"
            description="Require human approval before publish-ready."
            checked={
              draft.approvalRequired || draft.runMode === "production"
            }
            disabled={draft.runMode === "production"}
            onChange={(value) => setDraft({ approvalRequired: value })}
          />
        </div>
      </div>
    </div>
  );
}

function ReviewStep({
  draft,
  format,
  busy,
  onLaunch,
}: {
  draft: LaunchSettings;
  format: (typeof FORMAT_OPTIONS)[number];
  busy: boolean;
  onLaunch: (kind: "series" | "outline" | "blog") => void;
}) {
  return (
    <div>
      <StepHeading
        title="Review your brief"
        description="Confirm the configuration. Choose Outline only to preview the structure, or Single chapter for a focused run."
      />
      <div className="grid gap-3 md:grid-cols-2">
        <div className="surface-muted p-4">
          <p className="eyebrow eyebrow-accent">Format</p>
          <p className="mt-1.5 font-display text-lg font-medium tracking-tight">
            {format.label}
          </p>
        </div>
        <div className="surface-muted p-4">
          <p className="eyebrow eyebrow-accent">Run mode</p>
          <p className="mt-1.5 font-display text-lg font-medium tracking-tight capitalize">
            {draft.runMode}
          </p>
        </div>
      </div>

      <div className="mt-4 surface-muted p-4">
        <p className="eyebrow eyebrow-accent">Brief</p>
        <div className="mt-2 space-y-1">
          <KeyValue label="Topic">{draft.topic || "—"}</KeyValue>
          <KeyValue label="Audience">{draft.audience}</KeyValue>
          <KeyValue label="Parts">{draft.parts}</KeyValue>
          <KeyValue label="Selected parts">
            {draft.selectedParts.join(", ") || "—"}
          </KeyValue>
          <KeyValue label="Words per chapter">
            {draft.minWords.toLocaleString()}–{draft.maxWords.toLocaleString()}
          </KeyValue>
          <KeyValue label="Single chapter target">{draft.part}</KeyValue>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {draft.useMemory && <Badge tone="info">Memory enabled</Badge>}
        {draft.webSearch && <Badge tone="info">Web search</Badge>}
        {(draft.approvalRequired || draft.runMode === "production") && (
          <Badge tone="warn">Approval required</Badge>
        )}
      </div>

      <div className="hairline-top mt-7 grid gap-3 pt-5 sm:grid-cols-3">
        <Button
          variant="accent"
          disabled={busy}
          onClick={() => onLaunch("series")}
          leadingIcon={<SparkIcon className="h-4 w-4" />}
        >
          Launch full series
        </Button>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => onLaunch("outline")}
        >
          Outline only
        </Button>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => onLaunch("blog")}
        >
          Single chapter (#{draft.part})
        </Button>
      </div>
    </div>
  );
}

function StepHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mb-6">
      <h2 className="font-display text-2xl font-medium tracking-tight">
        {title}
      </h2>
      <p className="mt-1.5 text-sm text-ink-500">{description}</p>
    </div>
  );
}

function SummaryRail({
  draft,
  format,
}: {
  draft: LaunchSettings;
  format: (typeof FORMAT_OPTIONS)[number];
}) {
  return (
    <aside className="space-y-4 lg:sticky lg:top-6">
      <div className="surface-dark p-5">
        <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-feature-accent">
          Brief preview
        </p>
        <p className="mt-2 font-display text-xl font-medium tracking-tight text-feature">
          {draft.topic || "Untitled manuscript"}
        </p>
        <p className="mt-1 text-xs text-feature-muted">
          {format.label} · {draft.audience}
        </p>
        <div className="hairline-top mt-4 grid grid-cols-3 gap-3 border-white/10 pt-4 text-center">
          <div>
            <p className="font-display text-2xl font-medium text-feature">
              {draft.parts}
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-feature-muted">
              parts
            </p>
          </div>
          <div>
            <p className="font-display text-2xl font-medium text-feature">
              {Math.round((draft.minWords + draft.maxWords) / 2 / 100) / 10}k
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-feature-muted">
              words/ea
            </p>
          </div>
          <div>
            <p className="font-display text-2xl font-medium text-feature capitalize">
              {draft.runMode}
            </p>
            <p className="text-[11px] uppercase tracking-[0.14em] text-feature-muted">
              mode
            </p>
          </div>
        </div>
      </div>

      <div className="surface p-5">
        <p className="eyebrow eyebrow-accent">Tips</p>
        <ul className="mt-2 space-y-2 text-sm text-ink-600">
          <li>· Start with a small selected-parts list (1–3) to validate output before scaling.</li>
          <li>· Use Outline only when iterating on structure and titles.</li>
          <li>· Production mode locks the approval gate on.</li>
        </ul>
        <Link
          href="/library"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent-deep hover:text-accent"
        >
          See past runs <ArrowRightIcon className="h-4 w-4" />
        </Link>
      </div>
    </aside>
  );
}
