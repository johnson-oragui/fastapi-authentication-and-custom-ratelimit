from typing import Annotated, Optional
import logging
import logging.handlers
from fastapi.responses import JSONResponse
from fastapi import Request, status, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from celery.exceptions import CeleryError
from pika.exceptions import AMQPError

from api.v1.services.auth import auth_service, User


FORMAT = '%(asctime)s %(clientip)-15s %(user)-8s %(message)s'

async def get_current_user(request: Request):
    """
    Gets the current user
    """
    try:
        return await auth_service.get_current_current_user(request)
    except Exception:
        return

logging.basicConfig(
    level=logging.ERROR,
    format=FORMAT,
    handlers=[
        logging.handlers.RotatingFileHandler(
            filename='error.log',
            backupCount=100,
            maxBytes=100000
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Custom exception handler class
class GlobalExceptionHandler:
    """
    Custom error handler class
    """
    @staticmethod
    async def exception(
        request: Request,
        exc: Exception):
        """
        Handles any exception
        """
        current_user = await get_current_user(request)
        logger.error(
            msg=f'Unhandled exception: {exc}',
            stack_info=True,
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f'An unexpected error occured'
            }
        )

    @staticmethod
    async def handle_http_exception(
        request: Request,
        exc: HTTPException
    ):
        """
        Handles Http exceptions
        """
        current_user = await get_current_user(request)
        logger.exception(
            msg=f'HTTP exceptions: {exc.detail}',
            stack_info=True, exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'status': False,
                'status_code': exc.status_code,
                'message': exc.detail
            }
        )

    @staticmethod
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError):
        """
        Handles validation exceptions
        """
        current_user = await get_current_user(request)
        logger.error(
            msg=f"Validation error: {exc.errors()}",
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder({
                'status': False,
                'status_code': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': exc.errors(),
                'body': exc.body
            })
        )

    @staticmethod
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError):
        """
        Handles sqlslchemy related excptions
        """
        current_user = await get_current_user(request)
        logger.error(
            msg=f"SQLAlchemy error: {exc}",
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': f'An unexpected error occured'
            }
        )
    
    @staticmethod
    async def redis_exception_handler(
        request: Request,
        exc: RedisError):
        """
        Handles redis esceprion
        """
        current_user = await get_current_user(request)
        logger.error(
            f"Redis error: {exc}",
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                'status': False,
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
                'message': f'A Redis error occured'
            }
        )

    @staticmethod
    async def rabbitmq_exception_handler(
        request: Request,
        exc: AMQPError):
        """
        Handles rabbitmq exceptions
        """
        current_user = await get_current_user(request)
        logger.error(
            f"RabbitMQ error: {exc}",
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                'status': False,
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
                'message': f'A RabbitMQ error occurred'
            }
        )

    @staticmethod
    async def celery_exception_handler(
        request: Request,
        exc: CeleryError):
        """
        Handles celery exceptions
        """
        current_user = await get_current_user(request)
        logger.error(
            f"Celery error: {exc}",
            exc_info=True,
            extra={
                'clientip': request.client.host,
                'user': current_user.first_name if current_user else None
            }
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'status': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': f'A Celery error occurred'
            }
        )
