from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from apps.worker.celery_app import celery_app
from apps.worker.worker import enqueue_job


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/{job_type}")
def enqueue(job_type: str):
    try:
        task = enqueue_job(job_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "queued", "job_type": job_type, "task_id": task.id}


@router.get("/{task_id}")
def task_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    try:
        state = task.state
        ready = task.ready()
        successful = task.successful() if ready else False
    except Exception as exc:
        return {
            "task_id": task_id,
            "state": "backend_unavailable",
            "ready": False,
            "successful": False,
            "error": str(exc),
        }

    response = {
        "task_id": task_id,
        "state": state,
        "ready": ready,
        "successful": successful,
    }

    if ready:
        if successful:
            response["result"] = task.result
        else:
            response["error"] = str(task.result)

    return response
