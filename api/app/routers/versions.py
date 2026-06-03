import json
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/versions", tags=["versions"])


@router.post("/snapshot", status_code=201)
async def create_snapshot(comment: str = "", created_by: str = "system"):
    """Create a full snapshot of the current ontology state."""
    pool = await get_pool()

    # Get next version number
    latest = await pool.fetchval("SELECT MAX(version_number) FROM ontology_versions")
    next_version = (latest or 0) + 1

    # Capture all types
    types = await pool.fetch("SELECT * FROM ontology_types ORDER BY api_name")
    types_data = []
    for t in types:
        config = t["config"]
        if isinstance(config, str):
            config = json.loads(config)
        types_data.append({
            "api_name": t["api_name"],
            "type": t["type"],
            "display_name": t["display_name"],
            "description": t["description"],
            "config": config,
            "maturity": t["maturity"],
        })

    # Capture property definitions
    props = await pool.fetch("SELECT * FROM property_definitions ORDER BY type_api_name, sort_order")
    props_data = []
    for p in props:
        constraints = p["constraints"]
        if isinstance(constraints, str):
            constraints = json.loads(constraints)
        props_data.append({
            "type_api_name": p["type_api_name"],
            "name": p["name"],
            "semantic_type": p["semantic_type"],
            "pg_type": p["pg_type"],
            "constraints": constraints,
            "index": p["index"],
            "required": p["required"],
            "description": p["description"],
            "sort_order": p["sort_order"],
        })

    snapshot = {
        "version": next_version,
        "types": types_data,
        "property_definitions": props_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    row = await pool.fetchrow(
        """INSERT INTO ontology_versions (version_number, created_by, snapshot_data, comment)
           VALUES ($1, $2, $3::jsonb, $4) RETURNING *""",
        next_version,
        created_by,
        json.dumps(snapshot),
        comment or f"Snapshot v{next_version}",
    )

    # Log changes
    await pool.execute(
        """INSERT INTO version_change_log (version_id, entity_type, entity_id, change_summary)
           VALUES ($1, 'type', 'all', $2)""",
        row["id"],
        f"Created version {next_version} snapshot with {len(types_data)} types",
    )

    return {
        "id": row["id"],
        "version_number": next_version,
        "created_by": created_by,
        "comment": row["comment"],
        "type_count": len(types_data),
        "created_at": row["created_at"].isoformat(),
    }


@router.get("")
async def list_versions():
    """List all ontology versions (summary)."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, version_number, created_by, comment, created_at FROM ontology_versions ORDER BY version_number DESC"
    )
    return [
        {
            "id": r["id"],
            "version_number": r["version_number"],
            "created_by": r["created_by"],
            "comment": r["comment"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.get("/{version_id}")
async def get_version(version_id: int):
    """Get full snapshot details for a specific version."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM ontology_versions WHERE id = $1", version_id
    )
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"版本 '{version_id}' 不存在")

    snapshot = row["snapshot_data"]
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)

    changes = await pool.fetch(
        "SELECT * FROM version_change_log WHERE version_id = $1 ORDER BY created_at",
        version_id,
    )

    return {
        "id": row["id"],
        "version_number": row["version_number"],
        "created_by": row["created_by"],
        "comment": row["comment"],
        "created_at": row["created_at"].isoformat(),
        "snapshot": snapshot,
        "changes": [
            {
                "entity_type": c["entity_type"],
                "entity_id": c["entity_id"],
                "change_summary": c["change_summary"],
            }
            for c in changes
        ],
    }


@router.post("/compare")
async def compare_versions(base: int = Query(...), target: int = Query(...)):
    """Compare two versions and return the diff."""
    pool = await get_pool()
    base_row = await pool.fetchrow("SELECT * FROM ontology_versions WHERE id = $1", base)
    target_row = await pool.fetchrow("SELECT * FROM ontology_versions WHERE id = $1", target)

    if not base_row:
        raise AppError(ErrorCode.NOT_FOUND, f"基准版本 '{base}' 不存在")
    if not target_row:
        raise AppError(ErrorCode.NOT_FOUND, f"目标版本 '{target}' 不存在")

    base_snapshot = base_row["snapshot_data"]
    if isinstance(base_snapshot, str):
        base_snapshot = json.loads(base_snapshot)
    target_snapshot = target_row["snapshot_data"]
    if isinstance(target_snapshot, str):
        target_snapshot = json.loads(target_snapshot)

    base_types = {t["api_name"]: t for t in base_snapshot.get("types", [])}
    target_types = {t["api_name"]: t for t in target_snapshot.get("types", [])}

    added = [api_name for api_name in target_types if api_name not in base_types]
    removed = [api_name for api_name in base_types if api_name not in target_types]
    modified = [
        api_name for api_name in target_types
        if api_name in base_types and target_types[api_name] != base_types[api_name]
    ]

    return {
        "base_version": base_row["version_number"],
        "target_version": target_row["version_number"],
        "added_types": added,
        "removed_types": removed,
        "modified_types": modified,
        "base_type_count": len(base_types),
        "target_type_count": len(target_types),
    }


@router.post("/rollback/{version_id}")
async def rollback_to_version(version_id: int):
    """Rollback ontology types to a previous version by creating a new snapshot from old data."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM ontology_versions WHERE id = $1", version_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"版本 '{version_id}' 不存在")

    snapshot = row["snapshot_data"]
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Delete current property definitions
            await conn.execute("DELETE FROM property_definitions")
            # Delete current types (cascades to objects/links)
            # Save object/link counts before deletion
            obj_count = await conn.fetchval("SELECT COUNT(*) FROM ontology_objects")
            link_count = await conn.fetchval("SELECT COUNT(*) FROM ontology_links")

            await conn.execute("DELETE FROM ontology_links")
            await conn.execute("DELETE FROM ontology_objects")
            await conn.execute("DELETE FROM ontology_types")

            # Restore types from snapshot
            for t in snapshot.get("types", []):
                await conn.execute(
                    """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                       VALUES ($1, $2, $3, $4, $5::jsonb, $6)""",
                    t["api_name"], t["type"], t["display_name"],
                    t["description"], json.dumps(t.get("config", {})),
                    t.get("maturity", "DRAFT"),
                )

            # Restore property definitions
            for p in snapshot.get("property_definitions", []):
                await conn.execute(
                    """INSERT INTO property_definitions
                       (type_api_name, name, semantic_type, pg_type, constraints, "index", required, description, sort_order)
                       VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)""",
                    p["type_api_name"], p["name"], p.get("semantic_type", "string"),
                    p.get("pg_type"), json.dumps(p.get("constraints", {})),
                    p.get("index", False), p.get("required", False),
                    p.get("description", ""), p.get("sort_order", 0),
                )

    # Create a new version marking this rollback
    new_row = await pool.fetchrow(
        """INSERT INTO ontology_versions (version_number, created_by, snapshot_data, comment)
           VALUES ($1, 'system', $2::jsonb, $3) RETURNING *""",
        (await pool.fetchval("SELECT MAX(version_number) FROM ontology_versions") or 0) + 1,
        json.dumps(snapshot),
        f"Rollback to version {row['version_number']}",
    )

    return {
        "rolled_back_from": row["version_number"],
        "new_version": new_row["version_number"],
        "comment": f"Rolled back from v{row['version_number']}. Lost {obj_count} objects and {link_count} links.",
    }
