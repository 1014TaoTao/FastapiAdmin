from app.config.path_conf import BANNER_FILE

def worship(env: str) -> str | None:
    """
    获取项目启动Banner（优先读取 banner.txt）
    """
    if BANNER_FILE.exists():
        banner = BANNER_FILE.read_text(encoding='utf-8')
        banner = banner + f"🚀 当前运行环境: {env}\n"
        return banner