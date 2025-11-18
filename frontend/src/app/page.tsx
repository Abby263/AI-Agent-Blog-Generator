"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const contentTypeOptions = [
  { label: "Long-form Blog / Feature", value: "blog" },
  { label: "News Article", value: "news" },
  { label: "Tutorial / Guide", value: "tutorial" },
  { label: "Product Review / Opinion", value: "review" },
];

type JobProgress = {
  timestamp: string;
  message: string;
};

type BlogResult = {
  topic?: string;
  status: string;
  file_path?: string;
  word_count?: number;
  final_content: string;
  messages: string[];
};

type JobStatus = {
  job_id: string;
  status: string;
  series_name?: string;
  number_of_blogs?: number;
  progress: JobProgress[];
  result?: BlogResult[];
  error?: string;
};

const gradientCard =
  "rounded-3xl border border-white/40 bg-white/85 p-8 shadow-xl backdrop-blur-md";
const labelClass = "block text-sm font-semibold text-slate-700";
const inputClass =
  "mt-2 w-full rounded-xl border border-slate-200 bg-white/90 px-4 py-3 focus:border-blue-500 focus:outline-none";

export default function Home() {
  const [seriesForm, setSeriesForm] = useState({
    seriesName: "Content Series Blueprint",
    numberOfBlogs: 5,
    topicsCsv: "",
    author: "AI Agent",
    requirements: "",
    targetLength: 6000,
    includeCode: true,
    includeDiagrams: true,
    contentType: "blog",
  });
  const [seriesResult, setSeriesResult] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [activeBlogIndex, setActiveBlogIndex] = useState(0);

  const parsedTopics = useMemo(() => {
    if (!seriesForm.topicsCsv.trim()) return undefined;
    return seriesForm.topicsCsv
      .split(",")
      .map((topic) => topic.trim())
      .filter(Boolean);
  }, [seriesForm.topicsCsv]);

  useEffect(() => {
    if (seriesResult?.result?.length) {
      setActiveBlogIndex(0);
    }
  }, [seriesResult?.result?.length]);

  const activeBlog =
    seriesResult?.result && seriesResult.result[activeBlogIndex];

  const renderedMarkdown = useMemo(() => {
    if (!activeBlog?.final_content) return "";
    return formatContentForPreview(activeBlog.final_content);
  }, [activeBlog?.final_content]);

  function scheduleStatusPoll(jobIdValue: string) {
    const poll = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/series/jobs/${jobIdValue}`,
        );
        if (!response.ok) {
          throw new Error(await response.text());
        }
        const data = (await response.json()) as JobStatus;
        setSeriesResult(data);
        if (data.status === "completed" || data.status === "failed") {
          setLoading(false);
          if (data.status === "failed" && data.error) {
            setError(data.error);
          }
          return;
        }
        setTimeout(poll, 4000);
      } catch (err) {
        setLoading(false);
        setError(
          err instanceof Error ? err.message : "Unable to fetch job progress",
        );
      }
    };
    poll();
  }

  async function handleSeriesSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSeriesResult(null);
    setJobId(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/series/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          series_name: seriesForm.seriesName,
          number_of_blogs: seriesForm.numberOfBlogs,
          requirements: seriesForm.requirements,
          author: seriesForm.author,
          target_length: seriesForm.targetLength,
          include_code: seriesForm.includeCode,
          include_diagrams: seriesForm.includeDiagrams,
          content_type: seriesForm.contentType,
          topics: parsedTopics,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const data = (await response.json()) as { job_id: string };
      setJobId(data.job_id);
      scheduleStatusPoll(data.job_id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate blog series",
      );
      setLoading(false);
    }
  }

  function handleCopy(content?: string) {
    if (!content) return;
    navigator.clipboard.writeText(content);
  }

  function handleDownload(blog?: BlogResult, index?: number) {
    if (!blog?.final_content) return;
    const blob = new Blob([blog.final_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeTitle = blog.topic?.replace(/[^a-z0-9-]+/gi, "-") ?? `blog-${
      (index ?? 0) + 1
    }`;
    link.href = url;
    link.download = `${safeTitle}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50 text-slate-900">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-12 md:px-10">
        <header className="space-y-4 text-center">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/80 px-4 py-1 text-xs font-semibold uppercase tracking-widest text-blue-700 shadow-sm">
            Multi-Agent Studio
          </span>
          <h1 className="text-4xl font-black leading-tight text-slate-900 sm:text-5xl">
            Generate Cohesive Content Series & Editorial Sets
          </h1>
          <p className="mx-auto max-w-3xl text-lg text-slate-600">
            Orchestrate LangGraph agents to research, plan, and write cohesive
            editorial collections—whether you need news digests, product
            reviews, tutorials, or long-form essays.
          </p>
        </header>

        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-700 shadow">
            {error}
          </div>
        )}

        <section className="grid gap-8 lg:grid-cols-[380px_1fr]">
          <form onSubmit={handleSeriesSubmit} className={`${gradientCard}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-slate-500">
                  Series Blueprint
                </p>
                <h2 className="text-3xl font-bold text-slate-900">
                  Plan & Launch
                </h2>
              </div>
              <span className="rounded-full bg-blue-600/10 px-4 py-2 text-xs font-semibold text-blue-700">
                API Driven
              </span>
            </div>

            <div className="mt-8 space-y-5">
              <label className={labelClass}>
                Series Name
                <input
                  className={inputClass}
                  value={seriesForm.seriesName}
                  onChange={(e) =>
                    setSeriesForm((prev) => ({
                      ...prev,
                      seriesName: e.target.value,
                    }))
                  }
                  required
                />
              </label>
              <label className={labelClass}>
                Number of Pieces / Chapters
                <input
                  type="number"
                  min={1}
                  className={inputClass}
                  value={seriesForm.numberOfBlogs}
                  onChange={(e) =>
                    setSeriesForm((prev) => ({
                      ...prev,
                      numberOfBlogs: Number(e.target.value),
                    }))
                  }
                />
              </label>
              <label className={labelClass}>
                Optional Topics (comma-separated)
                <textarea
                  className={`${inputClass} min-h-[96px]`}
                  placeholder="Intro to LLM Infrastructure, Feature Stores, Real-time ETAs"
                  value={seriesForm.topicsCsv}
                  onChange={(e) =>
                    setSeriesForm((prev) => ({
                      ...prev,
                      topicsCsv: e.target.value,
                    }))
                  }
                />
              </label>
              <label className={labelClass}>
                Requirements / Constraints
                <textarea
                  className={`${inputClass} min-h-[96px]`}
                  value={seriesForm.requirements}
                  onChange={(e) =>
                    setSeriesForm((prev) => ({
                      ...prev,
                      requirements: e.target.value,
                    }))
                  }
                />
              </label>
              <div className="grid gap-4 md:grid-cols-2">
                <label className={labelClass}>
                  Author
                  <input
                    className={inputClass}
                    value={seriesForm.author}
                    onChange={(e) =>
                      setSeriesForm((prev) => ({
                        ...prev,
                        author: e.target.value,
                      }))
                    }
                  />
                </label>
                <label className={labelClass}>
                  Target Length (words)
                  <input
                    type="number"
                    min={500}
                    max={50000}
                    className={inputClass}
                    value={seriesForm.targetLength}
                    onChange={(e) =>
                      setSeriesForm((prev) => ({
                        ...prev,
                        targetLength: Number(e.target.value),
                      }))
                    }
                  />
                </label>
              </div>
              <label className={labelClass}>
                Content Type
                <select
                  className={`${inputClass} cursor-pointer`}
                  value={seriesForm.contentType}
                  onChange={(e) =>
                    setSeriesForm((prev) => ({
                      ...prev,
                      contentType: e.target.value,
                    }))
                  }
                >
                  {contentTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <div className="flex flex-wrap gap-4 text-sm">
                <label className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-2 font-medium text-blue-700">
                  <input
                    type="checkbox"
                    checked={seriesForm.includeCode}
                    onChange={(e) =>
                      setSeriesForm((prev) => ({
                        ...prev,
                        includeCode: e.target.checked,
                      }))
                    }
                  />
                  Include code snippets/examples
                </label>
                <label className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-4 py-2 font-medium text-emerald-700">
                  <input
                    type="checkbox"
                    checked={seriesForm.includeDiagrams}
                    onChange={(e) =>
                      setSeriesForm((prev) => ({
                        ...prev,
                        includeDiagrams: e.target.checked,
                      }))
                    }
                  />
                  Include diagrams/visuals
                </label>
              </div>
            </div>

            <button
              type="submit"
              className="mt-8 w-full rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 py-3 text-lg font-semibold text-white shadow-lg transition hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Coordinating Agents..." : "Generate Series"}
            </button>
            <p className="mt-3 text-center text-xs text-slate-500">
              Requests are executed via REST: {API_BASE_URL}/api/series/jobs
            </p>
          </form>

          <section className="flex flex-col gap-6">
            <div className={`${gradientCard} space-y-4`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.4em] text-slate-500">
                    Live Progress
                  </p>
                  <h3 className="text-xl font-semibold text-slate-900">
                    {seriesResult?.series_name ?? seriesForm.seriesName}
                  </h3>
                </div>
                <span className="rounded-full bg-slate-900/85 px-3 py-1 text-xs font-semibold text-white">
                  {seriesResult?.status ?? "pending"}
                </span>
              </div>
              <div className="min-h-[120px] space-y-2 overflow-y-auto text-sm text-slate-600">
                {seriesResult?.progress?.length ? (
                  seriesResult.progress.map((item) => (
                    <p key={`${item.timestamp}-${item.message}`}>
                      <span className="font-semibold text-slate-800">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>{" "}
                      {item.message}
                    </p>
                  ))
                ) : (
                  <p className="text-slate-500">
                    Progress will appear here as soon as the agents begin their
                    run.
                  </p>
                )}
              </div>
              {jobId && (
                <p className="text-xs text-slate-400">Job ID: {jobId}</p>
              )}
            </div>

            <div className={`${gradientCard} space-y-4`}>
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-semibold text-slate-900">
                  Blog Viewer
                </h3>
                <span className="text-xs text-slate-500">
                  {seriesResult?.result?.length ?? 0} chapters
                </span>
              </div>

              {seriesResult?.result?.length ? (
                <>
                  <div className="flex flex-wrap gap-2">
                    {seriesResult.result.map((blog, idx) => (
                      <button
                        key={`${blog.topic}-${idx}`}
                        type="button"
                        onClick={() => setActiveBlogIndex(idx)}
                        className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                          idx === activeBlogIndex
                            ? "bg-blue-600 text-white shadow"
                            : "bg-white/80 text-slate-700 hover:bg-white"
                        }`}
                      >
                        {blog.topic || `Blog ${idx + 1}`}
                      </button>
                    ))}
                  </div>

                  <div className="rounded-3xl border border-slate-100 bg-white/90 p-5 shadow-inner">
                    {activeBlog ? (
                      <>
                        <div className="flex flex-col gap-2 border-b border-slate-100 pb-4 sm:flex-row sm:items-center sm:justify-between">
                          <div>
                            <p className="text-lg font-bold text-slate-900">
                              {activeBlog.topic || `Blog ${activeBlogIndex + 1}`}
                            </p>
                            {activeBlog.file_path && (
                              <p className="text-xs text-slate-500">
                                Saved to {activeBlog.file_path}
                              </p>
                            )}
                            {typeof activeBlog.word_count === "number" && (
                              <p className="text-xs text-slate-500">
                                Word count: {activeBlog.word_count.toLocaleString()}
                              </p>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              onClick={() => handleCopy(activeBlog.final_content)}
                              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:border-slate-400"
                            >
                              Copy Markdown
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDownload(activeBlog, activeBlogIndex)}
                              className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 hover:border-slate-400"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                       <div className="mt-4 max-h-[600px] overflow-y-auto rounded-2xl bg-slate-50/80 p-4 text-sm leading-relaxed text-slate-800">
                          {activeBlog.final_content ? (
                            <ReactMarkdown
                              className="markdown-body"
                              remarkPlugins={[remarkGfm]}
                            >
                              {renderedMarkdown}
                            </ReactMarkdown>
                          ) : (
                            <p className="text-slate-500">
                              Content pending. The agents have not produced this
                              chapter yet.
                            </p>
                          )}
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-slate-500">
                        No chapters available yet.
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-transparent p-6 text-center text-sm text-slate-500">
                  Generate a series to preview content here.
                </div>
              )}
            </div>
          </section>
        </section>

        <footer className="py-6 text-center text-xs text-slate-500">
          Powered by LangGraph, LangSmith & FastAPI • Update the backend target
          via `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`.
        </footer>
      </div>
    </main>
  );
}

function formatContentForPreview(content: string): string {
  if (!content) return "";
  let formatted = content;
  formatted = formatted.replace(
    /\]\((images\/[^)]+)\)/g,
    (_match, path) => `](${API_BASE_URL}/${path})`,
  );
  formatted = formatted.replace(
    /\]\((output\/[^)]+)\)/g,
    (_match, path) => `](${API_BASE_URL}/${path})`,
  );
  return formatted;
}
