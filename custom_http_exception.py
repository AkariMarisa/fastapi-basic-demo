from typing import Union

from fastapi import HTTPException as FastAPIHTTPException
from starlette import status

status_message_map = {
    status.HTTP_400_BAD_REQUEST: '上送请求参数非法，请检查请求参数',
    status.HTTP_401_UNAUTHORIZED: '会话已过期，请重新登陆',
    status.HTTP_403_FORBIDDEN: '会话已过期，请刷新会话',
    status.HTTP_500_INTERNAL_SERVER_ERROR: '服务器发生错误，请联系管理员'
}


class HTTPException(FastAPIHTTPException):
    def __init__(self, status_code: int, detail: Union[str, None] = None):
        super().__init__(status_code=status_code, detail=detail)

        self.status_code = status_code
        self.detail = detail if detail is not None else status_message_map[status_code]
