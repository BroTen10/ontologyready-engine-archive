import json

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1", tags=["datasets"])


@router.get("/datasets")
async def list_datasets(payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    # First try the real datasets table, fall back to DISTINCT from objects
    rows = await pool.fetch("SELECT * FROM datasets ORDER BY is_default DESC, name")
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "description": r.get("description", ""),
            "is_default": r["is_default"],
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        })

    if not results:
        # Fallback: discover from ontology_objects
        ds_rows = await pool.fetch("SELECT DISTINCT dataset_id FROM ontology_objects ORDER BY dataset_id")
        results = [{"id": r["dataset_id"], "name": r["dataset_id"], "description": "", "is_default": r["dataset_id"] == "default"} for r in ds_rows]

    return results


@router.post("/datasets", status_code=201)
async def create_dataset(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    ds_id = body.get("id", "").strip()
    name = body.get("name", ds_id)
    description = body.get("description", "")
    is_default = body.get("is_default", False)

    if not ds_id:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'id' is required")

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM datasets WHERE id = $1", ds_id)
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"Dataset '{ds_id}' already exists")

    if is_default:
        await pool.execute("UPDATE datasets SET is_default = FALSE WHERE is_default = TRUE")

    await pool.execute(
        "INSERT INTO datasets (id, name, description, is_default) VALUES ($1, $2, $3, $4)",
        ds_id, name, description, is_default,
    )
    return {"id": ds_id, "name": name, "description": description, "is_default": is_default}


@router.put("/datasets/{dataset_id}")
async def update_dataset(dataset_id: str, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM datasets WHERE id = $1", dataset_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset '{dataset_id}' not found")

    updates = []
    values = []
    idx = 1
    for field in ("name", "description"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1

    if "is_default" in body:
        if body["is_default"]:
            await pool.execute("UPDATE datasets SET is_default = FALSE WHERE is_default = TRUE")
        updates.append(f"is_default = ${idx}")
        values.append(body["is_default"])
        idx += 1

    if updates:
        updates.append("updated_at = now()")
        values.append(dataset_id)
        await pool.execute(
            f"UPDATE datasets SET {', '.join(updates)} WHERE id = ${idx}",
            *values,
        )

    row = await pool.fetchrow("SELECT * FROM datasets WHERE id = $1", dataset_id)
    r = dict(row)
    return {
        "id": r["id"], "name": r["name"], "description": r.get("description", ""),
        "is_default": r["is_default"],
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    # Count objects in this dataset
    obj_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_objects WHERE dataset_id = $1", dataset_id)
    if obj_count > 0:
        raise AppError(ErrorCode.BUSINESS_RULE_ERROR, f"Cannot delete dataset '{dataset_id}' with {obj_count} objects. Remove objects first.")

    result = await pool.execute("DELETE FROM datasets WHERE id = $1", dataset_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Dataset '{dataset_id}' not found")
    return {"message": f"Dataset '{dataset_id}' deleted"}


@router.post("/datasets/backfill")
async def backfill_datasets(payload: dict = Depends(get_current_user)):
    """Discover distinct dataset_ids from ontology_objects and create dataset entries."""
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT dataset_id FROM ontology_objects ORDER BY dataset_id")
    created = []
    for r in rows:
        ds_id = r["dataset_id"]
        existing = await pool.fetchrow("SELECT id FROM datasets WHERE id = $1", ds_id)
        if not existing:
            await pool.execute(
                "INSERT INTO datasets (id, name, description, is_default) VALUES ($1, $2, 'Auto-discovered from objects', $3)",
                ds_id, ds_id, ds_id == "default",
            )
            created.append(ds_id)
    return {"backfilled": len(created), "dataset_ids": created, "total_discovered": len(rows)}


@router.get("/stats")
async def get_stats():
    pool = await get_pool()
    obj_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_objects")
    link_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_links")
    type_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_types")
    ds_count = await pool.fetchval("SELECT COUNT(*) FROM datasets")
    if ds_count == 0:
        ds_count = await pool.fetchval("SELECT COUNT(DISTINCT dataset_id) FROM ontology_objects")
    actions_today = await pool.fetchval(
        "SELECT COUNT(*) FROM ontology_actions_log WHERE executed_at >= CURRENT_DATE"
    )
    return {
        "objectCount": obj_count,
        "linkCount": link_count,
        "typeCount": type_count,
        "datasetCount": ds_count,
        "actionsToday": actions_today,
    }
