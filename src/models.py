from sqlalchemy.orm import Mapped, mapped_column 
from sqlalchemy import text, func
from datetime import datetime 
from sqlalchemy.dialects.postgresql import UUID
import uuid



class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
        server_default= text("gen_random_uuid()")
    )

class Timestamp:
    created_at: Mapped[datetime] = mapped_column(server_default= func.now(), nullable = False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(),
                                                 onupdate=func.now(),
                                                 nullable=False)