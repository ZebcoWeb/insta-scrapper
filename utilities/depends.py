from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from models import Users
from config import SECRET_KEY, JWT_ALGORITHM
from utilities.responses import ErrorResponse



async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login"))):
    validation_error = ErrorResponse(
        message="Could not validate credentials",
        status_code=401
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise validation_error
    except JWTError:
        raise validation_error
    user = await Users.find_one(Users.username==username)
    if not user:
        raise validation_error
    return {
        "username": user.username,
        "created_at": user.created_at,
    }

def is_authenticated(current_user: dict = Depends(get_current_user)):
    if not current_user:
        return False
    return True