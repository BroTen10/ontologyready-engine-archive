import json
import uuid

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/links", tags=["links"])


def _row_to_link(row: dict) -> dict:
    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    return {
        "id": str(row["id"]),
        "link_type": row["link_type"],
        "source_id": str(row["source_id"]),
        "target_id": str(row["target_id"]),
        "dataset_id": row["dataset_id"],
        "properties": props,
        "confidence": row["confidence"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


@router.get("")
async def list_links(dataset: str | None = None):
    pool = await get_pool()
    if dataset:
        rows = await pool.fetch(
            "SELECT * FROM ontology_links WHERE dataset_id = $1 ORDER BY created_at DESC",
            dataset,
        )
    else:
        rows = await pool.fetch("SELECT * FROM ontology_links ORDER BY created_at DESC")
    return [_row_to_link(dict(r)) for r in rows]


@router.post("", status_code=201)
async def create_link(body: dict):
    pool = await get_pool()
    link_type_name = body.get("link_type")
    source_id = body.get("source_id")
    target_id = body.get("target_id")
    if not all([link_type_name, source_id, target_id]):
        raise AppError(ErrorCode.VALIDATION_ERROR, "link_type, source_id, target_id 为必填项")
    # Validate UUIDs before hitting the database
    try:
        uuid.UUID(source_id)
        uuid.UUID(target_id)
    except (ValueError, AttributeError):
        raise AppError(ErrorCode.VALIDATION_ERROR, "source_id 或 target_id 不是有效的 UUID")
    type_row = await pool.fetchrow(
        "SELECT api_name, config FROM ontology_types WHERE api_name = $1 AND type = 'LINK'",
        link_type_name,
    )
    if not type_row:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"链接类型 '{link_type_name}' 不存在或不是 LINK 类型")
    source = await pool.fetchrow("SELECT object_type FROM ontology_objects WHERE id = $1", source_id)
    if not source:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"源对象 '{source_id}' 不存在")
    target = await pool.fetchrow("SELECT object_type FROM ontology_objects WHERE id = $1", target_id)
    if not target:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"目标对象 '{target_id}' 不存在")
    config = type_row["config"]
    if isinstance(config, str):
        config = json.loads(config)
    src_constraint = config.get("sourceType")
    if src_constraint and source["object_type"] != src_constraint:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"源对象类型不匹配：期望 {src_constraint}，实际 {source['object_type']}",
        )
    tgt_constraint = config.get("targetType")
    if tgt_constraint and target["object_type"] != tgt_constraint:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"目标对象类型不匹配：期望 {tgt_constraint}，实际 {target['object_type']}",
        )
    props = body.get("properties", {})
    confidence = body.get("confidence", 1.0)
    row = await pool.fetchrow(
        """INSERT INTO ontology_links (link_type, source_id, target_id, dataset_id, properties, confidence)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6) RETURNING *""",
        link_type_name,
        source_id,
        target_id,
        body.get("dataset_id", "default"),
        json.dumps(props),
        confidence,
    )
    return _row_to_link(dict(row))


@router.delete("/{link_id}", status_code=204)
async def delete_link(link_id: str):
    pool = await get_pool()
    result = await pool.execute("DELETE FROM ontology_links WHERE id = $1", link_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"链接 '{link_id}' 不存在")
