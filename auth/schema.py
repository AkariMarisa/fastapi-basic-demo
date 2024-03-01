from typing import Union

from pydantic import BaseModel, Field


class LoginSchema(BaseModel):
    username: str
    password: str = Field(min_length=1)


class SignUpSchema(LoginSchema):
    email: Union[str, None] = Field(default=None, min_length=1)
    repeat_password: str = Field(min_length=1, alias="repeatPassword")
