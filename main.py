from typing import AsyncIterator
from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException, RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from aioredis.exceptions import RedisError
from celery.exceptions import CeleryError
from aio_pika.exceptions import AMQPError
from contextlib import asynccontextmanager

from api.utils.exceptions import GlobalExceptionHandler
from api.db.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    
    """
    print("Starting up application...")
    # Yield control back to FastAPI while app is running
    try:
        yield
    finally:
        await engine.dispose()
        print("Shutting down application...")

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

app.get("/", tags=['HOME'])
async def read_root():
    """
    Read root
    """
    return {"root": "fastapi"}

@app.get("/", status_code=status.HTTP_200_OK, tags=['HOME'])
async def root():
    """
    Root
    """
    return {"message": "Welcome to fastapi custom ratelimite"}

@app.get("/raise-http-exception", tags=['TEST EXCEPTIONS'])
async def raise_http_exception():
    """
    Raises HTTPException
    """
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/raise-validation-error", tags=['TEST EXCEPTIONS'])
async def raise_validation_error():
    """
    Raises RequestValidationError
    """
    raise RequestValidationError(["Invalid request"])

@app.get("/raise-sqlalchemy-error", tags=['TEST EXCEPTIONS'])
async def raise_sqlalchemy_error():
    """
    Raises SQLAlchemyError
    """
    raise SQLAlchemyError("Database error")

@app.get("/raise-generic-exception", tags=['TEST EXCEPTIONS'])
async def raise_generic_exception():
    """
    Raises Exception
    """
    raise Exception("Some unexpected error")

@app.get("/raise-redis-error", tags=['TEST EXCEPTIONS'])
async def raise_redis_error():
    """
    Raises RedisError
    """
    raise RedisError("Redis connection failed")

@app.get("/raise-rabbitmq-error", tags=['TEST EXCEPTIONS'])
async def raise_rabbitmq_error():
    """
    Raises AMQPError
    """
    raise AMQPError("RabbitMQ connection failed")

@app.get("/raise-celery-error", tags=['TEST EXCEPTIONS'])
async def raise_celery_error():
    """
    Raises CeleryError
    """
    raise CeleryError("Celery task execution failed")

app.add_exception_handler(
    RequestValidationError,
    GlobalExceptionHandler.validation_exception_handler
)

app.add_exception_handler(
    HTTPException,
    GlobalExceptionHandler.handle_http_exception
)

app.add_exception_handler(
    RedisError,
    GlobalExceptionHandler.redis_exception_handler
)

app.add_exception_handler(
    CeleryError,
    GlobalExceptionHandler.celery_exception_handler
)

app.add_exception_handler(
    AMQPError,
    GlobalExceptionHandler.rabbitmq_exception_handler
)

app.add_exception_handler(
    SQLAlchemyError,
    GlobalExceptionHandler.sqlalchemy_exception_handler
)

app.add_exception_handler(
    Exception,
    GlobalExceptionHandler.exception
)
