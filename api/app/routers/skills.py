import json
import copy

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode
from ..routers.auto_model import _call_llm

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


SKILL_SYSTEM_PROMPT = """You are a skill definition expert for an ontology management platform. Generate executable skill configurations based on ontology datasets.

A skill_config is a JSON object with:
- "rules": array of business rules (conditions + actions)
- "queries": array of saved query templates
- "triggers": array of automated triggers (event + action)
- "workflows": array of multi-step workflows

Output must be valid JSON with a single "skill_config" key containing the configuration."""

PRESETS = [
    {
        "name": "Data Quality Validator",
        "description": "Validates object properties against type definitions, checking required fields, data types, and custom constraints.",
        "category": "data-quality",
        "skill_config": {
            "rules": [
                {"name": "check_required_fields", "condition": "object.properties missing required fields from type definition", "action": "flag_validation_error"},
                {"name": "check_data_types", "condition": "property value type mismatch", "action": "flag_type_error"},
            ],
            "queries": [
                {"name": "find_invalid_objects", "query": "SELECT id, object_type, properties FROM ontology_objects WHERE ..."},
            ],
        },
    },
    {
        "name": "Relationship Completeness Check",
        "description": "Checks that every object of a given type has the required relationships as defined by link type constraints.",
        "category": "data-quality",
        "skill_config": {
            "rules": [
                {"name": "check_min_links", "condition": "object link count < min_links constraint", "action": "flag_missing_relationship"},
            ],
            "queries": [
                {"name": "find_orphan_objects", "query": "SELECT o.id FROM ontology_objects o LEFT JOIN ontology_links l ON o.id = l.source_id OR o.id = l.target_id WHERE l.id IS NULL"},
            ],
        },
    },
    {
        "name": "Change Impact Analyzer",
        "description": "Analyzes the impact of changing a type definition on existing objects and links, identifying affected instances.",
        "category": "analysis",
        "skill_config": {
            "rules": [
                {"name": "detect_affected_objects", "condition": "type property removed or type changed", "action": "list_affected_objects"},
                {"name": "detect_broken_links", "condition": "link type constraint violated after change", "action": "list_broken_links"},
            ],
            "workflows": [
                {"name": "impact_report", "steps": ["identify_changes", "find_affected_instances", "generate_report", "notify_admin"]},
            ],
        },
    },
    {
        "name": "Auto-Classification",
        "description": "Automatically classifies objects into categories based on property patterns using configurable rules.",
        "category": "automation",
        "skill_config": {
            "rules": [
                {"name": "classify_by_properties", "condition": "property pattern match", "action": "assign_category"},
            ],
            "triggers": [
                {"event": "object.created", "action": "run_classification"},
                {"event": "object.updated", "action": "re_run_classification"},
            ],
        },
    },
    {
        "name": "Duplicate Detection",
        "description": "Detects potential duplicate objects based on property similarity using configurable matching rules.",
        "category": "data-quality",
        "skill_config": {
            "rules": [
                {"name": "fuzzy_name_match", "condition": "Levenshtein distance < 3 on display_name", "action": "flag_potential_duplicate"},
                {"name": "exact_property_match", "condition": "all key properties identical", "action": "flag_definite_duplicate"},
            ],
        },
    },
    {
        "name": "Data Export Engine",
        "description": "Exports ontology data to various formats (CSV, JSON, Excel) with configurable filters and field selection.",
        "category": "export",
        "skill_config": {
            "workflows": [
                {"name": "export_csv", "steps": ["select_dataset", "select_types", "configure_fields", "apply_filters", "generate_csv"]},
                {"name": "export_json", "steps": ["select_dataset", "select_types", "configure_fields", "generate_json"]},
            ],
        },
    },
]


def _row_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row.get("description", ""),
        "skill_config": json.loads(row["skill_config"]) if isinstance(row.get("skill_config"), str) else row.get("skill_config", {}),
        "status": row["status"],
        "is_preset": row["is_preset"],
        "category": row.get("category", "custom"),
        "created_by": row.get("created_by", ""),
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


