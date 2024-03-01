from typing import Union

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: Union[str, None]


class UserCreate(UserBase):
    password: str


class UserSchema(UserBase):
    id: int

    class Config:
        from_attributes = True
