from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List

from sqlalchemy import (
    String, Integer, Date, Enum as SAEnum, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models import UUIDPrimaryKey, Timestamp

class AssignmentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    LOADED = "loaded"
    REJECTED = "rejected"


class Product(Base, UUIDPrimaryKey, Timestamp):
    __tablename__ = "products"

    product_code: Mapped[str] = mapped_column(String(55), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(120), nullable=False)
    lot_items: Mapped[List["LoteProduct"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )


class Lote(Base, UUIDPrimaryKey, Timestamp):
    __tablename__ = "lotes"

    lote_code: Mapped[str] = mapped_column(String(55), nullable=False, unique=True, index=True)
    items: Mapped[List["LoteProduct"]] = relationship(
        back_populates="lote",
        cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        back_populates="lote",
        cascade="all, delete-orphan"
    )


class LoteProduct(Base, UUIDPrimaryKey, Timestamp):
    __tablename__ = "lote_products"

    lot_id: Mapped[str] = mapped_column(ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    certification_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    lote: Mapped["Lote"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="lot_items")


class Assignment(Base, UUIDPrimaryKey, Timestamp):
    __tablename__ = "assignments"

    lot_id: Mapped[str] = mapped_column(
        ForeignKey("lotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flight_assigned: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(
            AssignmentStatus,
            name="assignmentstatus",
            values_callable=lambda e: [m.value for m in e],  
            create_constraint=False,  
        ),
        nullable=False,
        default=AssignmentStatus.DRAFT,
        server_default=AssignmentStatus.DRAFT.value,  
        index=True,
    )

    lote: Mapped["Lote"] = relationship(back_populates="assignments")