@router.get("")
async def list_skills(category: str = "", status: str = "", payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    query = "SELECT * FROM skills WHERE 1=1"
    params = []
    idx = 1

    if category:
        query += f" AND category = ${idx}"
        params.append(category)
        idx += 1
    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1

    query += " ORDER BY is_preset DESC, updated_at DESC"
    rows = await pool.fetch(query, *params)
    return [_row_to_dict(dict(r)) for r in rows]


@router.post("")
async def create_skill(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    name = body.get("name", "")
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'name' is required")

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO skills (name, description, skill_config, status, category, created_by)
           VALUES ($1, $2, $3::jsonb, $4, $5, $6) RETURNING *""",
        name,
        body.get("description", ""),
        json.dumps(body.get("skill_config", {})),
        body.get("status", "active"),
        body.get("category", "custom"),
        payload.get("sub", ""),
    )
    return _row_to_dict(dict(row))


@router.get("/presets")
async def list_presets(payload: dict = Depends(get_current_user)):
    return PRESETS


@router.get("/{skill_id}")
async def get_skill(skill_id: int, payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")
    return _row_to_dict(dict(row))


@router.put("/{skill_id}")
async def update_skill(skill_id: int, body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    existing = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    if not existing:
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")

    updates = []
    values = []
    idx = 1

    for field in ("name", "description", "status", "category"):
        if field in body:
            updates.append(f"{field} = ${idx}")
            values.append(body[field])
            idx += 1

    if "skill_config" in body:
        updates.append(f"skill_config = ${idx}::jsonb")
        values.append(json.dumps(body["skill_config"]))
        idx += 1

    if updates:
        updates.append("updated_at = now()")
        values.append(skill_id)
        await pool.execute(
            f"UPDATE skills SET {', '.join(updates)} WHERE id = ${idx}",
            *values,
        )

    row = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    return _row_to_dict(dict(row))


@router.delete("/{skill_id}")
async def delete_skill(skill_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    result = await pool.execute("DELETE FROM skills WHERE id = $1", skill_id)
    if result == "DELETE 0":
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")
    return {"message": f"Skill {skill_id} deleted"}


@router.put("/{skill_id}/toggle")
async def toggle_skill(skill_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")

    r = dict(row)
    new_status = "inactive" if r["status"] == "active" else "active"
    await pool.execute(
        "UPDATE skills SET status = $1, updated_at = now() WHERE id = $2",
        new_status, skill_id,
    )
    return {"id": skill_id, "status": new_status}


@router.post("/{skill_id}/clone")
async def clone_skill(skill_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")

    r = dict(row)
    new_row = await pool.fetchrow(
        """INSERT INTO skills (name, description, skill_config, status, category, created_by)
           VALUES ($1, $2, $3::jsonb, 'draft', $4, $5) RETURNING *""",
        f"{r['name']} (Copy)",
        r.get("description", ""),
        r.get("skill_config", "{}") if isinstance(r.get("skill_config"), str) else json.dumps(r.get("skill_config", {})),
        r.get("category", "custom"),
        payload.get("sub", ""),
    )
    return _row_to_dict(dict(new_row))


@router.get("/export/{skill_id}")
async def export_skill(skill_id: int, payload: dict = Depends(get_current_user)):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM skills WHERE id = $1", skill_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Skill {skill_id} not found")

    r = _row_to_dict(dict(row))
    export_data = {
        "export_version": "1.0",
        "skill": {
            "name": r["name"],
            "description": r["description"],
            "skill_config": r["skill_config"],
            "category": r["category"],
        },
    }
    return JSONResponse(content=export_data, headers={
        "Content-Disposition": f'attachment; filename="skill_{skill_id}.json"',
    })


@router.post("/import")
async def import_skill(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    skill_data = body.get("skill", {})
    if not skill_data:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'skill' is required with name and skill_config")

    name = skill_data.get("name", "")
    if not name:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Skill name is required")

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO skills (name, description, skill_config, status, category, created_by)
           VALUES ($1, $2, $3::jsonb, 'active', $4, $5) RETURNING *""",
        name,
        skill_data.get("description", ""),
        json.dumps(skill_data.get("skill_config", {})),
        skill_data.get("category", "imported"),
        payload.get("sub", ""),
    )
    return _row_to_dict(dict(row))


@router.post("/datasets/{dataset_id}/generate")
async def generate_skills(dataset_id: str, body: dict | None = None, payload: dict = Depends(get_current_user)):
    """Generate skill suggestions from ontology dataset using LLM."""
    require_admin(payload)
    pool = await get_pool()

    # Gather ontology data for the dataset
    obj_types = await pool.fetch(
        "SELECT api_name, display_name, description, config, properties FROM ontology_types WHERE type = 'OBJECT'"
    )
    link_types = await pool.fetch(
        "SELECT api_name, display_name, description, config FROM ontology_types WHERE type = 'LINK'"
    )

    if not obj_types:
        raise AppError(ErrorCode.NOT_FOUND, "No ontology types found to generate skills from")

    ontology_summary = {
        "dataset_id": dataset_id,
        "object_types": [
            {
                "api_name": t["api_name"],
                "display_name": t["display_name"],
                "description": t["description"],
                "property_count": len(json.loads(t["properties"]) if isinstance(t.get("properties"), str) else t.get("properties", [])),
            }
            for t in obj_types
        ],
        "link_types": [
            {"api_name": t["api_name"], "display_name": t["display_name"], "description": t["description"]}
            for t in link_types
        ],
    }

    prompt = f"""Based on this ontology dataset, generate 3-5 useful skills.

Ontology:
{json.dumps(ontology_summary, indent=2)}

Each skill should have:
- name: short descriptive name
- description: what it does
- category: one of [data-quality, analysis, automation, export, governance]
- skill_config: with rules, queries, or workflows as appropriate

Output as a JSON array of skill objects."""

    result = await _call_llm(prompt, SKILL_SYSTEM_PROMPT)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        if "```json" in result:
            extracted = result.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(extracted)
        elif "```" in result:
            extracted = result.split("```")[1].split("```")[0].strip()
            parsed = json.loads(extracted)
        else:
            return {"raw_response": result, "error": "Could not parse LLM response as JSON"}

    # If parsed is a dict with skills key, extract it
    if isinstance(parsed, dict):
        skills_list = parsed.get("skills", [parsed])
    else:
        skills_list = parsed

    # Save generated skills to DB
    created = []
    for skill in skills_list:
        if isinstance(skill, dict) and skill.get("name"):
            row = await pool.fetchrow(
                """INSERT INTO skills (name, description, skill_config, status, category, created_by)
                   VALUES ($1, $2, $3::jsonb, 'draft', $4, $5) RETURNING *""",
                skill["name"],
                skill.get("description", ""),
                json.dumps(skill.get("skill_config", {})),
                skill.get("category", "custom"),
                payload.get("sub", ""),
            )
            created.append(_row_to_dict(dict(row)))

    return {"generated_count": len(created), "skills": created}
