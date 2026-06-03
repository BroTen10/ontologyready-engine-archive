import json

from fastapi import APIRouter

from ..database import get_pool

router = APIRouter(prefix="/api/v1", tags=["datasets"])


@router.get("/datasets")
async def list_datasets():
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT dataset_id FROM ontology_objects ORDER BY dataset_id")
    return [r["dataset_id"] for r in rows]


@router.post("/datasets", status_code=201)
async def create_dataset(body: dict):
    pool = await get_pool()
    ds_id = body.get("id", "")
    label = body.get("label", "")
    if not ds_id:
        return {"id": ds_id, "label": label, "warning": "数据集 ID 为空，未持久化"}
    # Insert a placeholder object to register the dataset
    await pool.execute(
        "INSERT INTO ontology_objects (object_type, dataset_id, properties) VALUES ($1, $2, $3::jsonb)",
        "__dataset_marker__", ds_id, json.dumps({"__meta": "dataset_placeholder", "label": label}),
    )
    return {"id": ds_id, "label": label}


@router.get("/stats")
async def get_stats():
    pool = await get_pool()
    obj_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_objects")
    link_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_links")
    type_count = await pool.fetchval("SELECT COUNT(*) FROM ontology_types")
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
