from apps.worker.celery_app import celery_app
from pipelines.faq_generation.generate_faq import generate_faq_entries
from pipelines.indexing.build_vector_index import build_vector_index
from pipelines.ingestion.ingest_documents import ingest_documents


RETRY_POLICY = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 60,
    "retry_jitter": True,
    "retry_kwargs": {"max_retries": 3},
}


@celery_app.task(name="tasks.ingestion", bind=True, **RETRY_POLICY)
def ingestion_task(self, raw_dir: str = "data/raw") -> dict:
    count = ingest_documents(raw_dir)
    return {"status": "ok", "job": "ingestion", "chunks": count}


@celery_app.task(name="tasks.indexing", bind=True, **RETRY_POLICY)
def indexing_task(self, processed_dir: str = "data/processed") -> dict:
    count = build_vector_index(processed_dir)
    return {"status": "ok", "job": "indexing", "vectors": count}


@celery_app.task(name="tasks.faq_generation", bind=True, **RETRY_POLICY)
def faq_generation_task(self, processed_dir: str = "data/processed") -> dict:
    count = generate_faq_entries(processed_dir)
    return {"status": "ok", "job": "faq_generation", "entries": count}
