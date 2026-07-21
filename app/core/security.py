from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from .config import settings

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password hashing configuration
password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Convert a plain-text password into a secure one-way hash.

    Registration:
    plain password → hash → database
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify the password entered during login
    against the hash stored in the database.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
) -> str:
    """
    Create a signed JWT access token.

    subject:
    Identifies the user the token belongs to.
    We will pass the user's ID as a string.
    """

    # Calculate the exact UTC time when the token expires.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    # JWT payload.
    # "sub" is the standard JWT claim for the token subject.
    # "exp" is the standard expiration claim.
    payload = {"sub": subject, "exp": expire, "type": "access"}

    # Sign the token using our private SECRET_KEY.
    # Anyone changing the payload will invalidate the signature.
    access_token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return access_token


def create_refresh_token(subject: str) -> str:
    """
    Create a signed JWT refresh token.

    Refresh tokens have a longer lifetime than access tokens
    and are used to generate new access tokens without
    requiring the user to log in again.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload = {"sub": subject, "exp": expire, "type": "refresh"}

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(
    token: str,
) -> dict:
    """
    Verify JWT signature.

    Verify expiration.

    Return payload.
    """

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        return payload

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )


def verify_token_type(
    payload: dict,
    expected_type: str,
) -> None:
    """
    Ensure the JWT is being used for the correct purpose.

    Example:
    Access Token  -> Protected APIs
    Refresh Token -> Refresh endpoint
    """

    token_type = payload.get("type")

    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected {expected_type} token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
