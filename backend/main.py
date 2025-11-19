# -*- coding: utf-8 -*-

import os
import uvicorn
import typer
from fastapi import FastAPI
from alembic import command
from alembic.config import Config

from app.common.enums import EnvironmentEnum


shell_app = typer.Typer()

# 初始化 Alembic 配置
alembic_cfg = Config("alembic.ini")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    from app.plugin.init_app import (
        register_middlewares,
        register_exceptions,
        register_routers,
        register_files,
        reset_api_docs,
        lifespan
    )
    from app.config.setting import settings
    # 创建FastAPI应用
    app = FastAPI(**settings.FASTAPI_CONFIG, lifespan=lifespan)
    
    from app.core.logger import setup_logging
    # 初始化日志
    setup_logging()
    # 注册各种组件
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

@shell_app.command(name="run", help="启动 FastapiAdmin 服务")
def run(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    """启动FastAPI服务"""

    try:
        # 设置环境变量
        os.environ["ENVIRONMENT"] = env.value
        
        # 显示启动横幅
        from app.utils.banner import worship
        typer.echo(worship(env.value))

        # 清除配置缓存，确保重新加载配置
        from app.config.setting import get_settings
        get_settings.cache_clear()
        settings = get_settings()
        
        from app.core.logger import setup_logging
        setup_logging()
        
        # 启动uvicorn服务
        uvicorn.run(
            app=f'main:create_app', 
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=settings.RELOAD,
            factory=True,
            log_config=None
        )
        
    except KeyboardInterrupt:
        from app.utils.console import display_shutdown_info
        display_shutdown_info()
    except Exception as e:
        raise

@shell_app.command(name="revision", help="生成新的 Alembic 迁移脚本")
def revision(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    """生成新的 Alembic 迁移脚本"""
    os.environ["ENVIRONMENT"] = env.value
    command.revision(alembic_cfg, autogenerate=True, message="迁移脚本")
    typer.echo(f"迁移脚本已生成")

@shell_app.command(name="upgrade", help="应用最新的 Alembic 迁移")
def upgrade(env: EnvironmentEnum = typer.Option(EnvironmentEnum.DEV, "--env", help="运行环境 (dev, prod)")) -> None:
    """应用最新的 Alembic 迁移"""
    os.environ["ENVIRONMENT"] = env.value
    command.upgrade(alembic_cfg, "head")
    typer.echo("所有迁移已应用。")


if __name__ == '__main__':
    
    shell_app()

    # 开发环境启动
    # python main.py run --env=dev (不加默认为dev)
