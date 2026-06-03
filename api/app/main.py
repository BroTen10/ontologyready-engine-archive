import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import AuthMiddleware
from .config import settings
from .database import check_db, close_pool
from .errors import AppError, error_response
from .routers import types, objects, links, graph, actions, templates, datasets, staging, versions, acr, auth as auth_router, config_admin, llm, documents, auto_model, skills, background_tasks, doc_engine, evaluation, oss, admin_users, api_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.api_key:
        settings.api_key = str(uuid.uuid4())
        import logging
        logging.info(f"Generated API Key: {settings.api_key}")
    if not settings.jwt_secret:
        settings.jwt_secret = str(uuid.uuid4())
        import logging
        logging.info(f"Generated JWT Secret (auto-generated, set JWT_SECRET env var for persistence)")
    ok = await check_db()
    if not ok:
        import logging
        logging.warning("Database connection failed on startup")
    yield
    await close_pool()


app = FastAPI(title="OntologyReady API", version="0.1.0", lifespan=lifespan)
app.add_middleware(AuthMiddleware)

app.include_router(types.router)
app.include_router(objects.router)
app.include_router(links.router)
app.include_router(graph.router)
app.include_router(actions.router)
app.include_router(templates.router)
app.include_router(datasets.router)
app.include_router(staging.router)
app.include_router(versions.router)
app.include_router(acr.router)
app.include_router(auth_router.router)
app.include_router(config_admin.router)
app.include_router(llm.router)
app.include_router(documents.router)
app.include_router(auto_model.router)
app.include_router(skills.router)
app.include_router(background_tasks.router)
app.include_router(doc_engine.router)
app.include_router(evaluation.router)
app.include_router(oss.router)
app.include_router(admin_users.router)
app.include_router(api_keys.router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    req_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message, exc.details, req_id),
    )


@app.get("/health")
async def health():
    db_ok = await check_db()
    return {
        "status": "ok" if db_ok else "error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db": "connected" if db_ok else "disconnected",
    }
