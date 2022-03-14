from pydantic import BaseSettings
from typing import Optional
import os

from pydantic.fields import T


class Settings(BaseSettings):
    app_name: str = "Kingsome API"
    admin_email: str = "pengtao@kingsome.cn"
    items_per_user: int = 50
    is_debug: bool = True

    redis_host: str = "192.168.100.30"  # reids 服务器IP
    redis_port: int = 6379  # redis 端口
    redis_db: int = 2   # redis db

    mail_server: str = "smtp.exmail.qq.com"  # 邮箱server
    mail_user: str = "ops@kingsome.cn"  # 邮箱用户名
    mail_pswd: Optional[str] = os.getenv('mail_pswd')  # 邮箱密码

    x_token: str = "abc"

    root_path_in_servers: Optional[bool] = False
    root_path: str = '/api/v1'

    origins: list = [
        "http://*.kingsome.cn",
        "https://*.kingsome.cn",
        "http://localhost",
        "http://localhost:8080",
    ]


settings = Settings()
