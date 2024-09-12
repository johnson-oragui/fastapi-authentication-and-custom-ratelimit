#!/usr/bin/env python3
"""
Auth Service module
"""
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from jose import jwt, JWTError
import hashlib
from uuid import uuid4

from api.v1.models import User
from api.core.base.async_services import AsyncServices
from api.v1.schemas.user import(RegisterUserSchema,
                                RegisterUserResponse,
                                AccessToken,
                                UserBase,
                                LoginUserData,
                                LoginUserResponse,
                                LogOutResponse)
from api.utils.settings import settings
from api.utils.background.producer import handle_login_attempt
from api.utils.auth_rate_limits import reset_failed_attempts
from api.utils.email_dns_resolver import check_email_deliverability
from api.utils.token_revocation import (store_jti_in_cache,
                                        check_active_jti,
                                        revoke_jti)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')

async def generate_idempotency_key(username: str, email: str):
    """
    Generates an idempotency key
    """
    key = f"{email}:{username}"
    return hashlib.sha256(key.encode()).hexdigest()

class AuthService(AsyncServices):
    """
    Service class for authentication
    """
    async def create(
        self, user_schema: RegisterUserSchema,
        db: AsyncSession):
        """
        Create
        """
        await check_email_deliverability(user_schema.email)
        # check if request had been made and successful with idempotency_key
        idempotency_key: str = await generate_idempotency_key(
            user_schema.username,
            user_schema.email
        )
        # returns a success response if idempotency jey already exists
        idempotency_response = await self.check_idempotency(idempotency_key, db)
        if idempotency_response:
            # return response to user
            return idempotency_response
        # throws a 409 if username or email already exists
        await self.check_user_exists(user_schema, db)
        # create a user model for the new user
        new_user: User = User(
            **user_schema.model_dump(
                exclude={
                    'password',
                    'confirm_password'
                }
            )
        )
        new_user.idempotency_key = idempotency_key
        # set a passwpord for the new user and save
        new_user.set_password(user_schema.password)
        db.add(new_user)
        await db.commit()

        # create a pydantic model from the new user
        user = UserBase.model_validate(
            new_user,
            from_attributes=True
        )

        return RegisterUserResponse(
            status_code=status.HTTP_201_CREATED,
            message='Successful',
            data=user
        )
        

    async def fetch(
        self, user_id: str,
        db: AsyncSession):
        """
        Featch a user with id
        """
        async with db:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            return user

    async def fetch_all(self):
        """
        Fetch all
        """
        pass

    async def update(self):
        """
        Update
        """
        pass

    async def delete(self):
        """
        Delete
        """
        pass

    async def check_idempotency(self, idempotency_key: str, db: AsyncSession):
        """
        Checks if the idempotency key already exists in the database.
        Returns a response if the user has already been registered.
        """
        stmt = select(User).where(
            User.idempotency_key == idempotency_key
        )
        result = await db.execute(stmt)
        user_exists = result.scalar_one_or_none()
        if user_exists:
            user = UserBase.model_validate(
                user_exists,
                from_attributes=True
            )
            return RegisterUserResponse(
                status_code=status.HTTP_201_CREATED,
                message='User already registered',
                data=user
            )
        

    async def check_user_exists(self, user_schema: RegisterUserSchema,
                                db: AsyncSession):
        """
        Checks if a user already exists with the provided email and also username.
        """
        # check if user's email already registered.
        email_stmt = select(User).where(
            User.email == user_schema.email
        )
        email_result = await db.execute(email_stmt)
        if email_result.scalar_one_or_none():
            message = 'email already exists.'
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message
            )
        # check if user's username already registered.
        username_stmt = select(User).where(
            User.username == user_schema.username 
        )
        username_result = await db.execute(username_stmt)
        if username_result.scalar_one_or_none():
            message = 'username already taken.'
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message
            )

    async def get_current_user(
        self,
        token: Annotated[OAuth2, Depends(oauth2_scheme)],
        request: Request,
        db: AsyncSession
    ) -> User:
        """
        Rtrieve the current user from the provided token.
        """
        # decode the token
        claims: dict = await self.verify_jwt_token(
            token=str(token),
            request=request
        )
        # check if the decoded token is a refresh token
        if claims.get('token_type') == 'refresh':
            # raise an exception
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='cannot use refresh token')
        # use the user_id to search for the user
        user_id = claims.get('user_id')
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        # raise an exception if no user with id is found
        if not user:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
            # return the user
        return user

    async def get_current_active_user(
        self,
        token: Annotated[OAuth2, Depends(oauth2_scheme)],
        request: Request,
        db: AsyncSession
    ) -> User:
        """
        Retrieves active users.
        """
        # check the current time
        now = datetime.now(timezone.utc)
        # retrieve the current user
        user: User = await self.get_current_user(
            token=token,
            request=request,
            db=db)
        # check if user is blocked
        if user.is_blocked:
            message = 'Account locked due to multiple failed login attempts'
            # calculate time remaining to unblock the user
            exp_time = user.lockout_expires_at.timestamp() - now.timestamp()
            # raise an exception with remaining time to user unblock
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'{message}. Try again in {exp_time} seconds'
            )
        # check if user is still active
        if not user.is_active:
            # raise an exception
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User is Inactive'
            )
        # return active user
        return user

    async def authenticate_user(self,
                                username: str,
                                password: str,
                                db: AsyncSession):
        """
        Authenticates a user.
        """
        # set the current time
        now = datetime.now(timezone.utc)
        # retrieve the user using username or password
        stmt = select(User).where(
            or_(
                User.email == username,
                User.username == username
            )
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        # if no user with provided details is found
        if not user:
            # raise an exception
            raise HTTPException(
                status_code=400,
                detail="Incorrect username or password"
            )

        # check if user is blocked
        if user.is_blocked and user.lockout_expires_at > now:
            # calculate time left for user unblock
            exp = user.lockout_expires_at
            exp_in = (exp.timestamp() - now.timestamp())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Locked out. Try again in {exp_in} seconds'
            )
        # check if user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'User is Inactive'
            )

        # check if the user provided the right password
        password_valid = user.verify_password(password)
        # check if password is correct
        if not password_valid:
            # pass the user_id to increment and handle failed login attempts
            handle_login_attempt(user.id)
            # raise an exception if there is a password mismatch
            raise HTTPException(
                status_code=400,
                detail="Incorrect username or password"
            )

        # remove/reset the user_id from failed attempt after a successful login
        reset_failed_attempts(user.id)
        # unblock user after lock-time expires and user login is successful
        if user.is_blocked or user.lockout_expires_at:
            user.is_blocked = False
            user.lockout_expires_at = None
            await db.commit()
        # return user
        return user

    async def login_user(self, username: str, password: str,
                         db: AsyncSession, request: Request, remember_me: bool = False):
        """
        Logs in a user.
        """
        # check for correct login fields
        logged_in_user = await self.authenticate_user(username, password, db)
        # create a pydantic model for user
        user = UserBase.model_validate(
            logged_in_user,
            from_attributes=True
        )
        # generate access token
        access_token = await self.generate_jwt_token(
            logged_in_user,
            request=request,
            remember_me=remember_me
        )
        # generate refresh token
        refresh_token = await self.generate_jwt_token(
            logged_in_user,
            request=request,
            token_type='refresh'
        )
        # create a response and return to he user
        user_data = LoginUserData(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )

        return LoginUserResponse(
            status_code=status.HTTP_200_OK,
            message='Login Successful',
            data=user_data
        )

    async def oauth2_authenticate(self,
                                username: str,
                                password: str,
                                db: AsyncSession,
                                request: Request):
        """
        Authenticates a user for the openapi docs usage.
        """
        # authenticate a user using provided username and password
        user = await self.authenticate_user(username, password, db)
        # generate access token
        access_token = await self.generate_jwt_token(
            user,
            request=request
        )
        # return access token
        return AccessToken(
            access_token=access_token
        )

    async def logout_user(self, token: str, request: Request):
        """

        """
        claims: dict = await self.verify_jwt_token(
            token=token,
            request=request
        )
        jti: str = claims.get('jti', '')
        token_type: str = claims.get('token_type', '')
        if not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='User must be logged in.')
        revoke_jti(jti, token_type)
        return LogOutResponse(
            status_code=status.HTTP_200_OK,
            message='Logout successful'
        )
        

    async def generate_jwt_token(self, user: User, request: Request,
                                 token_type: str = 'access',
                                 remember_me: bool = False) -> str:
        """
        Generate access/refresh token.
        """
        # Generate JTI (JWT ID)
        jti = str(uuid4())
        # set the current time
        now = datetime.now(timezone.utc)
        # Get the client IP address
        user_ip = request.client.host
        # Get the User-Agent header
        user_agent = request.headers.get('user-agent')

        # set expiry time based on the token-type to generate
        if token_type == 'access':
            # check if remeber_me is true
            if remember_me:
                exp: int = settings.REMEMBER_ME_EXPIRE
                # set a long lived access token
                access_expire = now + timedelta(days=exp)
            else:
                # if remeber_me is false
                exp: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES
                # set a short lived accesss token
                access_expire = now + timedelta(minutes=exp)
        elif token_type == 'refresh':
            exp = settings.REFRESH_TOKEN_EXPIRE
            refresh_expire = now + timedelta(days=exp)
        else:
            raise ValueError('token-type must either be access or refresh')
        
        # set the payloads to be encoded
        claims = {
            'user_id': user.id,
            'token_type': token_type,
            'jti': jti,
            'iat': now,
            'ip': user_ip,
            'user_agent': user_agent,
            'exp': (access_expire
                    if token_type == 'access'
                    else refresh_expire)
        }
        # generate and return the token
        token = jwt.encode(
            claims=claims,
            key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        store_jti_in_cache(jti, exp, token_type)
        return token

    async def verify_jwt_token(self, token: str, request: Request) -> dict:
        """
        Verify JWT token and check if the JTI is still active (i.e., not revoked).
        """
        try:
            # decode and return the token.
            claims: dict = jwt.decode(
                token=token,
                key=settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            token_type = claims.get('token_type', '')
            # Check if the JTI has been revoked
            jti = claims.get('jti', '')
            if not check_active_jti(jti, token_type):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
            )

            # Validate IP address
            token_ip = claims.get('ip')
            request_ip = request.client.host
            if token_ip != request_ip:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="IP address mismatch"
                )

            # Validate User-Agent
            token_user_agent = claims.get('user_agent')
            request_user_agent = request.headers.get('user-agent')
            if token_user_agent != request_user_agent:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User-Agent mismatch"
                )

            return claims
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# create an instance of the AuthService class
auth_service = AuthService()
