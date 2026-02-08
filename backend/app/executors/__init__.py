# Module executors
from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    LogMessage,
    ExecutorRegistry,
    registry,
    register_executor,
    get_backend_root,
    get_ffmpeg_path,
    get_ffprobe_path,
)

# 导入所有执行器以触发注册
from . import basic
from . import advanced
from . import advanced_browser
from . import advanced_image
from . import advanced_keyboard
from . import advanced_pillow
from . import control
from . import captcha
from . import data_structure
from . import ai
from . import ai_scraper
from . import ai_firecrawl
from . import table
from . import subflow
from . import database
from . import media
from . import media_record
from . import media_m3u8
from . import qq
from . import wechat
from . import pdf
from . import document_convert
from . import screen_share
from . import trigger
from . import utility_tools
from . import format_factory
from . import python_script
from . import table_extract
from . import switch_tab

# 调试：打印已注册的执行器
print(f"[DEBUG] 已注册的执行器类型: {registry.get_all_types()}")

__all__ = [
    "ModuleExecutor",
    "ExecutionContext",
    "ModuleResult",
    "LogMessage",
    "ExecutorRegistry",
    "registry",
    "register_executor",
    "get_backend_root",
    "get_ffmpeg_path",
    "get_ffprobe_path",
    "escape_css_selector",
]
