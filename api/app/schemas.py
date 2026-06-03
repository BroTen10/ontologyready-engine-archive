from pydantic import BaseModel


class PropertyDef(BaseModel):
    name: str
    type: str
    required: bool = False
    description: str = ""


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
