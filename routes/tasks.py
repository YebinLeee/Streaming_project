from fastapi import APIRouter, HTTPException
from app import conversion_tasks

router = APIRouter(tags=["tasks"])

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: int):
    """Get the status of a conversion task"""
    task = conversion_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task.get("status", "unknown"),
        "progress": task.get("progress", 0),
        "error": task.get("error"),
        "stream_url": f"/stream/{task_id}" if task.get("status") == "completed" else None
    }

@router.get("/tasks/")
async def list_tasks():
    """List all conversion tasks"""
    return [
        {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "filename": task.get("input", "").split("/")[-1],
            "created_at": task.get("created_at")
        }
        for task_id, task in conversion_tasks.items()
    ]
