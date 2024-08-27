from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from api.v1.models.base_model import Mixin
from api.db.database import Base

class User(Mixin, Base):
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
