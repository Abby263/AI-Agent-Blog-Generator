"""Background job management for long-running series generation."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from src.workflow.graph import run_blog_series
from src.utils.logger import get_logger

logger = get_logger()


class SeriesJobManager:
    """Manage asynchronous blog series jobs with progress tracking."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def _append_progress(self, job_id: str, message: str) -> None:
        timestamp = datetime.utcnow().isoformat() + "Z"
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job["progress"].append({"timestamp": timestamp, "message": message})

    def _build_series_payload(self, results: List[Dict]) -> List[Dict]:
        payload = []
        for item in results:
            result_state = item.get("result", {})
            metadata = result_state.get("metadata", {})
            payload.append({
                "topic": item.get("topic"),
                "status": item.get("status"),
                "file_path": metadata.get("output_path"),
                "word_count": metadata.get("word_count"),
                "final_content": result_state.get("final_content", ""),
                "messages": result_state.get("messages", []),
            })
        return payload

    def start_job(
        self,
        series_name: str,
        number_of_blogs: int,
        author: str,
        requirements: str,
        target_length: int,
        include_code: bool,
        include_diagrams: bool,
        content_type: str,
        topics: Optional[List[str]] = None,
    ) -> str:
        job_id = str(uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "status": "queued",
                "progress": [],
                "result": None,
                "error": None,
                "series_name": series_name,
                "number_of_blogs": number_of_blogs,
            }

        def progress_callback(message: str) -> None:
            self._append_progress(job_id, message)

        def run_job() -> None:
            self._append_progress(job_id, "Starting series generation")
            with self._lock:
                self._jobs[job_id]["status"] = "running"
            try:
                results = run_blog_series(
                    series_name=series_name,
                    number_of_blogs=number_of_blogs,
                    author=author,
                    requirements=requirements,
                    target_length=target_length,
                    include_code=include_code,
                    include_diagrams=include_diagrams,
                    content_type=content_type,
                    topics=topics,
                    progress_callback=progress_callback,
                )
                payload = self._build_series_payload(results)
                with self._lock:
                    self._jobs[job_id]["status"] = "completed"
                    self._jobs[job_id]["result"] = payload
                    self._jobs[job_id]["series_name"] = series_name
                    self._jobs[job_id]["number_of_blogs"] = len(payload)
            except Exception as exc:  # pragma: no cover - runtime issues
                logger.error("Series job %s failed: %s", job_id, exc, exc_info=True)
                with self._lock:
                    self._jobs[job_id]["status"] = "failed"
                    self._jobs[job_id]["error"] = str(exc)

        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            return job.copy()


series_job_manager = SeriesJobManager()
