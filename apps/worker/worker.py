from apps.worker.tasks import faq_generation_task, indexing_task, ingestion_task


def enqueue_job(job_type: str):
    if job_type == "ingestion":
        return ingestion_task.delay()
    if job_type == "indexing":
        return indexing_task.delay()
    if job_type == "faq":
        return faq_generation_task.delay()
    raise ValueError(f"Unsupported job_type={job_type}")


if __name__ == "__main__":
    task = enqueue_job("ingestion")
    print(f"Queued ingestion task: {task.id}")
