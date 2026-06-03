import json
import uuid

from fastapi import APIRouter, Query

from ..database import get_pool
from ..errors import AppError, ErrorCode
from ..schemas import MAX_BATCH_SIZE, ObjectsBatchRequest

router = APIRouter(prefix="/api/v1/objects", tags=["objects"])


def _row_to_object(row: dict) -> dict:
    props = row["properties"]
    if isinstance(props, str):
        props = json.loads(props)
    return {
        "id": str(row["id"]),
        "object_type": row["object_type"],
        "external_id": row["external_id"],
        "dataset_id": row["dataset_id"],
        "display_name": row["display_name"],
        "properties": props,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("")
async def list_objects(
    type: str | None = None,
    dataset: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    pool = await get_pool()
    conditions = []
    params = []
    if type:
        conditions.append(f"object_type = ${len(params)+1}")
        params.append(type)
    if dataset:
        conditions.append(f"dataset_id = ${len(params)+1}")
        params.append(dataset)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    offset = (page - 1) * size
    count = await pool.fetchval(f"SELECT COUNT(*) FROM ontology_objects {where}", *params)
    rows = await pool.fetch(
        f"SELECT * FROM ontology_objects {where} ORDER BY created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}",
        *params, size, offset,
    )
    return {
        "data": [_row_to_object(dict(r)) for r in rows],
        "total": count,
        "page": page,
        "size": size,
    }


@router.post("", status_code=201)
async def create_object(body: dict):
    pool = await get_pool()
    obj_type = body.get("object_type")
    if not obj_type:
        raise AppError(ErrorCode.VALIDATION_ERROR, "object_type 为必填项")
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            type_row = await conn.fetchrow(
                "SELECT api_name FROM ontology_types WHERE api_name = $1 AND type = 'OBJECT' FOR UPDATE",
                obj_type,
            )
            if not type_row:
                raise AppError(ErrorCode.VALIDATION_ERROR, f"对象类型 '{obj_type}' 不存在或不是 OBJECT 类型")
            props = body.get("properties", {})
            row = await conn.fetchrow(
                """INSERT INTO ontology_objects (object_type, external_id, dataset_id, properties)
                   VALUES ($1, $2, $3, $4::jsonb) RETURNING *""",
                obj_type,
                body.get("external_id"),
                body.get("dataset_id", "default"),
                json.dumps(props),
            )
    return _row_to_object(dict(row))


@router.post("/batch/create", status_code=201)
async def batch_create_objects(body: ObjectsBatchRequest):
    """Batch create objects in a single transaction. All-or-nothing."""
    if len(body.items) > MAX_BATCH_SIZE:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"批量创建最多支持 {MAX_BATCH_SIZE} 条记录，当前 {len(body.items)} 条",
        )
    if not body.items:
        raise AppError(ErrorCode.VALIDATION_ERROR, "items 不能为空")

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Pre-validate all object types exist and are OBJECT type
            obj_types = {item.object_type for item in body.items}
            for ot in obj_types:
                type_row = await conn.fetchrow(
                    "SELECT api_name FROM ontology_types WHERE api_name = $1 AND type = 'OBJECT' FOR UPDATE",
                    ot,
                )
                if not type_row:
                    raise AppError(
                        ErrorCode.VALIDATION_ERROR,
                        f"对象类型 '{ot}' 不存在或不是 OBJECT 类型",
                    )

            results = []
            for item in body.items:
                row = await conn.fetchrow(
                    """INSERT INTO ontology_objects (object_type, external_id, dataset_id, properties)
                       VALUES ($1, $2, $3, $4::jsonb) RETURNING *""",
                    item.object_type,
                    item.external_id,
                    item.dataset_id,
                    json.dumps(item.properties),
                )
                results.append(_row_to_object(dict(row)))
    return {"created": len(results), "items": results}


@router.get("/search")
async def search_objects(q: str = Query(..., min_length=1)):
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT * FROM ontology_objects
           WHERE properties::text ILIKE $1
           ORDER BY created_at DESC LIMIT 50""",
        f"%{q}%",
    )
    return [_row_to_object(dict(r)) for r in rows]


@router.get("/{obj_id}")
async def get_object(obj_id: str):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM ontology_objects WHERE id = $1", obj_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"对象 '{obj_id}' 不存在")
    return _row_to_object(dict(row))


@router.put("/{obj_id}")
async def update_object(obj_id: str, body: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT * FROM ontology_objects WHERE id = $1 FOR UPDATE", obj_id
            )
            if not row:
                raise AppError(ErrorCode.NOT_FOUND, f"对象 '{obj_id}' 不存在")
            type_row = await conn.fetchrow(
                "SELECT config FROM ontology_types WHERE api_name = $1", row["object_type"]
            )
            config = type_row["config"] if type_row else {}
            if isinstance(config, str):
                config = json.loads(config)
            if config.get("readOnly"):
                raise AppError(ErrorCode.BUSINESS_RULE_ERROR, f"对象类型 '{row['object_type']}' 为只读，不允许修改")
            parts = []
            vals = []
            if "external_id" in body:
                parts.append(f"external_id = ${len(vals)+1}")
                vals.append(body["external_id"])
            if "properties" in body:
                parts.append(f"properties = ${len(vals)+1}::jsonb")
                vals.append(json.dumps(body["properties"]))
            if "dataset_id" in body:
                parts.append(f"dataset_id = ${len(vals)+1}")
                vals.append(body["dataset_id"])
            if parts:
                parts.append("updated_at = now()")
                set_clause = ", ".join(parts)
                updated = await conn.fetchrow(
                    f"UPDATE ontology_objects SET {set_clause} WHERE id = ${len(vals)+1} RETURNING *",
                    *vals, obj_id,
                )
                row = updated if updated else row
    return _row_to_object(dict(row))


@router.delete("/{obj_id}", status_code=204)
async def delete_object(obj_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Delete links first to avoid orphaned references
            await conn.execute("DELETE FROM ontology_links WHERE source_id = $1 OR target_id = $1", obj_id)
            result = await conn.execute("DELETE FROM ontology_objects WHERE id = $1", obj_id)
            if result == "DELETE 0":
                raise AppError(ErrorCode.NOT_FOUND, f"对象 '{obj_id}' 不存在")
