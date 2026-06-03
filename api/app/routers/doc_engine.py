import json

from fastapi import APIRouter, Depends

from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/admin", tags=["doc-engine"])


@router.get("/doc-engine")
async def get_doc_engine_config(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM doc_engine_config WHERE is_active = TRUE LIMIT 1")
    if not row:
        return {"engine_type": "pgvector", "config": {}, "is_active": False}
    r = dict(row)
    return {
        "id": r["id"],
        "engine_type": r["engine_type"],
        "config": json.loads(r["config"]) if isinstance(r.get("config"), str) else r.get("config", {}),
        "is_active": r["is_active"],
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }


@router.put("/doc-engine")
async def update_doc_engine_config(body: dict, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    engine_type = body.get("engine_type", "pgvector")
    config = body.get("config", {})
    is_active = body.get("is_active", True)

    pool = await get_pool()
    existing = await pool.fetchrow("SELECT id FROM doc_engine_config LIMIT 1")
    if existing:
        await pool.execute(
            """UPDATE doc_engine_config
               SET engine_type = $1, config = $2::jsonb, is_active = $3, updated_at = now()
               WHERE id = $4""",
            engine_type, json.dumps(config), is_active, existing["id"],
        )
    else:
        await pool.execute(
            """INSERT INTO doc_engine_config (engine_type, config, is_active)
               VALUES ($1, $2::jsonb, $3)""",
            engine_type, json.dumps(config), is_active,
        )

    row = await pool.fetchrow("SELECT * FROM doc_engine_config WHERE is_active = TRUE LIMIT 1")
    r = dict(row)
    return {
        "id": r["id"],
        "engine_type": r["engine_type"],
        "config": json.loads(r["config"]) if isinstance(r.get("config"), str) else r.get("config", {}),
        "is_active": r["is_active"],
    }


@router.post("/doc-engine/test-connection")
async def test_doc_engine(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM doc_engine_config WHERE is_active = TRUE LIMIT 1")
    if not row:
        return {"status": "not_configured", "message": "No document engine configured"}

    r = dict(row)
    config = json.loads(r["config"]) if isinstance(r.get("config"), str) else r.get("config", {})
    engine_type = r["engine_type"]

    if engine_type == "pgvector":
        try:
            has_ext = await pool.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            if has_ext:
                dim = await pool.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name = 'ontology_objects' AND column_name = 'embedding')"
                )
                return {
                    "status": "ok",
                    "engine": "pgvector",
                    "vector_extension_installed": True,
                    "embedding_column_exists": dim,
                }
            return {"status": "error", "engine": "pgvector", "message": "pgvector extension not installed"}
        except Exception as e:
            return {"status": "error", "engine": "pgvector", "message": str(e)}

    if engine_type == "opensearch":
        url = config.get("url", "http://localhost:9200")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{url}/_cluster/health")
                if resp.status_code == 200:
                    return {"status": "ok", "engine": "opensearch", "cluster_health": resp.json()}
                return {"status": "error", "engine": "opensearch", "http_status": resp.status_code}
        except Exception as e:
            return {"status": "error", "engine": "opensearch", "message": str(e)}

    return {"status": "unknown", "engine": engine_type}
