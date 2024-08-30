from sqlalchemy.orm import (
    declared_attr,
    declarative_mixin,
    Mapped,
    mapped_column
)
from sqlalchemy import func, DateTime, String
from uuid import uuid4
from datetime import datetime


def get_id():
    """
    gets uuid as str
    """
    return str(uuid4())


@declarative_mixin
class Mixin:
    """
    Base class for model mixin
    """
    id: Mapped[str] = mapped_column(String, default=get_id, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
   

    @declared_attr
    @classmethod
    def __tablename__(cls):
        """
        table names
        """
        return f'{cls.__name__.lower()}s'
