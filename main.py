import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from loguru import logger
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

import custom_logging
from auth.router import router as auth_router
from custom_http_exception import status_message_map, HTTPException as MyHTTPException
from schema import ResponseBody
from user.router import router as user_router


# 应用生命周期
@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    logger.debug("FastAPI app starting...")
    yield
    logger.debug("FastAPI app shutting down...")


# 设置loguru日志
my_logger = custom_logging.setup_logger()

app = FastAPI(lifespan=app_lifespan)

app.logger = my_logger

# 加入路由
app.include_router(auth_router)
app.include_router(user_router)


# 中间件

@logger.catch
@app.middleware("http")
async def general_middleware(request: Request, call_next):
    try:
        logger.info(f"Request: {request.method} {request.url}")
        logger.debug(f"Request Headers: {request.headers.raw}")
        logger.debug(f"Request Body: {await request.body()}")

        response = await call_next(request)
    except Exception:
        logger.exception("Internal Server Error")
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ResponseBody(message=status_message_map[status.HTTP_500_INTERNAL_SERVER_ERROR])
            )
        )

    logger.info(f"Response Status Code: {response.status_code}")
    logger.debug(f"Response Headers: {response.headers.raw}")

    return response


# 异常处理

@logger.catch
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(ResponseBody(message="请求参数错误，请检查请求数据"))
    )


@logger.catch
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content=jsonable_encoder(ResponseBody(message=status_message_map[exc.status_code])))


@logger.catch
@app.exception_handler(MyHTTPException)
async def my_http_exception_handler(request: Request, exc: MyHTTPException):
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(ResponseBody(message=exc.detail)))
