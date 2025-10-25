from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from .schemas import (
    ProductCreate, ProductUpdate, ProductRead, 
    LoteCreate, LoteUpdate, LoteRead, LoteDetailed,
    LoteProductCreate, LoteProductUpdate, LoteProductRead,
    AssignmentCreate, AssignmentUpdate, AssignmentRead,
)
from .models import Product, Lote
from .service import CateringService
from src.database import get_db

from src.inventory.exceptions import (
    HTTP_LOT_DUPLICATE, HTTP_LOT_NOT_FOUND,
    HTTP_INVALID_PRODUCT, HTTP_INVALID_QUANTITY,
    HTTP_DATABASE_ERROR,
)

from fastapi import HTTPException
PRODUCT_DUPLICATE = {"error_code": "PRODUCT_DUPLICATE", "detail": "The provided product_code already exists."}
PRODUCT_NOT_FOUND = {"error_code": "PRODUCT_NOT_FOUND", "detail": "The requested product was not found."}
ASSIGNMENT_NOT_FOUND = {"error_code": "ASSIGNMENT_NOT_FOUND", "detail": "The requested assignment was not found."}
LOTE_PRODUCT_NOT_FOUND = {"error_code": "LOTE_PRODUCT_NOT_FOUND", "detail": "The requested lot item was not found."}

HTTP_PRODUCT_DUPLICATE = HTTPException(status_code=status.HTTP_409_CONFLICT, detail=PRODUCT_DUPLICATE)
HTTP_PRODUCT_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PRODUCT_NOT_FOUND)
HTTP_ASSIGNMENT_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ASSIGNMENT_NOT_FOUND)
HTTP_LOTE_PRODUCT_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LOTE_PRODUCT_NOT_FOUND)


products_router = APIRouter(prefix="/products", tags=["products"])
lotes_router = APIRouter(prefix="/lotes", tags=["lotes"])
lot_items_router = APIRouter(prefix="/lot-items", tags=["lote_products"])
assignments_router = APIRouter(prefix="/assignments", tags=["assignments"])

@products_router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.create_product(db, data)
    except ValueError:
        raise HTTP_PRODUCT_DUPLICATE
    except IntegrityError:
        raise HTTP_PRODUCT_DUPLICATE
    except Exception:
        raise HTTP_DATABASE_ERROR


@products_router.patch("/{product_id}", response_model=ProductRead)
async def update_product(product_id: uuid.UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.update_product(db, product_id, data)
    except LookupError:
        raise HTTP_PRODUCT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@products_router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        obj = await CateringService.get_product(db, product_id)
        return obj
    except LookupError:
        raise HTTP_PRODUCT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@products_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await CateringService.delete_product(db, product_id)
    except LookupError:
        raise HTTP_PRODUCT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@products_router.get("", response_model=List[ProductRead])
async def list_products(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(Product))
        return list(res.scalars().all())
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.post("", response_model=LoteRead, status_code=status.HTTP_201_CREATED)
async def create_lote(data: LoteCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.create_lote(db, data)
    except ValueError:
        raise HTTP_LOT_DUPLICATE
    except IntegrityError:
        raise HTTP_LOT_DUPLICATE
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.patch("/{lot_id}", response_model=LoteRead)
async def update_lote(lot_id: uuid.UUID, data: LoteUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.update_lote(db, lot_id, data)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.get("/{lot_id}", response_model=LoteRead)
async def get_lote(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.get_lote(db, lot_id)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.get("/{lot_id}/detailed", response_model=LoteDetailed)
async def get_lote_detailed(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.get_lote_detailed(db, lot_id)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.delete("/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lote(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await CateringService.delete_lote(db, lot_id)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.get("", response_model=List[LoteRead])
async def list_lotes(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(Lote))
        return list(res.scalars().all())
    except Exception:
        raise HTTP_DATABASE_ERROR


@lot_items_router.post("", response_model=LoteProductRead, status_code=status.HTTP_201_CREATED)
async def add_or_increment_item(data: LoteProductCreate, db: AsyncSession = Depends(get_db)):
    try:
        if data.quantity is None or data.quantity < 0:
            raise HTTP_INVALID_QUANTITY
        return await CateringService.add_or_increment_lote_product(db, data)
    except HTTPException:
        raise
    except LookupError as e:
        msg = str(e).lower()
        if "product" in msg:
            raise HTTP_INVALID_PRODUCT
        else:
            raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lot_items_router.patch("/{lote_product_id}", response_model=LoteProductRead)
async def update_item(lote_product_id: uuid.UUID, data: LoteProductUpdate, db: AsyncSession = Depends(get_db)):
    try:
        if data.quantity is not None and data.quantity < 0:
            raise HTTP_INVALID_QUANTITY
        return await CateringService.update_lote_product(db, lote_product_id, data)
    except LookupError:
        raise HTTP_LOTE_PRODUCT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lot_items_router.delete("/{lote_product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(lote_product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await CateringService.remove_lote_product(db, lote_product_id)
    except LookupError:
        raise HTTP_LOTE_PRODUCT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.get("/{lot_id}/items", response_model=List[LoteProductRead])
async def list_items(lot_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.list_lote_products(db, lot_id)
    except Exception:
        raise HTTP_DATABASE_ERROR


@assignments_router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_assignment(data: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.create_assignment(db, data)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@assignments_router.patch("/{assignment_id}", response_model=AssignmentRead)
async def update_assignment(assignment_id: uuid.UUID, data: AssignmentUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await CateringService.update_assignment(db, assignment_id, data)
    except LookupError:
        raise HTTP_ASSIGNMENT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@assignments_router.get("/{assignment_id}", response_model=AssignmentRead)
async def get_assignment(assignment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        obj = await CateringService.get_assignment(db, assignment_id)
        return obj
    except LookupError:
        raise HTTP_ASSIGNMENT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@assignments_router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(assignment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await CateringService.delete_assignment(db, assignment_id)
    except LookupError:
        raise HTTP_ASSIGNMENT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR


@lotes_router.put("/{lot_id}/assignment", response_model=AssignmentRead)
async def upsert_assignment_for_lote(
    lot_id: uuid.UUID, flight: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    try:
        return await CateringService.upsert_assignment_for_lote(db, lot_id, flight=flight)
    except LookupError:
        raise HTTP_LOT_NOT_FOUND
    except Exception:
        raise HTTP_DATABASE_ERROR

