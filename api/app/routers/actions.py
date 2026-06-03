import json

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])


@router.post("/{action_name}")
async def execute_action(action_name: str, body: dict):
    pool = await get_pool()
    type_row = await pool.fetchrow(
        "SELECT * FROM ontology_types WHERE api_name = $1 AND type = 'ACTION'", action_name
    )
    if not type_row:
        raise AppError(ErrorCode.NOT_FOUND, f"动作 '{action_name}' 不存在或不是 ACTION 类型")
    config = type_row["config"]
    if isinstance(config, str):
        config = json.loads(config)
    required_params = config.get("parameters", [])
    for p in required_params:
        if p.get("required") and (p["name"] not in body or body.get(p["name"]) is None):
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"缺少必填参数: {p['name']}",
                [{"field": p["name"], "code": "REQUIRED", "message": p.get("description", "")}],
            )
    before_snapshot = json.dumps({"status": "before_execution", "params": body})
    row = await pool.fetchrow(
        """INSERT INTO ontology_actions_log (action_type, parameters, status, executed_by, before_snapshot)
           VALUES ($1, $2::jsonb, 'SUCCESS', $3, $4::jsonb) RETURNING *""",
        action_name,
        json.dumps(body),
        body.get("executed_by", "system"),
        before_snapshot,
    )
    return {
        "id": str(row["id"]),
        "action_type": row["action_type"],
        "status": row["status"],
        "executed_by": row["executed_by"],
        "executed_at": row["executed_at"].isoformat() if row["executed_at"] else None,
    }


@router.get("/history")
async def action_history(page: int = 1, size: int = 20):
    pool = await get_pool()
    offset = (page - 1) * size
    total = await pool.fetchval("SELECT COUNT(*) FROM ontology_actions_log")
    rows = await pool.fetch(
        "SELECT * FROM ontology_actions_log ORDER BY executed_at DESC LIMIT $1 OFFSET $2",
        size, offset,
    )
    return {
        "data": [
            {
                "id": str(r["id"]),
                "action_type": r["action_type"],
                "status": r["status"],
                "executed_by": r["executed_by"],
                "executed_at": r["executed_at"].isoformat() if r["executed_at"] else None,
                "error_message": r["error_message"],
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "size": size,
    }
