import json

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode
from ..schemas import TypeCreate, TypeUpdate

router = APIRouter(prefix="/api/v1/types", tags=["types"])


def _row_to_type(row: dict) -> dict:
    config = row["config"]
    if isinstance(config, str):
        config = json.loads(config)
    return {
        "api_name": row["api_name"],
        "type": row["type"],
        "display_name": row["display_name"],
        "description": row["description"],
        "config": config,
        "maturity": row["maturity"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("")
async def list_types(type: str | None = None):
    pool = await get_pool()
    if type:
        rows = await pool.fetch(
            "SELECT * FROM ontology_types WHERE type = $1 ORDER BY created_at DESC",
            type.upper(),
        )
    else:
        rows = await pool.fetch("SELECT * FROM ontology_types ORDER BY created_at DESC")
    return [_row_to_type(dict(r)) for r in rows]


@router.post("", status_code=201)
async def create_type(body: TypeCreate):
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT api_name FROM ontology_types WHERE api_name = $1", body.api_name
    )
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"类型 '{body.api_name}' 已存在")
    row = await pool.fetchrow(
        """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6) RETURNING *""",
        body.api_name,
        body.type.upper(),
        body.display_name,
        body.description,
        json.dumps(body.config or {}),
        body.maturity.upper() if body.maturity else "DRAFT",
    )
    return _row_to_type(dict(row))


@router.get("/{api_name}")
async def get_type(api_name: str):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM ontology_types WHERE api_name = $1", api_name
    )
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"类型 '{api_name}' 不存在")
    return _row_to_type(dict(row))


@router.put("/{api_name}")
async def update_type(api_name: str, body: TypeUpdate):
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT * FROM ontology_types WHERE api_name = $1", api_name
    )
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"类型 '{api_name}' 不存在")
    parts = []
    vals = []
    if body.display_name is not None:
        parts.append(f"display_name = ${len(vals)+1}")
        vals.append(body.display_name)
    if body.description is not None:
        parts.append(f"description = ${len(vals)+1}")
        vals.append(body.description)
    if body.config is not None:
        parts.append(f"config = ${len(vals)+1}::jsonb")
        vals.append(json.dumps(body.config))
    if body.maturity is not None:
        parts.append(f"maturity = ${len(vals)+1}")
        vals.append(body.maturity.upper())
    if parts:
        parts.append("updated_at = now()")
        set_clause = ", ".join(parts)
        row = await pool.fetchrow(
            f"UPDATE ontology_types SET {set_clause} WHERE api_name = ${len(vals)+1} RETURNING *",
            *vals,
            api_name,
        )
    else:
        row = existing
    return _row_to_type(dict(row))


@router.delete("/{api_name}", status_code=204)
async def delete_type(api_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Lock the type row to prevent concurrent insertions
            type_row = await conn.fetchrow(
                "SELECT api_name FROM ontology_types WHERE api_name = $1 FOR UPDATE", api_name
            )
            if not type_row:
                raise AppError(ErrorCode.NOT_FOUND, f"类型 '{api_name}' 不存在")
            ref_count = await conn.fetchval(
                "SELECT COUNT(*) FROM ontology_objects WHERE object_type = $1", api_name
            )
            if ref_count and ref_count > 0:
                raise AppError(
                    ErrorCode.BUSINESS_RULE_ERROR,
                    f"无法删除类型 '{api_name}'：仍有 {ref_count} 个实例引用",
                )
            link_ref = await conn.fetchval(
                "SELECT COUNT(*) FROM ontology_links WHERE link_type = $1", api_name
            )
            if link_ref and link_ref > 0:
                raise AppError(
                    ErrorCode.BUSINESS_RULE_ERROR,
                    f"无法删除类型 '{api_name}'：仍有 {link_ref} 个链接引用",
                )
            await conn.execute("DELETE FROM ontology_types WHERE api_name = $1", api_name)
