# -*- coding: utf-8 -*-

import os
import uvicorn
import typer
from fastapi import FastAPI
from alembic import command
from alembic.config import Config

from app.common.enums import EnvironmentEnum
from app.config.setting import settings
from app.core.logger import setup_logging
from app.utils.common_util import worship


# 全局标志，用于跟踪日志是否已初始化
LOGGING_INITIALIZED = False


shell_app = typer.Typer()

# 初始化 Alembic 配置
alembic_cfg = Config("alembic.ini")

def create_app() -> FastAPI:
    global LOGGING_INITIALIZED
    from app.plugin.init_app import (
        register_middlewares,
        register_exceptions,
        register_routers,
        register_files,
        reset_api_docs,
        lifespan
    )
    # 初始化日志系统（确保每个工作进程都会初始化日志，但避免重复初始化）
    if not LOGGING_INITIALIZED:
        setup_logging()
        LOGGING_INITIALIZED = True
    # 创建FastAPI应用
    app = FastAPI(**settings.FASTAPI_CONFIG, lifespan=lifespan)

    # 注册异常处理器
    register_exceptions(app)
    # 注册中间件
    register_middlewares(app)
    # 注册路由
    register_routers(app)
    # 注册静态文件
    register_files(app)
    # 重设API文档
    reset_api_docs(app)

    return app

@shell_app.command()
def run(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    typer.echo("项目启动中..")
    # 设置环境变量
    os.environ["ENVIRONMENT"] = env.value
    # 初始化日志系统（确保uvicorn主进程的日志也被正确配置）
    setup_logging()
    worship()
    
    # 启动uvicorn服务
    uvicorn.run(app=f'main:create_app', **settings.UVICORN_CONFIG)

@shell_app.command()
def revision(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    """
    生成新的 Alembic 迁移脚本。
    """
    os.environ["ENVIRONMENT"] = env.value
    command.revision(alembic_cfg, autogenerate=True, message="迁移脚本")
    typer.echo(f"迁移脚本已生成")

@shell_app.command()
def upgrade(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    """
    应用最新的 Alembic 迁移。
    """
    os.environ["ENVIRONMENT"] = env.value
    command.upgrade(alembic_cfg, "head")
    typer.echo("所有迁移已应用。")


if __name__ == '__main__':
    
    shell_app()

    # 开发环境启动
    # python main.py run --env=dev (不加默认为dev)
