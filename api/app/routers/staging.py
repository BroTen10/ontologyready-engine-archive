import json

from fastapi import APIRouter, Query

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/staging", tags=["staging"])


@router.post("/store", status_code=201)
async def store_change(body: dict):
    """Stage a change for later commit or discard."""
    pool = await get_pool()

    target_type = body.get("target_type")
    if target_type not in ("object", "link", "type"):
        raise AppError(ErrorCode.VALIDATION_ERROR, "target_type 必须是 object、link 或 type")
    change_type = body.get("change_type")
    if change_type not in ("create", "update", "delete"):
        raise AppError(ErrorCode.VALIDATION_ERROR, "change_type 必须是 create、update 或 delete")

    # If updating/deleting, capture previous state for potential revert
    previous_state = None
    target_id = body.get("target_id")
    target_api_name = body.get("target_api_name")

    if target_id and change_type in ("update", "delete"):
        if target_type == "object":
            row = await pool.fetchrow(
                "SELECT * FROM ontology_objects WHERE id = $1::uuid", target_id
            )
        elif target_type == "link":
            row = await pool.fetchrow(
                "SELECT * FROM ontology_links WHERE id = $1::uuid", target_id
            )
        elif target_type == "type" and target_api_name:
            row = await pool.fetchrow(
                "SELECT * FROM ontology_types WHERE api_name = $1", target_api_name
            )
        else:
            row = None
        if row:
            previous_state = json.loads(json.dumps(dict(row), default=str))

    row = await pool.fetchrow(
        """INSERT INTO staging_changes
           (user_id, target_type, target_id, target_api_name, change_type, payload, previous_state)
           VALUES ($1, $2, $3::uuid, $4, $5, $6::jsonb, $7::jsonb) RETURNING *""",
        body.get("user_id", "system"),
        target_type,
        target_id,
        target_api_name,
        change_type,
        json.dumps(body.get("payload", {})),
        json.dumps(previous_state) if previous_state else None,
    )
    return {
        "id": str(row["id"]),
        "target_type": row["target_type"],
        "change_type": row["change_type"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
    }


@router.post("/commit")
async def commit_changes(ids: list[str] | None = None, all: bool = False):
    """Commit staged changes. Specify ids (array of UUIDs) or all=true to commit all staged changes."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if all:
                staged = await conn.fetch(
                    "SELECT * FROM staging_changes WHERE status = 'staged' ORDER BY created_at"
                )
            elif ids:
                staged = await conn.fetch(
                    "SELECT * FROM staging_changes WHERE status = 'staged' AND id = ANY($1::uuid[]) ORDER BY created_at",
                    ids,
                )
            else:
                raise AppError(ErrorCode.VALIDATION_ERROR, "请提供 ids 或设置 all=true")

            results = []
            for change in staged:
                payload = change["payload"]
                if isinstance(payload, str):
                    payload = json.loads(payload)

                if change["target_type"] == "object":
                    if change["change_type"] == "create":
                        await conn.execute(
                            """INSERT INTO ontology_objects (object_type, external_id, dataset_id, properties)
                               VALUES ($1, $2, $3, $4::jsonb)""",
                            payload["object_type"],
                            payload.get("external_id"),
                            payload.get("dataset_id", "default"),
                            json.dumps(payload.get("properties", {})),
                        )
                    elif change["change_type"] == "update" and change["target_id"]:
                        await conn.execute(
                            "UPDATE ontology_objects SET properties = $1::jsonb, updated_at = now() WHERE id = $2::uuid",
                            json.dumps(payload.get("properties", {})),
                            change["target_id"],
                        )
                    elif change["change_type"] == "delete" and change["target_id"]:
                        await conn.execute(
                            "DELETE FROM ontology_links WHERE source_id = $1::uuid OR target_id = $1::uuid",
                            change["target_id"],
                        )
                        await conn.execute(
                            "DELETE FROM ontology_objects WHERE id = $1::uuid",
                            change["target_id"],
                        )

                elif change["target_type"] == "link":
                    if change["change_type"] == "create":
                        await conn.execute(
                            """INSERT INTO ontology_links (link_type, source_id, target_id, dataset_id, properties, confidence)
                               VALUES ($1, $2::uuid, $3::uuid, $4, $5::jsonb, $6)""",
                            payload["link_type"],
                            payload["source_id"],
                            payload["target_id"],
                            payload.get("dataset_id", "default"),
                            json.dumps(payload.get("properties", {})),
                            payload.get("confidence", 1.0),
                        )
                    elif change["change_type"] == "delete" and change["target_id"]:
                        await conn.execute(
                            "DELETE FROM ontology_links WHERE id = $1::uuid",
                            change["target_id"],
                        )

                elif change["target_type"] == "type":
                    if change["change_type"] == "create":
                        await conn.execute(
                            """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                               VALUES ($1, $2, $3, $4, $5::jsonb, $6)""",
                            payload["api_name"],
                            payload.get("type", "OBJECT").upper(),
                            payload.get("display_name", payload["api_name"]),
                            payload.get("description", ""),
                            json.dumps(payload.get("config", {})),
                            payload.get("maturity", "DRAFT").upper(),
                        )

                await conn.execute(
                    "UPDATE staging_changes SET status = 'committed', updated_at = now() WHERE id = $1::uuid",
                    change["id"],
                )
                results.append(str(change["id"]))

    return {"committed": len(results), "ids": results, "total": len(staged)}


@router.delete("/discard")
async def discard_changes(ids: list[str] | None = None, all: bool = False):
    """Discard staged changes without applying them."""
    pool = await get_pool()
    if all:
        result = await pool.execute(
            "UPDATE staging_changes SET status = 'discarded', updated_at = now() WHERE status = 'staged'"
        )
    elif ids:
        result = await pool.execute(
            "UPDATE staging_changes SET status = 'discarded', updated_at = now() WHERE id = ANY($1::uuid[]) AND status = 'staged'",
            ids,
        )
    else:
        raise AppError(ErrorCode.VALIDATION_ERROR, "请提供 ids 或设置 all=true")

    return {"discarded": True}


@router.post("/revert")
async def revert_changes(ids: list[str]):
    """Revert previously committed changes using their previous_state snapshots."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            changes = await conn.fetch(
                "SELECT * FROM staging_changes WHERE id = ANY($1::uuid[]) AND status = 'committed'",
                ids,
            )
            if not changes:
                raise AppError(ErrorCode.NOT_FOUND, "未找到已提交的变更记录")

            reverted = []
            for change in changes:
                previous = change["previous_state"]
                if isinstance(previous, str):
                    previous = json.loads(previous)
                if not previous:
                    continue

                if change["target_type"] == "object":
                    await conn.execute(
                        """UPDATE ontology_objects
                           SET properties = $1::jsonb, external_id = $2, dataset_id = $3, updated_at = now()
                           WHERE id = $4::uuid""",
                        json.dumps(previous.get("properties", {})),
                        previous.get("external_id"),
                        previous.get("dataset_id", "default"),
                        change["target_id"],
                    )
                elif change["target_type"] == "link":
                    await conn.execute("DELETE FROM ontology_links WHERE id = $1::uuid", change["target_id"])
                elif change["target_type"] == "type" and change["target_api_name"]:
                    await conn.execute(
                        """UPDATE ontology_types
                           SET display_name = $1, description = $2, config = $3::jsonb, updated_at = now()
                           WHERE api_name = $4""",
                        previous.get("display_name", ""),
                        previous.get("description", ""),
                        json.dumps(previous.get("config", {})),
                        change["target_api_name"],
                    )

                await conn.execute(
                    "UPDATE staging_changes SET status = 'discarded', updated_at = now() WHERE id = $1::uuid",
                    change["id"],
                )
                reverted.append(str(change["id"]))

    return {"reverted": len(reverted), "ids": reverted}


@router.get("")
async def list_staged_changes(
    status: str | None = Query(None, pattern="^(staged|committed|discarded)$"),
    user_id: str | None = None,
):
    """List staging changes, optionally filtered by status and user."""
    pool = await get_pool()
    conditions = []
    params = []
    if status:
        conditions.append(f"status = ${len(params)+1}")
        params.append(status)
    if user_id:
        conditions.append(f"user_id = ${len(params)+1}")
        params.append(user_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await pool.fetch(
        f"SELECT * FROM staging_changes {where} ORDER BY created_at DESC LIMIT 100",
        *params,
    )
    results = []
    for r in rows:
        payload = r["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        results.append({
            "id": str(r["id"]),
            "user_id": r["user_id"],
            "target_type": r["target_type"],
            "target_id": str(r["target_id"]) if r["target_id"] else None,
            "target_api_name": r["target_api_name"],
            "change_type": r["change_type"],
            "payload": payload,
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
            "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
        })
    return results
