import Link from "next/link";
import { Button } from "@/components/ui";
import {
  ArrowRightIcon,
  BookOpenIcon,
  CheckIcon,
  FileTextIcon,
  FlaskIcon,
  GraphIcon,
  GithubIcon,
} from "@/components/icons";
import { GITHUB_REPOSITORY_URL, WORKFLOW_STAGES } from "@/lib/api";

const FORMATS = [
  {
    icon: BookOpenIcon,
    title: "Books & long-form series",
    detail:
      "Outline 10–14 chapters, draft each as a publish-ready Markdown manuscript, and keep them coherent across the whole arc.",
  },
  {
    icon: FileTextIcon,
    title: "Reports & whitepapers",
    detail:
      "Produce structured reports with grounded citations, sectioned analysis, and exportable artifacts ready for distribution.",
  },
  {
    icon: FlaskIcon,
    title: "Research papers",
    detail:
      "Coordinate research, drafting, review, and revision cycles with explicit memory of past feedback and reusable skills.",
  },
  {
    icon: GraphIcon,
    title: "Technical blog series",
    detail:
      "Build well-researched, source-backed posts with code examples, diagrams, and editorial review gates.",
  },
];

const PRINCIPLES = [
  {
    title: "Visible work, not magic.",
    detail:
      "Every research note, draft, review report, and revision is captured as an inspectable artifact you can audit.",
  },
  {
    title: "Human in the loop, by design.",
    detail:
      "Approvals are a release gate. Reviewers can request changes, leave comments, or block publishing.",
  },
  {
    title: "Memory that compounds.",
    detail:
      "Editorial feedback distills into reusable skills that future runs follow — your style improves over time.",
  },
  {
    title: "Production by default.",
    detail:
      "Three run modes (dev, review, production) gate the pipeline so the right work happens at the right stage.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="grid gap-10 pt-4 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
        <div>
          <p className="eyebrow eyebrow-accent mb-4">Editorial agent · v1</p>
          <h1 className="text-4xl font-medium tracking-tight md:text-5xl lg:text-6xl">
            Publish books, series, and research—written by a transparent agent
            pipeline.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-[var(--color-ink-600)] md:text-lg">
            Atlas is a content operations cockpit for long-form publishing.
            Configure a brief, watch the agents research, plan, draft, review,
            and revise—then approve chapters before they ship. Built for
            editors who need rigor, not just output.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <Link href="/compose">
              <Button variant="accent" trailingIcon={<ArrowRightIcon className="h-4 w-4" />}>
                Start a new manuscript
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="secondary">Open dashboard</Button>
            </Link>
            <a
              href={GITHUB_REPOSITORY_URL}
              target="_blank"
              rel="noreferrer"
              className="btn btn-ghost"
            >
              <GithubIcon className="h-4 w-4" /> GitHub
            </a>
          </div>
        </div>
        <div className="surface-dark p-6 md:p-7">
          <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-[#dcc99e]">
            What you get
          </p>
          <h2 className="mt-2 font-display text-2xl font-medium tracking-tight text-[#fffaf0]">
            A grounded, reviewable manuscript—not a single prompt response.
          </h2>
          <ul className="mt-5 space-y-3 text-sm text-[#e8dcc4]">
            {[
              "Series outline with chapter architecture",
              "Per-chapter drafts in clean Markdown",
              "Reviewer score and lint findings",
              "Improvement pass with revision history",
              "Asset and source plan per section",
              "Approval record with reviewer comments",
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <span className="mt-0.5 grid h-4 w-4 flex-shrink-0 place-items-center rounded-full bg-[var(--color-accent)] text-[#fffaf0]">
                  <CheckIcon className="h-3 w-3" />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Formats */}
      <section>
        <div className="mb-7 flex flex-col gap-2">
          <p className="eyebrow eyebrow-accent">Built for serious publishing</p>
          <h2 className="max-w-2xl text-3xl font-medium tracking-tight md:text-4xl">
            One pipeline. Four formats. Consistent editorial standards.
          </h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {FORMATS.map(({ icon: Icon, title, detail }) => (
            <article
              key={title}
              className="surface flex gap-4 p-5 md:p-6"
            >
              <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--color-accent-soft)] text-[var(--color-accent-deep)]">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-display text-lg font-medium tracking-tight">
                  {title}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-500)]">
                  {detail}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Process */}
      <section>
        <div className="mb-7 flex flex-col gap-2">
          <p className="eyebrow eyebrow-accent">How it works</p>
          <h2 className="max-w-2xl text-3xl font-medium tracking-tight md:text-4xl">
            From topic to publish-ready manuscript in eight observable stages.
          </h2>
          <p className="max-w-2xl text-sm text-[var(--color-ink-500)]">
            Each stage produces inspectable artifacts. You can pause, branch,
            or reroute the pipeline at any gate.
          </p>
        </div>
        <ol className="grid gap-3 md:grid-cols-2">
          {WORKFLOW_STAGES.map((stage, index) => (
            <li key={stage.name} className="process-step">
              <span className="process-step-number">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="process-step-title">{stage.name}</p>
                <p className="process-step-detail">{stage.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Principles */}
      <section className="surface-muted p-6 md:p-10">
        <p className="eyebrow eyebrow-accent">Operating principles</p>
        <h2 className="mt-2 max-w-2xl text-3xl font-medium tracking-tight md:text-4xl">
          Designed for editors who care about rigor.
        </h2>
        <div className="mt-7 grid gap-6 md:grid-cols-2">
          {PRINCIPLES.map((item) => (
            <div key={item.title}>
              <p className="font-display text-lg font-medium tracking-tight">
                {item.title}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-[var(--color-ink-500)]">
                {item.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="surface flex flex-col items-start justify-between gap-5 p-7 md:flex-row md:items-center md:p-9">
        <div>
          <p className="eyebrow eyebrow-accent">Ready to compose</p>
          <h2 className="mt-1.5 text-2xl font-medium tracking-tight md:text-3xl">
            Brief the agents, approve the work, ship the manuscript.
          </h2>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/compose">
            <Button variant="accent" trailingIcon={<ArrowRightIcon className="h-4 w-4" />}>
              Compose a new run
            </Button>
          </Link>
          <Link href="/library">
            <Button variant="secondary">Browse the library</Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
