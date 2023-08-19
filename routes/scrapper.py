import json, http.cookies

from typing import Union

from fastapi import APIRouter, Form, Depends

from models import InstaUsers
from utilities.utils import generate_digits
from utilities.api import InstaAPI
from utilities.depends import is_authenticated
from utilities.responses import SuccessResponse, ErrorResponse


router = APIRouter(
    prefix="/insta",
    tags=["insta"],
)
api = InstaAPI()



@router.post("/login")
async def login(
    username: str = Form(...), 
    password: str = Form(...),
    is_authenticated: bool = Depends(is_authenticated)
):
    if await InstaUsers.find_one(InstaUsers.username == username).exists():
        raise ErrorResponse(
            "Instagram User already exists",
            status_code=400
        )

    cookies = await api.login(username, password)
    cookies_str = json.dumps(cookies)

    user = await InstaUsers(
        user_id=generate_digits(),
        instagram_id=cookies.get("ds_user_id"),
        username=username,
        cookies=cookies_str
    ).save()

    data = {"user_id": user.user_id}
    return SuccessResponse(
        "Instagram Login successful",
        data=data
    )


@router.post("/set-cookie")
async def set_cookie(
    username: str = Form(...), 
    cookies: str = Form(...),
    is_authenticated: bool = Depends(is_authenticated)
):
    try:
        cookies = json.loads(cookies)
    except json.JSONDecodeError:
        cookies = http.cookies.SimpleCookie(cookies)
        cookies = {key: morsel.value for key, morsel in cookies.items()}
    
    instagram_id = cookies.get("ds_user_id")
    cookies_str = json.dumps(cookies)
    user = await InstaUsers.find_one(InstaUsers.username == username)
    
    if not user:
        user = InstaUsers(
            user_id=generate_digits(),
            instagram_id=instagram_id, 
            username=username, 
            cookies=cookies_str
        )
        await user.save()
        data = {"user_id": user.user_id}
        return SuccessResponse(
                "Cookie set successfully",
                data=data
            )
    else:
        user.cookies = cookies_str
        await user.save()
        data = {"user_id": user.user_id}
        return SuccessResponse(
            "Cookie updated successfully",
            data=data
        )


@router.get("/followers/")
async def followers(
    username: Union[str, None] = None, 
    user_id: Union[str, None] = None,
    is_authenticated: bool = Depends(is_authenticated)
):
    if not username and not user_id:
        raise ErrorResponse(
            "Username or user_id is required",
            status_code=400
        )
    if not username:
        user = await InstaUsers.find_one(InstaUsers.user_id == user_id)
    else:
        user = await InstaUsers.find_one(InstaUsers.username == username)
    if user:
        print(user.cookies_to_dict())
        users = await api.fetch_followers(user.instagram_id, user.cookies_to_dict())
        return SuccessResponse(
            "Followers fetched successfully",
            data=users
        )
    else:
        raise ErrorResponse(
            "User not found",
            status_code=404
        )
