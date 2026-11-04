# ============================================================
# SECTION 1: IMPORTS
# Import password hashing, JWT, environment, and time tools.
# ============================================================

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from jwt import InvalidTokenError
from pwdlib import PasswordHash


# ============================================================
# SECTION 2: LOAD ENVIRONMENT SETTINGS
# Load JWT settings from the backend .env file.
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


# ============================================================
# SECTION 3: JWT SETTINGS
# Read authentication settings from environment variables.
# ============================================================

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30",
    )
)


# ============================================================
# SECTION 4: SECURITY CONFIGURATION CHECK
# Stop application startup if the JWT secret is missing.
# ============================================================

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not configured."
    )


# ============================================================
# SECTION 5: PASSWORD HASHER
# Argon2 securely hashes user passwords.
# ============================================================

password_hasher = PasswordHash.recommended()


# ============================================================
# SECTION 6: HASH PASSWORD
# Convert a plain password into a secure hash.
# Never store the original password in the database.
# ============================================================

def hash_password(
    password: str,
) -> str:

    return password_hasher.hash(
        password
    )


# ============================================================
# SECTION 7: VERIFY PASSWORD
# Compare a login password with its stored hash.
# Return True only when the password matches.
# ============================================================

def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    return password_hasher.verify(
        password,
        password_hash,
    )


# ============================================================
# SECTION 8: CREATE ACCESS TOKEN
# Create a signed JWT access token for an authenticated user.
#
# The subject contains the database user ID as text.
# ============================================================

def create_access_token(
    user_id: int,
) -> str:

    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or user_id <= 0
    ):
        raise ValueError(
            "Invalid user ID"
        )

    now = datetime.now(
        timezone.utc
    )

    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# SECTION 9: DECODE ACCESS TOKEN
# Validate a JWT token and return its user ID.
#
# Invalid, expired, or malformed tokens return None.
# ============================================================

def decode_access_token(
    token: str,
) -> int | None:

    if (
        not isinstance(token, str)
        or not token.strip()
    ):
        return None

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        subject = payload.get(
            "sub"
        )

        if not isinstance(
            subject,
            str,
        ):
            return None

        user_id = int(
            subject
        )

        if user_id <= 0:
            return None

        return user_id

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):
        return None