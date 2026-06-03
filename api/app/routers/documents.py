import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import PlainTextResponse

from ..config import settings
from ..database import get_pool
from ..dependencies import get_current_user, require_admin
from ..errors import AppError, ErrorCode

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extract_text(file_path: str, content_type: str) -> str:
    if content_type == "text/plain":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    if content_type == "application/pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            pass

    return ""


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    extract: bool = True,
    payload: dict = Depends(get_current_user),
):
    require_admin(payload)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT, PNG, JPEG, GIF, WebP",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024} MB")

    _ensure_upload_dir()
    stored_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as f:
        f.write(content)

    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO documents (filename, original_name, content_type, file_size, file_path, status, uploaded_by)
           VALUES ($1, $2, $3, $4, $5, 'UPLOADED', $6) RETURNING *""",
        stored_name, file.filename, file.content_type, len(content), file_path, payload.get("sub", ""),
    )

    result = dict(row)

    if extract and file.content_type in ("text/plain", "application/pdf",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        await pool.execute("UPDATE documents SET status = 'EXTRACTING' WHERE id = $1", result["id"])
        try:
            text = _extract_text(file_path, file.content_type)
            await pool.execute(
                "UPDATE documents SET extracted_text = $1, status = 'EXTRACTED', updated_at = now() WHERE id = $2",
                text, result["id"],
            )
            result["extracted_text"] = text[:5000]
            result["status"] = "EXTRACTED"
        except Exception:
            await pool.execute(
                "UPDATE documents SET status = 'FAILED', updated_at = now() WHERE id = $1",
                result["id"],
            )
            result["status"] = "FAILED"

    return {
        "id": result["id"],
        "filename": result["filename"],
        "original_name": result["original_name"],
        "content_type": result["content_type"],
        "file_size": result["file_size"],
        "status": result["status"],
        "extracted_text_preview": result.get("extracted_text", "")[:500],
        "uploaded_by": result["uploaded_by"],
        "created_at": result["created_at"].isoformat() if result.get("created_at") else None,
    }


@router.get("")
async def list_documents(payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    rows = await pool.fetch("SELECT id, filename, original_name, content_type, file_size, status, uploaded_by, created_at FROM documents ORDER BY created_at DESC")
    return [
        {
            "id": r["id"],
            "filename": r["filename"],
            "original_name": r["original_name"],
            "content_type": r["content_type"],
            "file_size": r["file_size"],
            "status": r["status"],
            "uploaded_by": r["uploaded_by"],
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        }
        for r in rows
    ]


@router.get("/{doc_id}")
async def get_document(doc_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM documents WHERE id = $1", doc_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Document {doc_id} not found")
    r = dict(row)
    return {
        "id": r["id"],
        "filename": r["filename"],
        "original_name": r["original_name"],
        "content_type": r["content_type"],
        "file_size": r["file_size"],
        "status": r["status"],
        "extracted_text": r.get("extracted_text", "")[:10000],
        "uploaded_by": r["uploaded_by"],
        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
        "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
    }


@router.get("/{doc_id}/text")
async def get_document_text(doc_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT id, original_name, content_type, extracted_text, status FROM documents WHERE id = $1", doc_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Document {doc_id} not found")
    r = dict(row)
    if r["status"] != "EXTRACTED":
        raise AppError(ErrorCode.BUSINESS_RULE_ERROR, "Text has not been extracted for this document")
    return PlainTextResponse(content=r.get("extracted_text", ""), headers={
        "X-Document-Id": str(r["id"]),
        "X-Document-Name": r["original_name"],
    })


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, payload: dict = Depends(get_current_user)):
    require_admin(payload)
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM documents WHERE id = $1", doc_id)
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"Document {doc_id} not found")

    r = dict(row)
    file_path = r["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)

    await pool.execute("DELETE FROM documents WHERE id = $1", doc_id)
    return {"message": f"Document {doc_id} deleted"}
