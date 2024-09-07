from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2

from api.v1.models import User
from api.core.base.async_services import AsyncServices


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

class AuthService(AsyncServices):
    """
    Service class for authentication
    """
    async def create(self):
        """
        Create
        """
        pass

    async def fetch(self):
        """
        Create
        """
        pass

    async def fetch_all(self):
        """
        Create
        """
        pass

    async def update(self):
        """
        Create
        """
        pass

    async def delete(self):
        """
        Create
        """
        pass

    async def get_current_current_user(
        self,
        token: Annotated[OAuth2, Depends(oauth2_scheme)]
    ) -> Optional[User]:
        """
        
        """
        return None


auth_service = AuthService()
