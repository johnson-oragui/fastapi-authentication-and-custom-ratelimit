from sqlalchemy import String, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from passlib.context import CryptContext
from datetime import datetime

from api.v1.models.base_model import Mixin
from api.db.database import Base
from api.utils.settings import settings

SECRET_KEY: str = settings.SECRET_KEY

password_context: CryptContext = CryptContext(
    schemes=['bcrypt'],
    deprecated='auto'
)

class User(Mixin, Base):
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    password: Mapped[str] = mapped_column(nullable=True)
    idempotency_key: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    blocked_reason: Mapped[str] = mapped_column(nullable=True)
    lockout_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    def set_password(self, plain_password: str) -> None:
        '''
        Hashes user password using bcrypt
        '''
        if not isinstance(plain_password, str) or not plain_password:
            raise ValueError(f'{plain_password} must be a string')
        hashed_password: str = password_context.hash(plain_password)
        self.password = hashed_password

    def verify_password(self, plain_password: str) -> bool:
        '''
        Compares the hashed password with provided password
        '''
        if not plain_password:
            raise ValueError(f'{plain_password} must be provided')
        return password_context.verify(
            secret=plain_password,
            hash=self.password
        )
