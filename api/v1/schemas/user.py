import re
from decouple import config
from typing import Annotated, Optional, Literal, Dict, List, Union
from pydantic import (BaseModel,
                      ConfigDict,
                      model_validator,
                      StringConstraints,
                      EmailStr,
                      Field)
from email_validator import validate_email, EmailNotValidError
from bleach import clean
import unicodedata

TESTING = config('TESTING')

if TESTING:
    TEST = True
else:
    TEST = False

class RegisterUserSchema(BaseModel):
    email: Annotated[
        EmailStr,
        StringConstraints(
            min_length=11,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Johnson@example.com'])
    username: Annotated[
        str,
        StringConstraints(
            max_length=20,
            min_length=3,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Johnson1234'])
    first_name: Annotated[
        str,
        StringConstraints(
            max_length=20,
            min_length=3,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Johnson'])
    last_name: Annotated[
        str,
        StringConstraints(
            max_length=20,
            min_length=3,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Doe'])
    password: Annotated[
        str,
        StringConstraints(
            max_length=30,
            min_length=8,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Johnson1234@'])
    confirm_password: Annotated[
        str,
        StringConstraints(
            max_length=30,
            min_length=8,
            strip_whitespace=True,
            strict=True
        )
    ] = Field(examples=['Johnson1234@'])

    @model_validator(mode='before')
    @classmethod
    def validate_fields(cls, values: dict):
        """
        Validates all fields
        """
        password: str = values.get('password', '')
        confirm_password = values.get('confirm_password', '')
        email: EmailStr = values.get('email', '')
        first_name: str = values.get('first_name', '')
        last_name: str = values.get('last_name', '')
        username: str = values.get('username', '')

        # not allowed characters for username, first_name, and last_name
        name_disallowed = '1234567890!@~`#$%^&*()_+=-,.<>/?"\|'
        # allowed special characters for password
        password_allowed = '!@#&-_,.'
        # emails liable to fraud
        blacklisted_domains = [
            'example.com', 'mailinator.com', 'tempmail.com'
        ]
        # offensive words
        offensive_words = [
            'fuck', 'ass', 'pussy'
        ]
        # reserved usernames
        reserved_usernames = [
            'admin', 'root', 'superuser', 'superadmin'
        ]

        # check for reserved username
        if username in reserved_usernames:
            raise ValueError('Username is reserved and cannot be used')

        # check for offfensive words
        for word in offensive_words:
            if word in username:
                raise ValueError('Username contains offensive language')

        for c in first_name:
            if c == ' ':
                raise ValueError('use of white space is not allowed in first_name')
            if c in name_disallowed:
                raise ValueError(f'{c} is not allowed in first_name')
        for c in last_name:
            if c == ' ':
                raise ValueError('use of white space is not allowed in last_name')
            if c in name_disallowed:
                raise ValueError(f'{c} is not allowed in last_name')
        for c in username:
            if c == ' ':
                raise ValueError('use of white space is not allowed in username')
            if c in '!@~`#$%^&*()_+=,.<>/?"\|':
                raise ValueError(f'{c} is not allowed in username')

        values['first_name'] = clean(first_name.lower())
        values['first_name'] = unicodedata.normalize('NFKC', first_name)
        
        values['last_name'] = clean(last_name.lower())
        values['last_name'] = unicodedata.normalize('NFKC', last_name)

        values['username'] = clean(username.lower())
        values['username'] = unicodedata.normalize('NFKC', username)

        try:
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            pattern = re.compile(email_regex)
            email = validate_email(
                email,
                check_deliverability=True,
                test_environment=TEST
            ).normalized
            if not pattern.match(email):
                raise ValueError(f'{email} is invalid')
            values['email'] = email
        except EmailNotValidError as exc:
            raise ValueError(exc)

        email_domain = email.split('@')[1]
        if email_domain in blacklisted_domains:
            raise ValueError(f'{email_domain} is not allowed for registration')

        if not any(char for char in password if char.islower()):
            raise ValueError(f'{password} must contain at least one lowercase letter')
        if not any(char for char in password if char.isupper()):
            raise ValueError(f'{password} must contain at least one uppercase letter')
        if not any(char for char in password if char.isdigit()):
            raise ValueError(f'{password} must contain at least one digit character')
        if not any(char for char in password if char in password_allowed):
            raise ValueError(f'{password} must contain at least one of these special characters {password_allowed}')
        if password != confirm_password:
            raise ValueError(f'{password} and {confirm_password} must match')

        return values


class UserBase(BaseModel):
    id: str = Field(examples=['1234ed.4455tf...'])
    email: str = Field(examples=['Johnson@example.com'])
    username: str = Field(examples=['Johnson1234'])
    first_name: str = Field(examples=['Johnson'])
    last_name: str = Field(examples=['Doe'])

    model_config = ConfigDict(from_attributes=True)

class RegisterUserResponse(BaseModel):
    status_code: int = Field(examples=[201])
    message: str = Field(examples=['Successful'])
    data: UserBase

class AccessToken(BaseModel):
    access_token: str = Field(examples=['12wxc3.55v44f3A.4f5gh5n67yn...'])
    token_type: str = Field(default='Bearer')
    
class RefreshToken(BaseModel):
    refresh_token: str = Field(examples=['12wxc3.55v44f3A.4f5gh5n67yn...'])

class LoginUserData(BaseModel):
    user: UserBase
    access_token: str = Field(examples=['12wxc3.55v44f3A.4f5gh5n67yn...'])
    refresh_token: str = Field(examples=['12wxc3.55v44f3A.4f5gh5n67yn...'])

class LoginUserResponse(BaseModel):
    status_code: int = Field(examples=[201])
    message: str = Field(examples=['Successful'])
    data: LoginUserData

class LoginUserSchema(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=3
        )
    ] = Field(examples=['johnson@example.com', 'Johnson123'])

    password: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=8
        )
    ] = Field(
        examples=['Johnson1234#']
    )

    @model_validator(mode='before')
    @classmethod
    def validate_data(cls, values: dict):
        """
        Validates login data.
        """
        username: str = values.get('username', '')
        password: str = values.get('password', '')

        password_allowed = '!@#&-_,.'

        values['username'] = username.lower()

        if not any(char for char in password if char.islower()):
            raise ValueError(f'{password} must contain at least one lowercase letter')
        if not any(char for char in password if char.isupper()):
            raise ValueError(f'{password} must contain at least one uppercase letter')
        if not any(char for char in password if char.isdigit()):
            raise ValueError(f'{password} must contain at least one digit character')
        if not any(char for char in password if char in password_allowed):
            raise ValueError(f'{password} must contain at least one of these special characters {password_allowed}')

        return values
