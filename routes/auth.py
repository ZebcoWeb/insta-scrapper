from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Form
from jose import jwt

from models import Users
from config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from utilities.utils import hash_password
from utilities.depends import get_current_user
from utilities.responses import SuccessResponse, ErrorResponse



router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt
    

@router.post("/register")
async def register(
    username: str = Form(..., min_length=4, max_length=20), 
    password: str = Form(..., min_length=8, max_length=35)
):
    if await Users.find_one(Users.username==username).exists():
        raise ErrorResponse("Username already exists")
    
    await Users(
        username=username, 
        password=hash_password(password)
    ).save()
    return SuccessResponse("User registered successfully")


@router.post("/login")
async def login(
    username: str = Form(..., min_length=4, max_length=20), 
    password: str = Form(..., min_length=8, max_length=35)
):
    user = await Users.find_one(Users.username==username)
    if not user:
        raise ErrorResponse("Invalid username")
    elif user.password != hash_password(password):
        raise ErrorResponse("Invalid password")
    
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    data = {"access_token": access_token, "token_type": "bearer"}
    return SuccessResponse(
        "Login success",
        data=data
    )

@router.get("/me")
def me(current_user = Depends(get_current_user)):
    return current_user

