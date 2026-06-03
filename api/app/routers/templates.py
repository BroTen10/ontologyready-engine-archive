import json
from pathlib import Path

from fastapi import APIRouter

from ..database import get_pool
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1", tags=["templates"])

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "data" / "templates"


def _load_template(template_id: str) -> dict | None:
    # Sanitize: only allow alphanumeric + hyphens + underscores (kebab-case IDs)
    if not template_id or ".." in template_id or "/" in template_id or "\\" in template_id:
        return None
    path = TEMPLATES_DIR / f"{template_id}.json"
    # Resolve and verify stays within TEMPLATES_DIR
    resolved = path.resolve()
    if not str(resolved).startswith(str(TEMPLATES_DIR.resolve())):
        return None
    if not resolved.exists():
        return None
    return json.loads(resolved.read_text(encoding="utf-8"))


def _template_summary(tpl: dict) -> dict:
    return {k: tpl[k] for k in ("id", "name", "description", "tags", "stats")}


@router.get("/templates")
async def list_templates():
    results = []
    if TEMPLATES_DIR.exists():
        for f in sorted(TEMPLATES_DIR.glob("*.json")):
            tpl = _load_template(f.stem)
            if tpl:
                results.append(_template_summary(tpl))
    return results


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    tpl = _load_template(template_id)
    if not tpl:
        raise AppError(ErrorCode.NOT_FOUND, f"模板 '{template_id}' 不存在")
    return tpl


@router.post("/templates/{template_id}/analyze")
async def analyze_template(template_id: str):
    if not _load_template(template_id):
        raise AppError(ErrorCode.NOT_FOUND, f"模板 '{template_id}' 不存在")
    return {"status": "not_implemented", "message": "LLM 映射分析将在 Phase 2 实现"}


@router.post("/templates/{template_id}/apply")
async def apply_template(template_id: str):
    tpl = _load_template(template_id)
    if not tpl:
        raise AppError(ErrorCode.NOT_FOUND, f"模板 '{template_id}' 不存在")
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            created = {"objects": 0, "links": 0, "actions": 0}
            for ot in tpl.get("objectTypes", []):
                row = await conn.fetchrow(
                    "SELECT api_name FROM ontology_types WHERE api_name = $1", ot["api_name"]
                )
                if not row:
                    await conn.execute(
                        """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                           VALUES ($1, 'OBJECT', $2, $3, '{}', 'ACTIVE')""",
                        ot["api_name"], ot["display_name"], ot["description"],
                    )
                    created["objects"] += 1
            for lt in tpl.get("linkTypes", []):
                row = await conn.fetchrow(
                    "SELECT api_name FROM ontology_types WHERE api_name = $1", lt["api_name"]
                )
                if not row:
                    await conn.execute(
                        """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                           VALUES ($1, 'LINK', $2, $3, '{}', 'ACTIVE')""",
                        lt["api_name"], lt["display_name"], lt["description"],
                    )
                    created["links"] += 1
            for at in tpl.get("actionTypes", []):
                row = await conn.fetchrow(
                    "SELECT api_name FROM ontology_types WHERE api_name = $1", at["api_name"]
                )
                if not row:
                    await conn.execute(
                        """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                           VALUES ($1, 'ACTION', $2, $3, '{}', 'ACTIVE')""",
                        at["api_name"], at["display_name"], at["description"],
                    )
                    created["actions"] += 1
    total = created["objects"] + created["links"] + created["actions"]
    return {
        "status": "success",
        "message": f"已导入 {total} 个类型定义（对象: {created['objects']}, 关系: {created['links']}, 动作: {created['actions']}）",
        "created": created,
    }
