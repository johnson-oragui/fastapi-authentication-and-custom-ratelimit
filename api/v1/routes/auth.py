from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, Request

from api.utils.check_rate_limit import check_rate_limits_sync
from api.utils.background.producer import send_to_queue_sync


auth = APIRouter(prefix='/auth', tags=['AUTH'])

@auth.post('/login',
           status_code=status.HTTP_200_OK)
async def login(request: Request, login_schema: dict):
    """sumary_line
    
        Keyword arguments:
            argument -- description
        Return:
            return_description
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    return {'message': 'Login attempt recorded'}


@auth.post('/register',
           status_code=status.HTTP_200_OK)
async def register(request: Request, login_schema: dict):
    """sumary_line
    
        Keyword arguments:
            argument -- description
        Return:
            return_description
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    return {'message': 'Register attempt recorded'}


@auth.post('/others',
           status_code=status.HTTP_200_OK)
async def get(request: Request, login_schema: dict):
    """sumary_line
    
        Keyword arguments:
            argument -- description
        Return:
            return_description
    """
    check_rate_limits_sync(request)
    user_ip: str = request.client.host
    path: str = request.url.path
    message_body: str = f'{user_ip},{path}'
    send_to_queue_sync(message_body)
    return {'message': 'get attempt recorded'}
