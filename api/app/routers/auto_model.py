import json
import base64
import hashlib

from fastapi import APIRouter, Depends
from cryptography.fernet import Fernet

from ..config import settings
from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/auto-model", tags=["auto-model"])


def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.jwt_secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def _decrypt(value: str) -> str:
    if not value:
        return ""
    return _get_fernet().decrypt(value.encode()).decode()


async def _get_default_llm_config() -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM llm_configs WHERE is_active = TRUE ORDER BY is_default DESC LIMIT 1"
    )
    if not row:
        return None
    return dict(row)


async def _call_llm(prompt: str, system_prompt: str = "") -> str:
    config = await _get_default_llm_config()
    if not config:
        raise AppError(ErrorCode.BUSINESS_RULE_ERROR, "No active LLM config found. Configure one in LLM Configs first.")

    import httpx

    api_key = _decrypt(config["api_key"])
    provider = config["provider"].lower()
    endpoint = config.get("endpoint", "")
    model = config.get("model", "")
    llm_settings = config.get("settings", {})
    if isinstance(llm_settings, str):
        llm_settings = json.loads(llm_settings)

    if provider == "openai":
        url = f"{endpoint}/chat/completions" if endpoint else "https://api.openai.com/v1/chat/completions"
    elif provider == "deepseek":
        url = f"{endpoint}/chat/completions" if endpoint else "https://api.deepseek.com/v1/chat/completions"
    elif provider == "tongyi":
        url = endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    else:
        url = f"{endpoint}/chat/completions"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model or "gpt-4",
        "messages": messages,
        "temperature": llm_settings.get("temperature", 0.3),
        "max_tokens": llm_settings.get("max_tokens", 4096),
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        if resp.status_code != 200:
            raise AppError(ErrorCode.BUSINESS_RULE_ERROR, f"LLM call failed: {resp.status_code} {resp.text[:500]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ── Connection testing ────────────────────────────────────────

@router.post("/test-connection")
async def test_db_connection(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    db_type = body.get("db_type", "postgresql")
    host = body.get("host", "localhost")
    port = body.get("port", 5432)
    database = body.get("database", "")
    username = body.get("username", "")
    password = body.get("password", "")

    if db_type != "postgresql":
        return {"status": "unsupported", "message": f"Database type '{db_type}' is not supported yet. Currently supported: postgresql"}

    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=host, port=port, database=database,
            user=username, password=password, timeout=10,
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        return {"status": "ok", "message": "Connection successful", "version": version}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Database introspection ────────────────────────────────────

@router.get("/databases")
async def list_databases(body: dict | None = None, payload: dict = Depends(get_current_user)):
    """List databases on a server. Requires connection params as query/body."""
    # For security, this returns databases from the main connection pool
    pool = await get_pool()
    rows = await pool.fetch("SELECT datname FROM pg_database WHERE datistemplate = FALSE ORDER BY datname")
    return [r["datname"] for r in rows]


@router.get("/schemas")
async def list_schemas(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name NOT IN ('pg_catalog', 'information_schema') ORDER BY schema_name"
    )
    return [r["schema_name"] for r in rows]


@router.get("/tables")
async def list_tables(schema: str = "public", payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = $1 AND table_type = 'BASE TABLE' ORDER BY table_name",
        schema,
    )
    return [r["table_name"] for r in rows]


@router.get("/describe-table")
async def describe_table(table: str, schema: str = "public", payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()

    cols = await pool.fetch(
        """SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
           FROM information_schema.columns
           WHERE table_schema = $1 AND table_name = $2
           ORDER BY ordinal_position""",
        schema, table,
    )
    if not cols:
        raise AppError(ErrorCode.NOT_FOUND, f"Table '{schema}.{table}' not found")

    pks = await pool.fetch(
        """SELECT kcu.column_name
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
           WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = $1 AND tc.table_name = $2""",
        schema, table,
    )
    pk_names = {r["column_name"] for r in pks}

    fks = await pool.fetch(
        """SELECT kcu.column_name, ccu.table_schema AS foreign_schema, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
           JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
           WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = $1 AND tc.table_name = $2""",
        schema, table,
    )

    return {
        "table": f"{schema}.{table}",
        "columns": [
            {
                "name": c["column_name"],
                "type": c["data_type"],
                "nullable": c["is_nullable"] == "YES",
                "default": c["column_default"],
                "max_length": c["character_maximum_length"],
                "is_primary_key": c["column_name"] in pk_names,
                "foreign_key": next(
                    ({"column": fk["column_name"], "references": f"{fk['foreign_schema']}.{fk['foreign_table']}.{fk['foreign_column']}"}
                     for fk in fks if fk["column_name"] == c["column_name"]),
                    None,
                ),
            }
            for c in cols
        ],
    }


# ── AI-powered analysis ───────────────────────────────────────

ONTOLOGY_SYSTEM_PROMPT = """You are an ontology modeling expert. Your task is to analyze database schemas and generate ontology type definitions in valid JSON format.

Output must be a JSON object with two keys:
- "object_types": array of object type definitions
- "link_types": array of link type definitions

Each object type: {"api_name": "...", "display_name": "...", "description": "...", "properties": [{"name": "...", "type": "...", "required": bool, "description": "...", "pg_type": "..."}]}
Each link type: {"api_name": "...", "display_name": "...", "description": "...", "source_type": "...", "target_type": "..."}

Follow these rules:
1. api_name must be snake_case, alphanumeric with underscores
2. Map PostgreSQL types to pg_type field
3. Include ALL columns as properties
4. Foreign keys should become link types
5. Provide meaningful display_name and description in English"""


@router.post("/analyze")
async def analyze_table(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    table = body.get("table", "")
    schema = body.get("schema", "public")

    if not table:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'table' is required")

    # Get table description
    pool = await get_pool()
    cols = await pool.fetch(
        """SELECT column_name, data_type, is_nullable, column_default
           FROM information_schema.columns
           WHERE table_schema = $1 AND table_name = $2
           ORDER BY ordinal_position""",
        schema, table,
    )
    if not cols:
        raise AppError(ErrorCode.NOT_FOUND, f"Table '{schema}.{table}' not found")

    fks = await pool.fetch(
        """SELECT kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
           JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
           WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = $1 AND tc.table_name = $2""",
        schema, table,
    )

    columns_desc = "\n".join(
        f"  - {c['column_name']}: {c['data_type']}" +
        (" NOT NULL" if c['is_nullable'] == 'NO' else "") +
        (f" (FK -> {next((fk['foreign_table'] for fk in fks if fk['column_name'] == c['column_name']), '')})" if c['column_name'] in {fk['column_name'] for fk in fks} else "")
        for c in cols
    )

    prompt = f"""Analyze this database table and generate ontology definitions.

Table: {schema}.{table}
Columns:
{columns_desc}

Generate appropriate object type and link types based on the columns and foreign keys."""

    result = await _call_llm(prompt, ONTOLOGY_SYSTEM_PROMPT)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown
        if "```json" in result:
            extracted = result.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(extracted)
        elif "```" in result:
            extracted = result.split("```")[1].split("```")[0].strip()
            parsed = json.loads(extracted)
        else:
            return {"raw_response": result, "error": "Could not parse LLM response as JSON"}

    return {
        "table": f"{schema}.{table}",
        "analysis": parsed,
    }


@router.post("/quick-analyze")
async def quick_analyze(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    tables = body.get("tables", [])
    schema = body.get("schema", "public")

    if not tables:
        # Auto-discover all tables
        pool = await get_pool()
        rows = await pool.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_type = 'BASE TABLE'",
            schema,
        )
        tables = [r["table_name"] for r in rows]

    if not tables:
        raise AppError(ErrorCode.NOT_FOUND, f"No tables found in schema '{schema}'")

    all_results = []
    for table in tables[:10]:  # Limit to 10 tables
        try:
            result = await analyze_table({"table": table, "schema": schema}, payload)
            all_results.append(result)
        except Exception as e:
            all_results.append({"table": table, "error": str(e)})

    return {"schema": schema, "tables_analyzed": len(all_results), "results": all_results}


# ── Validation and refinement ─────────────────────────────────

@router.post("/validate")
async def validate_ontology(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    object_types = body.get("object_types", [])
    link_types = body.get("link_types", [])

    errors = []
    warnings = []

    api_names = set()
    for ot in object_types:
        name = ot.get("api_name", "")
        if not name:
            errors.append("Object type missing api_name")
        elif name in api_names:
            errors.append(f"Duplicate api_name: {name}")
        else:
            api_names.add(name)

    for lt in link_types:
        source = lt.get("source_type", "")
        target = lt.get("target_type", "")
        if source and source not in api_names:
            warnings.append(f"Link type '{lt.get('api_name', '?')}' references unknown source_type: {source}")
        if target and target not in api_names:
            warnings.append(f"Link type '{lt.get('api_name', '?')}' references unknown target_type: {target}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


@router.post("/refine")
async def refine_ontology(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    current = body.get("current", {})
    feedback = body.get("feedback", "")

    if not feedback:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'feedback' is required")

    prompt = f"""Refine this ontology based on the feedback.

Current ontology:
{json.dumps(current, indent=2)}

Feedback: {feedback}

Output the refined ontology in the same JSON format (object_types + link_types)."""

    result = await _call_llm(prompt, ONTOLOGY_SYSTEM_PROMPT)

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

    return {"refined": parsed}


# ── Sync ──────────────────────────────────────────────────────

@router.post("/sync")
async def sync_ontology(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    object_types = body.get("object_types", [])
    link_types = body.get("link_types", [])

    if not object_types and not link_types:
        raise AppError(ErrorCode.VALIDATION_ERROR, "At least one object_type or link_type is required")

    pool = await get_pool()
    created_types = []
    errors = []

    for ot in object_types:
        try:
            api_name = ot["api_name"]
            existing = await pool.fetchrow(
                "SELECT api_name FROM ontology_types WHERE api_name = $1", api_name
            )
            if existing:
                errors.append(f"Type '{api_name}' already exists — skipped")
                continue

            config = {
                "displayName": ot.get("display_name", api_name),
                "description": ot.get("description", ""),
                "icon": ot.get("icon", "DatabaseOutlined"),
                "color": ot.get("color", "#1890ff"),
                "group": ot.get("group", "auto-modeled"),
            }
            props = ot.get("properties", [])
            props_json = json.dumps(props)

            await pool.execute(
                """INSERT INTO ontology_types (api_name, type, display_name, description, config, properties, maturity)
                   VALUES ($1, 'OBJECT', $2, $3, $4::jsonb, $5::jsonb, 'DRAFT')""",
                api_name, ot.get("display_name", api_name), ot.get("description", ""),
                json.dumps(config), props_json,
            )
            created_types.append({"api_name": api_name, "type": "OBJECT"})
        except Exception as e:
            errors.append(f"Failed to create '{ot.get('api_name', '?')}': {str(e)}")

    for lt in link_types:
        try:
            api_name = lt["api_name"]
            existing = await pool.fetchrow(
                "SELECT api_name FROM ontology_types WHERE api_name = $1", api_name
            )
            if existing:
                errors.append(f"Link type '{api_name}' already exists — skipped")
                continue

            config = {
                "displayName": lt.get("display_name", api_name),
                "description": lt.get("description", ""),
                "sourceType": lt.get("source_type", ""),
                "targetType": lt.get("target_type", ""),
                "icon": lt.get("icon", "LinkOutlined"),
                "color": lt.get("color", "#52c41a"),
                "group": lt.get("group", "auto-modeled"),
            }

            await pool.execute(
                """INSERT INTO ontology_types (api_name, type, display_name, description, config, maturity)
                   VALUES ($1, 'LINK', $2, $3, $4::jsonb, 'DRAFT')""",
                api_name, lt.get("display_name", api_name), lt.get("description", ""),
                json.dumps(config),
            )
            created_types.append({"api_name": api_name, "type": "LINK"})
        except Exception as e:
            errors.append(f"Failed to create link type '{lt.get('api_name', '?')}': {str(e)}")

    return {
        "created": created_types,
        "created_count": len(created_types),
        "errors": errors,
    }


@router.post("/detect-changes")
async def detect_changes(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    table = body.get("table", "")
    schema = body.get("schema", "public")

    if not table:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Field 'table' is required")

    pool = await get_pool()
    cols = await pool.fetch(
        """SELECT column_name, data_type, is_nullable
           FROM information_schema.columns
           WHERE table_schema = $1 AND table_name = $2
           ORDER BY ordinal_position""",
        schema, table,
    )
    if not cols:
        raise AppError(ErrorCode.NOT_FOUND, f"Table '{schema}.{table}' not found")

    current_columns = {c["column_name"]: {"type": c["data_type"], "nullable": c["is_nullable"] == "YES"} for c in cols}

    # Check if there's a corresponding ontology type
    api_name = table.lower()
    row = await pool.fetchrow(
        "SELECT config, properties FROM ontology_types WHERE api_name = $1 AND type = 'OBJECT'",
        api_name,
    )

    if not row:
        return {
            "table": f"{schema}.{table}",
            "status": "new_table",
            "message": "No ontology type exists for this table. Run /analyze to generate one.",
            "current_columns": current_columns,
        }

    existing = dict(row)
    existing_props = existing.get("properties", [])
    if isinstance(existing_props, str):
        existing_props = json.loads(existing_props)

    existing_col_names = {p["name"] for p in existing_props}

    added = [name for name in current_columns if name not in existing_col_names]
    removed = [name for name in existing_col_names if name not in current_columns]
    changed = []
    for name in current_columns:
        if name in existing_col_names:
            existing_prop = next((p for p in existing_props if p["name"] == name), {})
            if existing_prop.get("pg_type", "").upper() != current_columns[name]["type"].upper():
                changed.append({
                    "column": name,
                    "old_type": existing_prop.get("pg_type", ""),
                    "new_type": current_columns[name]["type"],
                })

    return {
        "table": f"{schema}.{table}",
        "ontology_type": api_name,
        "has_changes": bool(added or removed or changed),
        "added_columns": added,
        "removed_columns": removed,
        "changed_columns": changed,
    }
