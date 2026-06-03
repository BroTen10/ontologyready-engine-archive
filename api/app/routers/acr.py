import json

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/acr", tags=["acr"])


# ── Rules ──


@router.get("/rules")
async def list_rules():
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM acr_rules ORDER BY priority DESC")
    return [
        {
            "id": r["id"], "rule_name": r["rule_name"],
            "description": r["description"],
            "conditions": json.loads(r["conditions"]) if isinstance(r["conditions"], str) else r["conditions"],
            "permissions": json.loads(r["permissions"]) if isinstance(r["permissions"], str) else r["permissions"],
            "priority": r["priority"], "is_active": r["is_active"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.post("/rules", status_code=201)
async def create_rule(body: dict):
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM acr_rules WHERE rule_name = $1", body["rule_name"])
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"规则 '{body['rule_name']}' 已存在")

    row = await pool.fetchrow(
        """INSERT INTO acr_rules (rule_name, description, conditions, permissions, priority, is_active)
           VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6) RETURNING *""",
        body["rule_name"],
        body.get("description", ""),
        json.dumps(body.get("conditions", {})),
        json.dumps(body.get("permissions", {})),
        body.get("priority", 0),
        body.get("is_active", True),
    )
    conditions = row["conditions"]
    if isinstance(conditions, str):
        conditions = json.loads(conditions)
    permissions = row["permissions"]
    if isinstance(permissions, str):
        permissions = json.loads(permissions)
    return {
        "id": row["id"], "rule_name": row["rule_name"],
        "description": row["description"],
        "conditions": conditions, "permissions": permissions,
        "priority": row["priority"], "is_active": row["is_active"],
    }


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, body: dict):
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM acr_rules WHERE id = $1", rule_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"规则 '{rule_id}' 不存在")

    parts = []
    vals = []
    for field in ["rule_name", "description", "priority"]:
        if field in body:
            parts.append(f"{field} = ${len(vals)+1}")
            vals.append(body[field])
    for field in ["conditions", "permissions"]:
        if field in body:
            parts.append(f"{field} = ${len(vals)+1}::jsonb")
            vals.append(json.dumps(body[field]))
    if "is_active" in body:
        parts.append(f"is_active = ${len(vals)+1}")
        vals.append(body["is_active"])

    if parts:
        parts.append("updated_at = now()")
        row = await pool.fetchrow(
            f"UPDATE acr_rules SET {', '.join(parts)} WHERE id = ${len(vals)+1} RETURNING *",
            *vals, rule_id,
        )
    else:
        row = existing
    return {
        "id": row["id"], "rule_name": row["rule_name"],
        "description": row["description"],
        "conditions": json.loads(row["conditions"]) if isinstance(row["conditions"], str) else row["conditions"],
        "permissions": json.loads(row["permissions"]) if isinstance(row["permissions"], str) else row["permissions"],
        "priority": row["priority"], "is_active": row["is_active"],
    }


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: int):
    pool = await get_pool()
    result = await pool.execute("DELETE FROM acr_rules WHERE id = $1", rule_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"规则 '{rule_id}' 不存在")


# ── Groups ──


