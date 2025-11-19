# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional
from rich import get_console
from rich.panel import Panel
from rich.text import Text
from rich.console import Group

from app.config.setting import settings

console = get_console()


def create_service_panel(
    host: str, port: int, reload: bool, *, 
    redis_ready: Optional[bool] = None, 
    scheduler_jobs: Optional[int] = None, 
    scheduler_status: Optional[str] = None,
    startup_time: Optional[str] = None
) -> Panel:
    """创建简洁的服务启动信息面板"""
    
    url = f'http://{host}:{port}'
    base_url = f'{url}{settings.ROOT_PATH}'
    docs_url = base_url + settings.DOCS_URL

    # 核心服务信息
    service_info = Text()
    service_info.append("🚀 ", style="bold green")
    service_info.append(f"FastapiAdmin v{settings.VERSION}")
    service_info.append(f"\n🌐 {url}", style="bold blue")
    service_info.append(f"\n📊 {settings.ENVIRONMENT.value if hasattr(settings.ENVIRONMENT, 'value') else settings.ENVIRONMENT}")
    service_info.append(f" • {settings.TITLE}")
    
    # 组件状态（简化显示）
    component_info = Text()
    component_info.append("⚙️ 组件状态", style="bold cyan")
    component_info.append(f"\n💾 {settings.DATABASE_TYPE}")
    
    if redis_ready is not None:
        status = "✅" if redis_ready else "❌"
        component_info.append(f"\n🔴 Redis {status}")
    
    if scheduler_jobs is not None:
        icon = "✅" if scheduler_status == "running" else "⏸️"
        component_info.append(f"\n⏰ 定时任务 {icon} {scheduler_jobs}")
    
    # 配置信息
    config_info = Text()
    config_info.append("⚡ 配置", style="bold yellow")
    if settings.DEBUG:
        config_info.append(f"\n🐛 Debug: ✅ 开启", style="yellow")
    else:
        config_info.append(f"\n🐛 Debug: ❌ 关闭", style="dim")
        
    config_info.append(f"\n🔄 重载: {'✅' if reload else '❌'}")
    
    # 组合内容
    all_content = Group(
        service_info,
        "\n" + "─" * 40,
        component_info,
        "\n" + "─" * 40,
        config_info
    )
    
    # 在调试模式下添加文档链接
    if settings.DEBUG:
        docs_info = Text()
        docs_info.append("📖 文档", style="bold magenta")
        docs_info.append(f"\n🔗 {docs_url}", style="blue link")
        
        all_content = Group(
            all_content,
            "\n" + "─" * 40,
            docs_info
        )
    
    # 添加底部提示
    footer = Text()
    footer.append("🌟 FastapiAdmin • ", style="dim")
    footer.append("优雅 · 简洁 · 高效", style="dim italic")
    
    final_content = Group(
        all_content,
        "\n" + "─" * 40,
        footer
    )

    return Panel(
        final_content,
        title="[bold purple]🚀 服务启动完成[/]",
        border_style="green",
        padding=(1, 2)
    )


def run(host: str, port: int, reload: bool, *, 
        redis_ready: Optional[bool] = None, 
        scheduler_jobs: Optional[int] = None, 
        scheduler_status: Optional[str] = None,
        show_banner: bool = True,
        startup_time: Optional[str] = None) -> None:
    """显示启动信息面板"""
    
    if show_banner:
        console.print("\n")
    
    # 创建并显示启动面板
    service_panel = create_service_panel(
        host=host,
        port=port,
        reload=reload,
        redis_ready=redis_ready,
        scheduler_jobs=scheduler_jobs,
        scheduler_status=scheduler_status,
        startup_time=startup_time
    )
    
    console.print(service_panel)

def display_shutdown_info():
    """显示关闭信息"""
    shutdown_content = Text()
    shutdown_content.append("🛑 ", style="bold red")
    shutdown_content.append("FastapiAdmin 服务关闭")
    shutdown_content.append(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
    shutdown_content.append("\n👋 感谢使用！", style="dim")
    
    shutdown_panel = Panel(
        shutdown_content,
        title="[bold red]服务关闭[/]",
        border_style="red",
        padding=(1, 2)
    )
    
    console.print(shutdown_panel)
