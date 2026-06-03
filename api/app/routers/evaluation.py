import json
import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/eval", tags=["evaluation"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "eval")


def _dataset_row(r: dict) -> dict:
    return {
        "id": str(r["id"]),
        "name": r["name"],
        "description": r.get("description", ""),
        "item_count": r.get("item_count", 0),
        "created_by": r.get("created_by", ""),
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }


def _run_row(r: dict) -> dict:
    return {
        "id": str(r["id"]),
        "dataset_id": str(r["dataset_id"]),
        "config": json.loads(r["config"]) if isinstance(r.get("config"), str) else r.get("config", {}),
        "status": r["status"],
        "metrics": json.loads(r["metrics"]) if isinstance(r.get("metrics"), str) else r.get("metrics", {}),
        "created_by": r.get("created_by", ""),
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "completed_at": r["completed_at"].isoformat() if r.get("completed_at") else None,
    }


# ── Datasets ──────────────────────────────────────────────────

@router.get("/datasets")
async def list_datasets(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM evaluation_datasets ORDER BY created_at DESC")
    return [_dataset_row(dict(r)) for r in rows]


@router.post("/datasets")
async def create_dataset(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    name = body.get("name", "")
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO evaluation_datasets (name, description, created_by)
           VALUES ($1, $2, $3) RETURNING *""",
        name, body.get("description", ""), payload.get("sub", ""),
    )
    return _dataset_row(dict(row))


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM evaluation_datasets WHERE id = $1::uuid", dataset_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset {dataset_id} not found")
    return _dataset_row(dict(row))


@router.put("/datasets/{dataset_id}")
async def update_dataset(dataset_id: str, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM evaluation_datasets WHERE id = $1::uuid", dataset_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset {dataset_id} not found")

    updates = []
    values = []
    idx = 1
    for field in ("name", "description"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1

    if updates:
        updates.append("updated_at = now()")
        values.append(dataset_id)
        await pool.execute(
            f"UPDATE evaluation_datasets SET {', '.join(updates)} WHERE id = ${idx}::uuid",
            *values,
        )

    row = await pool.fetchrow("SELECT * FROM evaluation_datasets WHERE id = $1::uuid", dataset_id)
    return _dataset_row(dict(row))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    result = await pool.execute("DELETE FROM evaluation_datasets WHERE id = $1::uuid", dataset_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset {dataset_id} not found")
    return {"message": f"Dataset {dataset_id} deleted"}


@router.post("/datasets/upload")
async def upload_dataset_file(file: UploadFile = File(...), payload: dict = Depends(get_current_user)):
    require_admin(payload)
    content = await file.read()

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Try to parse file and count items
    item_count = 0
    if file.filename.endswith(".json"):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                item_count = len(data)
            elif isinstance(data, dict):
                item_count = len(data.get("items", data.get("data", [])))
        except json.JSONDecodeError:
            pass
    elif file.filename.endswith(".csv"):
        item_count = len(content.decode("utf-8", errors="replace").strip().split("\n")) - 1  # minus header

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO evaluation_datasets (name, description, file_path, item_count, created_by)
           VALUES ($1, $2, $3, $4, $5) RETURNING *""",
        file.filename, f"Uploaded: {file.filename}", file_path, max(0, item_count), payload.get("sub", ""),
    )
    return _dataset_row(dict(row))


# ── Runs ──────────────────────────────────────────────────────

@router.post("/runs")
async def create_run(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    dataset_id = body.get("dataset_id", "")
    if not dataset_id:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'dataset_id' is required")

    pool = await get_pool()
    ds = await pool.fetchrow("SELECT * FROM evaluation_datasets WHERE id = $1::uuid", dataset_id)
    if not ds:
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset {dataset_id} not found")

    config = body.get("config", {})
    row = await pool.fetchrow(
        """INSERT INTO evaluation_runs (dataset_id, config, created_by)
           VALUES ($1::uuid, $2::jsonb, $3) RETURNING *""",
        dataset_id, json.dumps(config), payload.get("sub", ""),
    )

    # Simulate running evaluation
    run_id = str(row["id"])
    await pool.execute("UPDATE evaluation_runs SET status = 'RUNNING' WHERE id = $1::uuid", run_id)

    # Generate mock metrics
    metrics = {
        "faithfulness": round(0.75 + __import__("random").random() * 0.2, 3),
        "answer_relevancy": round(0.7 + __import__("random").random() * 0.25, 3),
        "context_recall": round(0.65 + __import__("random").random() * 0.3, 3),
        "context_precision": round(0.7 + __import__("random").random() * 0.25, 3),
        "total_queries": dict(ds).get("item_count", 50),
    }

    await pool.execute(
        """UPDATE evaluation_runs
           SET status = 'COMPLETED', metrics = $1::jsonb, completed_at = now()
           WHERE id = $2::uuid""",
        json.dumps(metrics), run_id,
    )

    row = await pool.fetchrow("SELECT * FROM evaluation_runs WHERE id = $1::uuid", run_id)
    return _run_row(dict(row))


@router.get("/runs")
async def list_runs(dataset_id: str = "", payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    if dataset_id:
        rows = await pool.fetch(
            "SELECT * FROM evaluation_runs WHERE dataset_id = $1::uuid ORDER BY created_at DESC",
            dataset_id,
        )
    else:
        rows = await pool.fetch("SELECT * FROM evaluation_runs ORDER BY created_at DESC LIMIT 50")
    return [_run_row(dict(r)) for r in rows]


@router.get("/runs/{run_id}")
async def get_run(run_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM evaluation_runs WHERE id = $1::uuid", run_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Run {run_id} not found")
    return _run_row(dict(row))


@router.get("/comparisons")
async def compare_runs(run_ids: str = "", payload: dict = Depends(get_current_user)):
    require_admin(payload)
    if not run_ids:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Query parameter 'run_ids' is required (comma-separated UUIDs)")

    ids = [rid.strip() for rid in run_ids.split(",") if rid.strip()]
    pool = await get_pool()
    rows = []
    for rid in ids:
        row = await pool.fetchrow("SELECT * FROM evaluation_runs WHERE id = $1::uuid", rid)
        if row:
            rows.append(_run_row(dict(row)))

    return {
        "runs": rows,
        "comparison": {
            "metric_keys": ["faithfulness", "answer_relevancy", "context_recall", "context_precision"],
            "runs": [
                {
                    "run_id": r["id"],
                    "metrics": {k: r["metrics"].get(k) for k in ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]},
                }
                for r in rows
            ],
        },
    }
