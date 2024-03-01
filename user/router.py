from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from custom_http_exception import HTTPException
from database import get_db
from security import get_payload
from user.schema import UserSchema
from user.service import get_user_by_id

router = APIRouter(prefix="/user", tags=["user"], dependencies=[Depends(get_payload)])


@router.get("/")
async def get_user_info():
    pass


@router.get("/self", response_model=UserSchema)
async def get_self_info(payload: dict = Depends(get_payload), db: Session = Depends(get_db)):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if payload is None:
        raise unauthorized
    user_id = payload.get("sub")
    if user_id is None or user_id.strip() == '':
        raise unauthorized

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized

    return user


@router.get("/list")
async def get_user_list():
    return {"list": []}


@router.post("/")
async def create_user():
    pass


@router.put("/")
async def update_user():
    pass


@router.delete("/")
async def delete_user():
    pass
