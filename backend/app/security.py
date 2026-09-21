"""Password hashing + JWT session tokens for the AUTH STUB (dev/staging only)."""
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta

from .config import get_jwt_secret, get_session_ttl_minutes

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, email: str, token_version: int, jti: str) -> tuple[str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(minutes=get_session_ttl_minutes())
    payload = {
        "sub": user_id, "email": email, "ver": token_version,
        "jti": jti, "type": "access", "exp": expires,
        "stub": True,  # AUTH STUB marker present in every token
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM), expires


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
