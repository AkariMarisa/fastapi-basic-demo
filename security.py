from datetime import timedelta, datetime, timezone
from typing import Union

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from starlette import status
from custom_http_exception import HTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "30496947639fdcbf2f000af3c1c53ff626c65fe430ead51142dd6d03778ea305"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

refresh_token_cache = {}


def create_tokens(
        data: dict,
        access_token_expires_delta: Union[timedelta, None] = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_token_expires_delta: Union[timedelta, None] = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
):
    """
    生成access_token和refresh_token
    :param data: JWT中用户数据
    :param access_token_expires_delta: access_token过期时间（分钟）
    :param refresh_token_expires_delta: refresh_token过期时间（分钟）
    :return: [access_token, refresh_token]
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    access_token_expire = now + access_token_expires_delta

    to_encode.update({"exp": access_token_expire})

    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    refresh_token_expire = now + refresh_token_expires_delta
    refresh_token = jwt.encode({"exp": refresh_token_expire, "sub": ""}, SECRET_KEY, algorithm=ALGORITHM)

    return [access_token, refresh_token]


def get_payload(token: str = Depends(oauth2_scheme), verify_exp: bool = True):
    """
    获取JWT中的信息
    :param verify_exp: 是否验证是否过期，默认True
    :param token: JWT
    :return: JWT中的信息
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": verify_exp})
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return payload


def cache_refresh_token(token_id, refresh_token):
    refresh_token_cache[token_id] = refresh_token


def remove_refresh_token(token_id):
    del refresh_token_cache[token_id]


def check_refresh_token_cache(token_id):
    refresh_token: str = refresh_token_cache.get(token_id)
    return refresh_token is not None and refresh_token.strip() != ""


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    比较明文密码和加密后的密码是否一致
    :param plain_password: 明文密码
    :param hashed_password: 加密后的密码
    :return: 密码是否一致
    """
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_password(password):
    """
    加密密码（获取密码散列）
    :param password: 明文密码
    :return: 加密后的密码
    """
    return pwd_context.hash(password)
