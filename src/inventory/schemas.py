from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date
from enum import Enum


class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    LOADED = "loaded"
    REJECTED = "rejected"


class ProductBase(BaseModel):
    product_code: str
    product_name: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_code: Optional[str]
    product_name: Optional[str]

class ProductRead(ProductBase):
    id: UUID
    model_config = dict(from_attributes=True)


class LoteBase(BaseModel):
    lote_code: str

class LoteCreate(LoteBase):
    pass

class LoteUpdate(BaseModel):
    lote_code: Optional[str]

class LoteRead(LoteBase):
    id: UUID
    model_config = dict(from_attributes=True)


class LoteProductBase(BaseModel):
    quantity: int
    expiration_date: Optional[date]
    certification_date: Optional[date]

class LoteProductCreate(LoteProductBase):
    lot_id: UUID
    product_id: UUID

class LoteProductUpdate(BaseModel):
    quantity: Optional[int]
    expiration_date: Optional[date]
    certification_date: Optional[date]

class LoteProductRead(LoteProductBase):
    id: UUID
    lot_id: UUID
    product_id: UUID
    model_config = dict(from_attributes=True)


class AssignmentBase(BaseModel):
    flight_assigned: Optional[str]
    status: AssignmentStatus

class AssignmentCreate(AssignmentBase):
    lot_id: UUID

class AssignmentUpdate(BaseModel):
    flight_assigned: Optional[str]
    status: Optional[AssignmentStatus]

class AssignmentRead(AssignmentBase):
    id: UUID
    lot_id: UUID
    model_config = dict(from_attributes=True)


class LoteDetailed(LoteRead):
    items: List[LoteProductRead]
    assignments: List[AssignmentRead]
    model_config = dict(from_attributes=True)

class ProductWithLots(ProductRead):
    lot_items: List[LoteProductRead]
    model_config = dict(from_attributes=True)
