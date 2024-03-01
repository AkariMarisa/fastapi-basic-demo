# FastAPI 练手

## 目前实现功能

1. 用户登陆获取JWT
2. JWT过期刷新
3. 用户注册
4. 根据JWT获取用户信息
5. 用户登出
6. 全局异常处理
7. 请求前后日志打印
8. 日志旋转

## 如何运行？

运行以下SQL创建数据库。

```sql
create schema fastapi_test collate utf8mb4_general_ci;

create table fastapi_test.user
(
    id  int auto_increment  primary key,
    username    varchar(40) not null,
    password    varchar(64)    null,
    email   varchar(64) null,
    constraint  user_username_unique    unique (username)
);
```

运行以下指令安装依赖。

```shell
python3 -m venv venv

. venv/bin/activate

pip install -r requirements.txt
```

运行以下指令启动服务。

```shell
uvicorn main:app --host 0.0.0.0 --port 80
```