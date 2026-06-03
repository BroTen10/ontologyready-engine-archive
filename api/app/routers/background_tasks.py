import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

_running_tasks: dict[str, asyncio.Task] = {}


def _row_to_dict(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "task_type": row["task_type"],
        "status": row["status"],
        "progress": row.get("progress", 0),
        "params": json.loads(row["params"]) if isinstance(row.get("params"), str) else row.get("params", {}),
        "result": json.loads(row["result"]) if isinstance(row.get("result"), str) else row.get("result"),
        "error": row.get("error"),
        "logs": row.get("logs", ""),
        "created_by": row.get("created_by", ""),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "cancelled_at": row["cancelled_at"].isoformat() if row.get("cancelled_at") else None,
    }


@router.get("")
async def list_tasks(status: str = "", task_type: str = "", payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    query = "SELECT * FROM background_tasks WHERE 1=1"
    params = []
    idx = 1

    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1
    if task_type:
        query += f" AND task_type = ${idx}"
        params.append(task_type)
        idx += 1

    query += " ORDER BY created_at DESC LIMIT 100"
    rows = await pool.fetch(query, *params)
    return [_row_to_dict(dict(r)) for r in rows]


@router.get("/{task_id}")
async def get_task(task_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM background_tasks WHERE id = $1::uuid", task_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
    return _row_to_dict(dict(row))


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM background_tasks WHERE id = $1::uuid", task_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Task {task_id} not found")

    r = dict(row)
    if r["status"] not in ("PENDING", "RUNNING"):
        raise AppError(ErrorCode.BUSINESS_RULE_ERROR, f"Cannot cancel task with status '{r['status']}'")

    # Cancel the running asyncio task if it exists
    if task_id in _running_tasks:
        _running_tasks[task_id].cancel()
        del _running_tasks[task_id]

    await pool.execute(
        "UPDATE background_tasks SET status = 'CANCELED', cancelled_at = now(), updated_at = now() WHERE id = $1::uuid",
        task_id,
    )
    return {"id": task_id, "status": "CANCELED", "message": "Task cancelled"}


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT id, logs, status FROM background_tasks WHERE id = $1::uuid", task_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Task {task_id} not found")
    r = dict(row)
    return {
        "task_id": str(r["id"]),
        "status": r["status"],
        "logs": r.get("logs", ""),
    }


async def _run_task(task_id: str, task_type: str, params: dict):
    """Execute a background task. Different task types have different logic."""
    pool = await get_pool()
    try:
        await pool.execute(
            "UPDATE background_tasks SET status = 'RUNNING', updated_at = now() WHERE id = $1::uuid",
            task_id,
        )

        logs = []
        result = {}

        if task_type == "data_export":
            logs.append("Starting data export...")
            await pool.execute(
                "UPDATE background_tasks SET progress = 10, logs = $1 WHERE id = $2::uuid",
                "\n".join(logs), task_id,
            )
            await asyncio.sleep(0.5)  # Simulate work
            logs.append("Export completed.")
            result = {"exported_count": 100, "format": params.get("format", "json")}

        elif task_type == "bulk_import":
            logs.append("Starting bulk import...")
            await pool.execute(
                "UPDATE background_tasks SET progress = 20, logs = $1 WHERE id = $2::uuid",
                "\n".join(logs), task_id,
            )
            await asyncio.sleep(0.5)
            logs.append("Import completed.")
            result = {"imported_count": params.get("count", 50)}

        elif task_type == "graph_reindex":
            logs.append("Rebuilding graph indexes...")
            await pool.execute(
                "UPDATE background_tasks SET progress = 30, logs = $1 WHERE id = $2::uuid",
                "\n".join(logs), task_id,
            )
            await asyncio.sleep(0.5)
            logs.append("Reindex completed.")
            result = {"reindexed_nodes": 500, "reindexed_edges": 1200}

        else:
            logs.append(f"Running generic task: {task_type}")
            await asyncio.sleep(0.3)
            result = {"status": "done"}

        await pool.execute(
            """UPDATE background_tasks
               SET status = 'COMPLETED', progress = 100, result = $1::jsonb, logs = $2, completed_at = now(), updated_at = now()
               WHERE id = $3::uuid""",
            json.dumps(result), "\n".join(logs), task_id,
        )
    except asyncio.CancelledError:
        await pool.execute(
            "UPDATE background_tasks SET status = 'CANCELED', cancelled_at = now(), updated_at = now() WHERE id = $1::uuid",
            task_id,
        )
    except Exception as e:
        await pool.execute(
            "UPDATE background_tasks SET status = 'FAILED', error = $1, updated_at = now() WHERE id = $2::uuid",
            str(e), task_id,
        )
    finally:
        _running_tasks.pop(task_id, None)


@router.post("/submit")
async def submit_task(body: dict, payload: dict = Depends(get_current_user)):
    """Submit a new background task for execution."""
    require_admin(payload)
    task_type = body.get("task_type", "")
    params = body.get("params", {})

    if not task_type:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'task_type' is required")

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO background_tasks (task_type, params, created_by)
           VALUES ($1, $2::jsonb, $3) RETURNING *""",
        task_type, json.dumps(params), payload.get("sub", ""),
    )

    r = dict(row)
    task_id = str(r["id"])

    task = asyncio.create_task(_run_task(task_id, task_type, params))
    _running_tasks[task_id] = task

    return _row_to_dict(dict(r))
