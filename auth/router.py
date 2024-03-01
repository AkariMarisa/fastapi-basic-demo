from typing import Union

from fastapi import APIRouter, Depends, Response
from starlette import status
from starlette.datastructures import MutableHeaders
from starlette.requests import Request

import security
from auth.schema import LoginSchema, SignUpSchema
from custom_http_exception import HTTPException
from database import get_db
from schema import ResponseBody
from user.model import User
from user.service import *

router = APIRouter(prefix="/auth", tags=["authentication"])

REFRESH_TOKEN_COOKIE_NAME = "x_rt"


@router.post("/signup")
async def signup(signup_data: SignUpSchema, db: Session = Depends(get_db)):
    # 验证两次密码是否重复
    if signup_data.password != signup_data.repeat_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="两次密码不一致")

    # 验证用户名是否存在
    user_list = await get_user_by_username(db, signup_data.username)
    if len(user_list) > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    # 将密码加密，保存用户信息到数据库中
    hashed_password = security.encrypt_password(signup_data.password)
    await save_user(db,
                    schema.UserCreate(username=signup_data.username, email=signup_data.email, password=hashed_password))

    # 提示注册成功
    return ResponseBody(message="注册成功")


@router.post("/login")
async def login(response: Response, login_data: LoginSchema, db: Session = Depends(get_db)):
    """
    用户登陆
    :param response:
    :param login_data:
    :param db:
    :return:
    """
    # 根据用户名获取数据库中的用户信息
    username = login_data.username
    # 判断用户是否存在
    user_list: List = await get_user_by_username(db, username)
    user: Union[User, None] = user_list.pop() if len(user_list) > 0 else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    # 判断用户密码是否一致
    if not security.verify_password(login_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或密码错误")
    # 签发access_token和refresh_token
    user_id = str(user.id)
    tokens = await create_tokens(response, user_id)
    return {"access_token": tokens[0]}


async def create_tokens(response: Response, user_id: str):
    """
    创建access_token与refresh_token，并缓存refresh_token
    :param response: Response对象，用于将refresh_token放到Cookie中
    :param user_id: 生成token的用户ID
    :return: [access_token, refresh_token]
    """
    tokens: List = security.create_tokens({"sub": user_id})

    # refresh_token放在Cookie中，这样刷新access_token的时候直接从请求Cookie中取就行了
    refresh_token = tokens[-1]
    response.set_cookie(key=REFRESH_TOKEN_COOKIE_NAME, value=refresh_token, httponly=True)

    # 缓存refresh_token
    security.cache_refresh_token(user_id, refresh_token)
    return tokens


@router.post("/logout")
async def logout(request: Request, response: Response, access_token: str = Depends(security.oauth2_scheme)):
    """
    用户登出
    :param request: Request对象，用来删除请求头中的Authorization
    :param response: Response对象，用来清除Cookie中的refresh_token
    :param access_token: access_token，用于获取用户ID并清除对应的refresh_token缓存
    :return: {"message": "已登出"}
    """
    # 删除Cookie中的refresh_token
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, httponly=True)

    # 删除缓存的refresh_token
    payload = security.get_payload(access_token)
    security.remove_refresh_token(payload.get("sub") if payload is not None else "")

    # 删除请求头的access_token
    # 这段代码真的有什么用吗❓❓❓
    headers = MutableHeaders(request.headers)
    del headers["Authorization"]
    request._headers = headers

    return {"message": "已登出"}


@router.post("/refresh")
async def refresh_tokens(
        request: Request,
        response: Response,
        access_token: str = Depends(security.oauth2_scheme),
        db: Session = Depends(get_db)
):
    """
    刷新access_token与refresh_token
    :param request: Request对象，用于获取Cookie中的refresh_token
    :param response: Response对象，用于更新Cookie中的refresh_token
    :param access_token: access_token，自动获取
    :param db:
    :return: { "access_token": access_token }
    """
    # 根据请求Cookie中的x_rt（refresh_token）来签发新的access_token
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token is None or refresh_token.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="刷新凭证错误")

    # 验证refresh_token是否已经被使用过
    if not security.check_refresh_token_cache(refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证已被使用，请重新登陆")

    # 如果refresh_token过期，则直接提醒用户重新登陆
    try:
        security.get_payload(refresh_token)
    except HTTPException as ex:
        if ex.status_code == status.HTTP_403_FORBIDDEN:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证已过期，请重新登陆")
        else:
            raise ex

    payload: dict = security.get_payload(access_token, verify_exp=False)
    user_id = payload.get("sub")

    # 验证用户ID是否存在
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="访问凭证非法")

    # 一并重新签发refresh_token
    new_tokens = await create_tokens(response, user_id)
    return {"access_token": new_tokens[0]}
