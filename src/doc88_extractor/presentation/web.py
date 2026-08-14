"""Минимальный веб-интерфейс для запуска извлечения документов."""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from ..core.config import Config
from ..core.gen_cfg import GenConfig
from ..services.conversion import convert
from ..services.document_source import decode_main, load_from_url
from ..services.page_downloader import PageDownloader
from ..services.workspace import clean, initialize


@dataclass(slots=True)
class Job:
    id: str
    value: str = field(repr=False)
    image_pdf: bool = False
    status: str = "queued"
    message: str = "Задание ожидает запуска"
    filename: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


app = FastAPI(title="DOC88 Extractor", version="2.2.1")
templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))
jobs: dict[str, Job] = {}
jobs_lock = threading.Lock()
extraction_lock = threading.Lock()


def _public(job: Job) -> dict:
    data = asdict(job)
    data.pop("value", None)
    if job.status == "completed":
        data["download_url"] = f"/api/jobs/{job.id}/download"
    return data


def _source_from_input(value: str) -> dict:
    value = value.strip()
    if value.isdigit():
        value = f"https://www.doc88.com/p-{value}.html"
    if value.startswith(("http://", "https://")):
        source = load_from_url(value, use_cdn_on_waf=True)
        if not source:
            raise ValueError("Не удалось получить данные документа.")
        return source
    return decode_main(value)


def _run_job(job_id: str) -> None:
    job = jobs[job_id]
    job.status = "running"
    job.message = "Документ загружается и преобразуется"
    try:
        with extraction_lock:
            source = _source_from_input(job.value)
            root = Path(os.getenv("DOC88_DATA_DIR", "data")) / "jobs" / job_id
            config = Config()
            config.o_dir_path = f"{root.as_posix()}/"
            config.check_update = False
            config.get_more = False
            config.clean = True
            config.swf2svg = job.image_pdf
            config.svgfontface = job.image_pdf
            document = GenConfig(source)
            initialize(config, source)
            PageDownloader(document, config).run()
            output = Path(convert(document, config)).resolve()
            clean(config)
        job.filename = str(output)
        job.status = "completed"
        job.message = "PDF готов"
    except Exception as error:  # Ошибка сохраняется для опроса статуса клиентом.
        job.status = "failed"
        job.message = str(error) or error.__class__.__name__


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs", status_code=202)
def create_job(
    background_tasks: BackgroundTasks,
    value: str = Form(min_length=1),
    image_pdf: bool = Form(False),
) -> dict:
    job = Job(id=uuid.uuid4().hex, value=value, image_pdf=image_pdf)
    with jobs_lock:
        jobs[job.id] = job
    background_tasks.add_task(_run_job, job.id)
    return _public(job)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Задание не найдено")
    return _public(job)


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Задание не найдено")
    if job.status != "completed" or not job.filename or not Path(job.filename).is_file():
        raise HTTPException(409, "PDF ещё не готов")
    return FileResponse(job.filename, media_type="application/pdf", filename=Path(job.filename).name)


def main() -> None:
    import uvicorn

    uvicorn.run("doc88_extractor.presentation.web:app", host="0.0.0.0", port=8080)