@router.get("/groups")
async def list_groups():
    pool = await get_pool()
    rows = await pool.fetch("SELECT * FROM acr_groups ORDER BY id")
    return [
        {
            "id": r["id"], "group_name": r["group_name"],
            "description": r["description"],
            "rules": r["rules"], "is_active": r["is_active"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.post("/groups", status_code=201)
async def create_group(body: dict):
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM acr_groups WHERE group_name = $1", body["group_name"])
    if existing:
        raise AppError(ErrorCode.CONFLICT, f"组 '{body['group_name']}' 已存在")

    row = await pool.fetchrow(
        """INSERT INTO acr_groups (group_name, description, rules, is_active)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        body["group_name"],
        body.get("description", ""),
        body.get("rules", []),
        body.get("is_active", True),
    )
    return {
        "id": row["id"], "group_name": row["group_name"],
        "description": row["description"],
        "rules": row["rules"], "is_active": row["is_active"],
    }


@router.put("/groups/{group_id}")
async def update_group(group_id: int, body: dict):
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM acr_groups WHERE id = $1", group_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"组 '{group_id}' 不存在")

    parts = []
    vals = []
    for field in ["group_name", "description"]:
        if field in body:
            parts.append(f"{field} = ${len(vals)+1}")
            vals.append(body[field])
    if "rules" in body:
        parts.append(f"rules = ${len(vals)+1}")
        vals.append(body["rules"])
    if "is_active" in body:
        parts.append(f"is_active = ${len(vals)+1}")
        vals.append(body["is_active"])

    if parts:
        parts.append("updated_at = now()")
        row = await pool.fetchrow(
            f"UPDATE acr_groups SET {', '.join(parts)} WHERE id = ${len(vals)+1} RETURNING *",
            *vals, group_id,
        )
    else:
        row = existing
    return {
        "id": row["id"], "group_name": row["group_name"],
        "description": row["description"],
        "rules": row["rules"], "is_active": row["is_active"],
    }


@router.delete("/groups/{group_id}", status_code=204)
async def delete_group(group_id: int):
    pool = await get_pool()
    result = await pool.execute("DELETE FROM acr_groups WHERE id = $1", group_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"组 '{group_id}' 不存在")


# ── Bindings ──


@router.get("/bindings")
async def list_bindings(user_id: str | None = None):
    pool = await get_pool()
    if user_id:
        rows = await pool.fetch(
            "SELECT * FROM acr_bindings WHERE user_id = $1 ORDER BY id", user_id
        )
    else:
        rows = await pool.fetch("SELECT * FROM acr_bindings ORDER BY id")
    return [
        {
            "id": r["id"], "user_id": r["user_id"],
            "group_id": r["group_id"],
            "target_type": r["target_type"], "target_id": r["target_id"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.post("/bindings", status_code=201)
async def create_binding(body: dict):
    pool = await get_pool()
    group_exists = await pool.fetchrow("SELECT id FROM acr_groups WHERE id = $1", body["group_id"])
    if not group_exists:
        raise AppError(ErrorCode.NOT_FOUND, f"组 '{body['group_id']}' 不存在")

    row = await pool.fetchrow(
        """INSERT INTO acr_bindings (user_id, group_id, target_type, target_id)
           VALUES ($1, $2, $3, $4) RETURNING *""",
        body["user_id"],
        body["group_id"],
        body.get("target_type", "*"),
        body.get("target_id", "*"),
    )
    return {
        "id": row["id"], "user_id": row["user_id"],
        "group_id": row["group_id"],
        "target_type": row["target_type"], "target_id": row["target_id"],
    }


@router.delete("/bindings/{binding_id}", status_code=204)
async def delete_binding(binding_id: int):
    pool = await get_pool()
    result = await pool.execute("DELETE FROM acr_bindings WHERE id = $1", binding_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"绑定 '{binding_id}' 不存在")


# ── Evaluate ──


@router.post("/evaluate")
async def evaluate_access(body: dict):
    """Evaluate whether a user has permission to perform an action on a target."""
    pool = await get_pool()
    user_id = body.get("user_id")
    action = body.get("action", "read")
    target_type = body.get("target_type", "*")
    target_id = body.get("target_id", "*")

    # Get user's group memberships with active rules
    bindings = await pool.fetch(
        """SELECT b.group_id, g.rules
           FROM acr_bindings b
           JOIN acr_groups g ON b.group_id = g.id AND g.is_active = TRUE
           WHERE b.user_id = $1
             AND (b.target_type = '*' OR b.target_type = $2)
             AND (b.target_id = '*' OR b.target_id = $3)""",
        user_id, target_type, target_id,
    )

    all_rule_ids = set()
    for b in bindings:
        for rid in b["rules"]:
            all_rule_ids.add(rid)

    if not all_rule_ids:
        return {"allowed": True, "reason": "no rules match — default allow"}

    rules = await pool.fetch(
        "SELECT * FROM acr_rules WHERE id = ANY($1) AND is_active = TRUE ORDER BY priority DESC",
        list(all_rule_ids),
    )

    for rule in rules:
        conditions = rule["conditions"]
        if isinstance(conditions, str):
            conditions = json.loads(conditions)
        permissions = rule["permissions"]
        if isinstance(permissions, str):
            permissions = json.loads(permissions)

        # Simple condition evaluation
        condition_type = conditions.get("type", "always")
        if condition_type == "always":
            match = True
        elif condition_type == "target_type":
            match = conditions.get("value") == target_type
        elif condition_type == "action":
            match = action in (conditions.get("values") or [])
        else:
            match = False

        if match:
            allowed_actions = permissions.get("actions", [])
            denied_actions = permissions.get("deny", [])
            if action in denied_actions:
                return {"allowed": False, "reason": f"Denied by rule '{rule['rule_name']}'"}
            if "all" in allowed_actions or action in allowed_actions:
                return {"allowed": True, "reason": f"Allowed by rule '{rule['rule_name']}'"}

    return {"allowed": True, "reason": "no matching deny rule — default allow"}
