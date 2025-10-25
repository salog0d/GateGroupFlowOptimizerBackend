from __future__ import annotations

import uuid
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Product, Lote, LoteProduct, Assignment, AssignmentStatus
from .schemas import (
    ProductCreate, ProductUpdate,
    LoteCreate, LoteUpdate,
    LoteProductCreate, LoteProductUpdate,
    AssignmentCreate, AssignmentUpdate,
)


class CateringService:

    @staticmethod
    async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
        res = await db.execute(select(Product).where(Product.product_code == data.product_code))
        if res.scalar_one_or_none():
            raise ValueError("product_code already exists")
        obj = Product(product_code=data.product_code, product_name=data.product_name)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def update_product(db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        obj = await db.get(Product, product_id)
        if not obj:
            raise LookupError("Product not found")
        if data.product_code is not None:
            obj.product_code = data.product_code
        if data.product_name is not None:
            obj.product_name = data.product_name
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> None:
        obj = await db.get(Product, product_id)
        if not obj:
            raise LookupError("Product not found")
        await db.delete(obj)
        await db.commit()

    @staticmethod
    async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
        obj = await db.get(Product, product_id)
        if not obj:
            raise LookupError("Product not found")
        return obj

    @staticmethod
    async def create_lote(db: AsyncSession, data: LoteCreate) -> Lote:
        res = await db.execute(select(Lote).where(Lote.lote_code == data.lote_code))
        if res.scalar_one_or_none():
            raise ValueError("lote_code already exists")
        obj = Lote(lote_code=data.lote_code)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def update_lote(db: AsyncSession, lot_id: uuid.UUID, data: LoteUpdate) -> Lote:
        obj = await db.get(Lote, lot_id)
        if not obj:
            raise LookupError("Lote not found")
        if data.lote_code is not None:
            obj.lote_code = data.lote_code
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete_lote(db: AsyncSession, lot_id: uuid.UUID) -> None:
        obj = await db.get(Lote, lot_id)
        if not obj:
            raise LookupError("Lote not found")
        await db.delete(obj)
        await db.commit()

    @staticmethod
    async def get_lote(db: AsyncSession, lot_id: uuid.UUID) -> Lote:
        obj = await db.get(Lote, lot_id)
        if not obj:
            raise LookupError("Lote not found")
        return obj

    @staticmethod
    async def get_lote_detailed(db: AsyncSession, lot_id: uuid.UUID) -> Lote:
        q = (
            select(Lote)
            .where(Lote.id == str(lot_id))
            .options(
                selectinload(Lote.items).selectinload(LoteProduct.product),
                selectinload(Lote.assignments),
            )
        )
        res = await db.execute(q)
        obj = res.scalar_one_or_none()
        if not obj:
            raise LookupError("Lote not found")
        return obj

    @staticmethod
    async def add_or_increment_lote_product(db: AsyncSession, data: LoteProductCreate) -> LoteProduct:
        if not await db.get(Lote, data.lot_id):
            raise LookupError("Lote not found")
        if not await db.get(Product, data.product_id):
            raise LookupError("Product not found")
        q = select(LoteProduct).where(
            and_(LoteProduct.lot_id == str(data.lot_id), LoteProduct.product_id == str(data.product_id))
        )
        res = await db.execute(q)
        lp = res.scalar_one_or_none()
        if lp:
            lp.quantity += data.quantity
            lp.expiration_date = data.expiration_date or lp.expiration_date
            lp.certification_date = data.certification_date or lp.certification_date
        else:
            lp = LoteProduct(
                lot_id=str(data.lot_id),
                product_id=str(data.product_id),
                quantity=data.quantity,
                expiration_date=data.expiration_date,
                certification_date=data.certification_date,
            )
            db.add(lp)
        await db.commit()
        await db.refresh(lp)
        return lp

    @staticmethod
    async def update_lote_product(db: AsyncSession, lote_product_id: uuid.UUID, data: LoteProductUpdate) -> LoteProduct:
        lp = await db.get(LoteProduct, lote_product_id)
        if not lp:
            raise LookupError("LoteProduct not found")
        if data.quantity is not None:
            lp.quantity = data.quantity
        if data.expiration_date is not None:
            lp.expiration_date = data.expiration_date
        if data.certification_date is not None:
            lp.certification_date = data.certification_date
        await db.commit()
        await db.refresh(lp)
        return lp

    @staticmethod
    async def remove_lote_product(db: AsyncSession, lote_product_id: uuid.UUID) -> None:
        lp = await db.get(LoteProduct, lote_product_id)
        if not lp:
            raise LookupError("LoteProduct not found")
        await db.delete(lp)
        await db.commit()

    @staticmethod
    async def list_lote_products(db: AsyncSession, lot_id: uuid.UUID) -> List[LoteProduct]:
        q = (
            select(LoteProduct)
            .where(LoteProduct.lot_id == str(lot_id))
            .options(selectinload(LoteProduct.product))
        )
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def create_assignment(db: AsyncSession, data: AssignmentCreate) -> Assignment:
        if not await db.get(Lote, data.lot_id):
            raise LookupError("Lote not found")
        obj = Assignment(
            lot_id=str(data.lot_id),
            flight_assigned=data.flight_assigned,
            status=data.status,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def update_assignment(db: AsyncSession, assignment_id: uuid.UUID, data: AssignmentUpdate) -> Assignment:
        obj = await db.get(Assignment, assignment_id)
        if not obj:
            raise LookupError("Assignment not found")
        if data.flight_assigned is not None:
            obj.flight_assigned = data.flight_assigned
        if data.status is not None:
            obj.status = data.status
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> None:
        obj = await db.get(Assignment, assignment_id)
        if not obj:
            raise LookupError("Assignment not found")
        await db.delete(obj)
        await db.commit()

    @staticmethod
    async def get_assignment(db: AsyncSession, assignment_id: uuid.UUID) -> Assignment:
        obj = await db.get(Assignment, assignment_id)
        if not obj:
            raise LookupError("Assignment not found")
        return obj

    @staticmethod
    async def upsert_assignment_for_lote(
        db: AsyncSession, lot_id: uuid.UUID, flight: Optional[str], status: AssignmentStatus = AssignmentStatus.DRAFT
    ) -> Assignment:
        res = await db.execute(select(Assignment).where(Assignment.lot_id == str(lot_id)))
        obj = res.scalar_one_or_none()
        if obj:
            if flight is not None:
                obj.flight_assigned = flight
            obj.status = status
        else:
            if not await db.get(Lote, lot_id):
                raise LookupError("Lote not found")
            obj = Assignment(lot_id=str(lot_id), flight_assigned=flight, status=status)
            db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @staticmethod
    async def get_lotes_by_product(db: AsyncSession, product_id: uuid.UUID) -> List[Lote]:
        q = (
            select(Lote)
            .join(Lote.items)
            .where(LoteProduct.product_id == str(product_id))
            .options(selectinload(Lote.items).selectinload(LoteProduct.product))
        )
        res = await db.execute(q)
        return list(res.scalars().all())

    @staticmethod
    async def get_products_in_lote(db: AsyncSession, lot_id: uuid.UUID) -> List[Product]:
        q = (
            select(Product)
            .join(Product.lot_items)
            .where(LoteProduct.lot_id == str(lot_id))
        )
        res = await db.execute(q)
        return list(res.scalars().all())
