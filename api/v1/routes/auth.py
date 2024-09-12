from typing import Annotated
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.utils.check_rate_limit import check_rate_limits_sync
from api.utils.background.producer import send_to_queue_sync
from api.v1.services.auth import (RegisterUserResponse,
                                  auth_service,
                                  RegisterUserSchema,
                                  oauth2_scheme,
                                  OAuth2,
                                  AccessToken,
                                  LogOutResponse)
from api.db.database import get_db
from api.v1.schemas.user import LoginUserSchema, LoginUserResponse


auth = APIRouter(prefix='/auth', tags=['AUTH'])

@auth.post('/login',
           status_code=status.HTTP_200_OK,
           response_model=LoginUserResponse)
async def login(request: Request,
                login_schema: LoginUserSchema,
                db: Annotated[AsyncSession, Depends(get_db)]):
    """Logs in a user.
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    return await auth_service.login_user(
        username=login_schema.username,
        password=login_schema.password,
        request=request,
        db=db,
        remember_me=login_schema.remember_me
    )


@auth.post('/register',
           status_code=status.HTTP_201_CREATED,
           response_model=RegisterUserResponse)
async def register(request: Request,
                   register_schema: RegisterUserSchema,
                   db: Annotated[AsyncSession, Depends(get_db)]):
    """Registers a user.
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    return await auth_service.create(
        user_schema=register_schema,
        db=db)

@auth.post('/token',
           status_code=status.HTTP_200_OK,
           response_model=AccessToken,
           include_in_schema=False)
async def token(request: Request,
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: Annotated[AsyncSession, Depends(get_db)]):
    """Logs in a user on openai.
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    
    return await auth_service.oauth2_authenticate(
        username=form_data.username,
        password=form_data.password,
        db=db,
        request=request
    )

@auth.get('/logout',
          status_code=status.HTTP_200_OK,
          response_model=LogOutResponse)
async def logout(token: Annotated[OAuth2, Depends(oauth2_scheme)]
                 ,request: Request):
    """
    Logs out a user.
    """
    return await auth_service.logout_user(str(token), request)

@auth.post('/others',
           status_code=status.HTTP_200_OK)
async def get(request: Request,
              token: Annotated[OAuth2, Depends(oauth2_scheme)],
              db: Annotated[AsyncSession, Depends(get_db)]):
    """Placeholder for other routes.
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    await auth_service.get_current_active_user(
        token=token,
        request=request,
        db=db)
    return {'message': 'others route attempt recorded'}
