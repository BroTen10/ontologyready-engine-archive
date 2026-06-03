import json
import re

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode
from ..schemas import PropertyDef, TypeCreate, TypeUpdate

router = APIRouter(prefix="/api/v1/types", tags=["types"])

# Whitelist of known PostgreSQL types
_VALID_PG_TYPES = {
    "VARCHAR", "TEXT", "INTEGER", "BIGINT", "SMALLINT", "NUMERIC",
    "REAL", "DOUBLE PRECISION", "BOOLEAN", "DATE", "TIMESTAMP",
    "TIMESTAMPTZ", "TIME", "UUID", "JSONB", "JSON", "BYTEA",
    "INTEGER[]", "TEXT[]", "VARCHAR[]",
}


async def _sync_property_definitions(pool, api_name: str, props: list[dict]) -> None:
    """Sync property definitions to the dedicated table."""
    await pool.execute(
        "DELETE FROM property_definitions WHERE type_api_name = $1", api_name
    )
    for idx, p in enumerate(props):
        await pool.execute(
            """INSERT INTO property_definitions
               (type_api_name, name, semantic_type, pg_type, constraints, "index", required, description, sort_order)
               VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)""",
            api_name,
            p["name"],
            p.get("type", "string"),
            p.get("pg_type"),
            json.dumps(p.get("constraints") or {}),
            p.get("index", False),
            p.get("required", False),
            p.get("description", ""),
            idx,
        )


async def _load_properties(pool, api_name: str) -> list[dict]:
    """Load enhanced property definitions from the dedicated table."""
    rows = await pool.fetch(
        "SELECT name, semantic_type AS type, pg_type, constraints, \"index\" AS index, "
        "required, description FROM property_definitions "
        "WHERE type_api_name = $1 ORDER BY sort_order",
        api_name,
    )
    return [
        {
            "name": r["name"],
            "type": r["type"],
            "pg_type": r["pg_type"],
            "constraints": json.loads(r["constraints"]) if isinstance(r["constraints"], str) else r["constraints"],
            "index": r["index"],
            "required": r["required"],
            "description": r["description"],
        }
        for r in rows
    ]


def _validate_properties(props: list[PropertyDef]) -> list[dict]:
    """Validate property definitions and return as list of dicts."""
    result = []
    seen = set()
    for p in props:
        if p.name in seen:
            raise AppError(ErrorCode.VALIDATION_ERROR, f"属性名 '{p.name}' 重复")
        seen.add(p.name)
        _validate_pg_type(p.pg_type)
        _validate_constraints(p.constraints, p.type)
        result.append(p.model_dump(exclude_none=True))
    return result


def _validate_pg_type(pg_type: str | None) -> None:
    if pg_type is None:
        return
    upper = pg_type.upper()
    if upper not in _VALID_PG_TYPES and not re.match(r"^VARCHAR\(\d+\)$", upper):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"无效的 pg_type '{pg_type}'。必须是有效的 PostgreSQL 类型。",
        )


def _validate_constraints(constraints: dict | None, semantic_type: str) -> None:
    if constraints is None:
        return
    allowed_keys = {"min", "max", "minLength", "maxLength", "pattern", "enum", "multipleOf"}
    for key in constraints:
        if key not in allowed_keys:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"不支持的约束类型 '{key}'。支持: {', '.join(sorted(allowed_keys))}",
            )
    if semantic_type in ("number", "integer"):
        for k in ("min", "max", "multipleOf"):
            if k in constraints and not isinstance(constraints[k], (int, float)):
                raise AppError(ErrorCode.VALIDATION_ERROR, f"约束 '{k}' 必须是数字")
    if semantic_type == "string":
        for k in ("minLength", "maxLength"):
            if k in constraints and not isinstance(constraints[k], int):
                raise AppError(ErrorCode.VALIDATION_ERROR, f"约束 '{k}' 必须是整数")
        if "pattern" in constraints:
            try:
                re.compile(constraints["pattern"])
            except re.error as e:
                raise AppError(ErrorCode.VALIDATION_ERROR, f"无效的正则表达式 pattern: {e}")


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


async def _row_to_type_with_props(row: dict, pool) -> dict:
    result = _row_to_type(row)
    try:
        props = await _load_properties(pool, row["api_name"])
        if props:
            result["properties"] = props
    except Exception:
        pass  # property_definitions table may not exist yet
    return result


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
    props = _validate_properties(body.properties)
    config = body.config or {}
    config["properties"] = props
    row = await pool.fetchrow(
        """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6) RETURNING *""",
        body.api_name,
        body.type.upper(),
        body.display_name,
        body.description,
        json.dumps(config),
        body.maturity.upper() if body.maturity else "DRAFT",
    )
    await _sync_property_definitions(pool, body.api_name, props)
    return await _row_to_type_with_props(dict(row), pool)


@router.get("/{api_name}")
async def get_type(api_name: str):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM ontology_types WHERE api_name = $1", api_name
    )
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"类型 '{api_name}' 不存在")
    return await _row_to_type_with_props(dict(row), pool)


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
    if body.properties is not None:
        props = _validate_properties(body.properties)
        config = dict(existing["config"]) if existing["config"] else {}
        if isinstance(config, str):
            config = json.loads(config)
        config["properties"] = props
        parts.append(f"config = ${len(vals)+1}::jsonb")
        vals.append(json.dumps(config))
        await _sync_property_definitions(pool, api_name, props)
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
    return await _row_to_type_with_props(dict(row), pool)


@router.patch("/{api_name}/properties")
async def update_type_properties(api_name: str, properties: list[PropertyDef]):
    """Update only the properties of a type definition."""
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT * FROM ontology_types WHERE api_name = $1", api_name
    )
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"类型 '{api_name}' 不存在")
    props = _validate_properties(properties)
    config = dict(existing["config"]) if existing["config"] else {}
    if isinstance(config, str):
        config = json.loads(config)
    config["properties"] = props
    row = await pool.fetchrow(
        "UPDATE ontology_types SET config = $1::jsonb, updated_at = now() WHERE api_name = $2 RETURNING *",
        json.dumps(config),
        api_name,
    )
    await _sync_property_definitions(pool, api_name, props)
    return await _row_to_type_with_props(dict(row), pool)


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
