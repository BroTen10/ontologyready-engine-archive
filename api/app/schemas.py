from pydantic import BaseModel, field_validator

# Valid PostgreSQL data types for pg_type mapping
VALID_PG_TYPES = {
    "VARCHAR", "TEXT", "INTEGER", "BIGINT", "SMALLINT", "NUMERIC",
    "REAL", "DOUBLE PRECISION", "BOOLEAN", "DATE", "TIMESTAMP",
    "TIMESTAMPTZ", "TIME", "UUID", "JSONB", "JSON", "BYTEA",
    "INTEGER[]", "TEXT[]", "VARCHAR[]",
}


class PropertyDef(BaseModel):
    name: str
    type: str
    required: bool = False
    description: str = ""
    pg_type: str | None = None
    constraints: dict | None = None
    index: bool = False

    @field_validator("pg_type")
    @classmethod
    def validate_pg_type(cls, v: str | None) -> str | None:
        if v is not None:
            upper = v.upper()
            if upper not in VALID_PG_TYPES and not upper.startswith("VARCHAR("):
                raise ValueError(f"Invalid pg_type '{v}'. Must be a valid PostgreSQL type.")
            return upper
        return v


class TypeCreate(BaseModel):
    api_name: str
    type: str
    display_name: str
    description: str
    config: dict | None = None
    maturity: str = "DRAFT"
    properties: list[PropertyDef] = []


class TypeUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    config: dict | None = None
    maturity: str | None = None
    properties: list[PropertyDef] | None = None


# ── Auth schemas ────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: str
    updated_at: str


# ── Batch operation schemas ──────────────────────────────────

MAX_BATCH_SIZE = 100


class ObjectBatchCreate(BaseModel):
    object_type: str
    external_id: str | None = None
    dataset_id: str = "default"
    properties: dict = {}


class ObjectsBatchRequest(BaseModel):
    items: list[ObjectBatchCreate]


class LinkBatchCreate(BaseModel):
    link_type: str
    source_id: str
    target_id: str
    dataset_id: str = "default"
    properties: dict = {}
    confidence: float = 1.0


class LinksBatchRequest(BaseModel):
    items: list[LinkBatchCreate]


# ── LLM Config schemas ────────────────────────────────────────

class LLMConfigCreate(BaseModel):
    provider: str
    api_key: str
    endpoint: str = ""
    model: str = ""
    settings: dict = {}
    is_default: bool = False
    is_active: bool = True


class LLMConfigUpdate(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    endpoint: str | None = None
    model: str | None = None
    settings: dict | None = None
    is_default: bool | None = None
    is_active: bool | None = None
