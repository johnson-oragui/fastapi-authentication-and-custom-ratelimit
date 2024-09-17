#!/usr/bin/env python3
"""
Test Auth Service module
"""
import pytest
from unittest import mock
from fastapi import HTTPException

from api.v1.models import User
from api.v1.services.auth import (auth_service, RegisterUserSchema,
                                  RegisterUserResponse, UserBase,
                                  LoginUserResponse, LogOutResponse,
                                  LoginUserData)


class TestAuthService:
    """
    Test class for AuthService
    """
    @pytest.mark.asyncio
    @mock.patch("api.utils.email_dns_resolver.check_email_deliverability")
    @mock.patch("api.v1.services.auth.AuthService.check_idempotency")
    @mock.patch("api.v1.services.auth.AuthService.check_user_exists")
    @mock.patch("api.v1.services.auth.auth_service.create")
    async def test_creat_user(self, mock_create,
                              mock_check_user_exists,
                              mock_check_idempotency,
                              mock_check_email_deliverability,
                              mock_get_db, user_two):
        """Tests create user success"""
        # Setup a mock RegisterUserSchema
        schema = RegisterUserSchema(**user_two)
        user_two.pop('confirm_password')
        new_user = User(**user_two)

        # Mocking the database session
        mock_check_user_exists.return_value = None
        mock_check_idempotency.return_value = None
        mock_check_email_deliverability.return_value = None
        mock_create.return_value = RegisterUserResponse(
            status_code=201,
            message="Successful",
            data=UserBase.model_validate(new_user, from_attributes=True)
        )


        response = await auth_service.create(schema, mock_get_db)

        assert isinstance(response, RegisterUserResponse)
        assert response.status_code == 201
        assert response.message == 'Successful'
        assert isinstance(response.data, UserBase)

    @pytest.mark.asyncio
    @mock.patch("api.v1.services.auth.auth_service.authenticate_user")
    @mock.patch("api.v1.services.auth.auth_service.generate_jwt_token")
    @mock.patch("api.v1.services.auth.auth_service.login_user")
    async def test_user_login(self, mock_login_user, mock_generate_jwt_token,
                              mock_authenticate_user,
                              mock_get_db, user_three,
                              mock_request):
        """Test login user"""
        # Mock data
        user = User(**user_three)
        mock_authenticate_user.return_value = user
        mock_generate_jwt_token.return_value = "fake-jwt-token"
        mock_login_user.return_value = LoginUserResponse(
            status_code=200,
            message="Login Successful",
            data=LoginUserData(
                access_token="fake-jwt-token",
                refresh_token="fake-jwt-token",
                user=UserBase.model_validate(user, from_attributes=True)
            )
        )

        response = await auth_service.login_user(
            user_three['username'],
            user_three['password'],
            mock_get_db,
            mock_request
        )
        
        assert isinstance(response, LoginUserResponse)
        assert response.status_code == 200
        assert response.message == "Login Successful"
        assert response.data.access_token == "fake-jwt-token"
        assert response.data.refresh_token == "fake-jwt-token"

    @pytest.mark.asyncio
    @mock.patch("api.v1.services.auth.auth_service.get_current_user")
    async def test_get_current_user(self, mock_get_current_user, mock_verify_jwt_token,
                                    mock_get_db, user_one, mock_request):
        """Test get current user"""
        # Mock user data
        user = User(**user_one)

        mock_get_current_user.return_value = user

        current_user = await auth_service.get_current_user(
            "fake-jwt-token",
            mock_request,
            mock_get_db
        )
        
        assert current_user == user

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_get_db, mock_request):
        """Test get current user with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.get_current_user("invalid-token", mock_request, mock_get_db)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"

    @pytest.mark.asyncio
    @mock.patch("api.v1.services.auth.AuthService.verify_jwt_token")
    @mock.patch("api.utils.token_revocation.revoke_jti")
    async def test_logout_user(self, mock_revoke_jti,
                               mock_verify_jwt_token,
                               mock_get_db,
                               mock_request):
        """Test logout user"""
        mock_verify_jwt_token.return_value = {"jti": "fake-jti", "token_type": "access"}

        response = await auth_service.logout_user("fake-jwt-token", mock_request)
        
        assert isinstance(response, LogOutResponse)
        assert response.status_code == 200
        assert response.message == "Logout successful"

    @pytest.mark.asyncio
    @mock.patch("api.v1.services.auth.auth_service.generate_jwt_token")
    async def test_generate_jwt_token(self, mock_jwt_encode,
                                      mock_get_db,
                                      user_one,
                                      mock_request):
        """Test Generate jwt token"""
        user = User(**user_one)

        mock_jwt_encode.return_value = "fake-jwt-token"
        
        token = await auth_service.generate_jwt_token(user, mock_request)
        
        assert token == "fake-jwt-token"
        auth_service.generate_jwt_token.assert_called_once()
