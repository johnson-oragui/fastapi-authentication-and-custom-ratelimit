from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
from uuid import uuid4

from api.v1.models.base_model import Mixin
from api.db.database import Base

def get_id():
    """
    Gets the organization id.
    """
    return f'org_{str(uuid4())}'

class Organization(Mixin, Base):
    id: Mapped[str] = mapped_column(String, default=get_id, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(150), nullable=False)
    owner_email: Mapped[str] = mapped_column(String(50), nullable=False)
