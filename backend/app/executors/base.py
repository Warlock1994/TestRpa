"""模块执行器基类和注册机制 - 异步版本"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Type
from dataclasses import dataclass, field
from pathlib import Path
from playwright.async_api import Page, Browser, BrowserContext
import asyncio

from app.models.workflow import LogLevel


def get_backend_root() -> Path:
    """获取 backend 目录（包含 ffmpeg.exe, ffprobe.exe 等的目录）"""
    # 从当前文件向上找到 backend 目录
    # backend/app/executors/base.py -> backend/app/executors -> backend/app -> backend
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent.parent
    print(f"[DEBUG] Backend 目录: {backend_root}")
    return backend_root


def get_ffmpeg_path() -> str:
    """获取 ffmpeg.exe 的路径"""
    ffmpeg_path = get_backend_root() / 'ffmpeg.exe'
    print(f"[DEBUG] FFmpeg 路径: {ffmpeg_path}, 存在: {ffmpeg_path.exists()}")
    if ffmpeg_path.exists():
        return str(ffmpeg_path)
    print(f"[WARNING] FFmpeg 不存在于 {ffmpeg_path}，使用系统 PATH 中的 ffmpeg")
    return 'ffmpeg'


def get_ffprobe_path() -> str:
    """获取 ffprobe.exe 的路径"""
    ffprobe_path = get_backend_root() / 'ffprobe.exe'
    print(f"[DEBUG] FFprobe 路径: {ffprobe_path}, 存在: {ffprobe_path.exists()}")
    if ffprobe_path.exists():
        return str(ffprobe_path)
    print(f"[WARNING] FFprobe 不存在于 {ffprobe_path}，使用系统 PATH 中的 ffprobe")
    return 'ffprobe'


def escape_css_selector(selector: str) -> str:
    """转义 CSS 选择器中的特殊字符"""
    if not selector:
        return selector
    # 如果选择器看起来已经是有效的，直接返回
    if selector.startswith(('#', '.', '[')) or ' ' in selector or '>' in selector:
        return selector
    # 否则尝试转义
    return selector


@dataclass
class ExecutionContext:
    """执行上下文 - 在模块执行器之间共享的状态（异步版本）"""
    browser: Optional[Browser] = None
    browser_context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    variables: dict[str, Any] = field(default_factory=dict)
    data_rows: list[dict[str, Any]] = field(default_factory=list)
    current_row: dict[str, Any] = field(default_factory=dict)
    loop_stack: list[dict] = field(default_factory=list)  # 循环状态栈
    should_break: bool = False
    should_continue: bool = False
    headless: bool = False  # 无头模式
    browser_config: Optional[dict] = None  # 浏览器配置 {type, executablePath}
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)  # 异步锁
    
    # iframe 状态跟踪
    _in_iframe: bool = False  # 是否在iframe中
    _main_page: Optional[Page] = None  # 主页面引用（用于从iframe切换回来）
    _iframe_locator: Optional[dict] = None  # iframe定位信息 {type: 'name'|'index'|'selector', value: ...}
    _current_frame: Optional[Page] = None  # 当前iframe的直接引用（用于嵌套iframe）
    
    # Playwright 实例引用
    _playwright: Any = None
    _user_data_dir: Optional[str] = None
    
    # 进度日志回调（用于媒体处理等长时间操作）
    _progress_callback: Optional[Any] = None  # Callable[[str, str], Awaitable[None]]
    
    # 执行日志存储（用于导出日志模块）
    _logs: list[dict[str, Any]] = field(default_factory=list)
    
    # 变量更新回调
    _variable_update_callback: Optional[Any] = None  # Callable[[str, Any], Awaitable[None]]
    
    async def get_current_frame(self) -> Optional[Page]:
        """获取当前的frame（如果在iframe中）或page
        
        如果在iframe中，优先返回保存的frame引用
        """
        if not self._in_iframe:
            print(f"[get_current_frame] 不在iframe中，返回当前page")
            return self.page
        
        # 如果有保存的frame引用，直接返回
        if self._current_frame:
            print(f"[get_current_frame] 返回保存的frame引用: {self._current_frame.url}")
            return self._current_frame
        
        # 否则尝试动态获取（兼容旧逻辑）
        if not self._iframe_locator or not self._main_page:
            print(f"[get_current_frame] 没有iframe定位信息，返回当前page")
            return self.page
        
        try:
            locator_type = self._iframe_locator.get('type')
            locator_value = self._iframe_locator.get('value')
            
            print(f"[get_current_frame] 动态获取iframe，定位方式: {locator_type}, 值: {locator_value}")
            
            frame = None
            
            if locator_type == 'name':
                frame = self._main_page.frame(name=locator_value)
                if not frame:
                    try:
                        iframe_element = await self._main_page.wait_for_selector(
                            f'iframe[id="{locator_value}"]',
                            timeout=2000
                        )
                        if iframe_element:
                            frame = await iframe_element.content_frame()
                    except Exception as e:
                        print(f"[get_current_frame] 通过id查找失败: {e}")
                    
            elif locator_type == 'index':
                frames = self._main_page.frames
                child_frames = [f for f in frames if f != self._main_page.main_frame]
                if 0 <= locator_value < len(child_frames):
                    frame = child_frames[locator_value]
                    
            elif locator_type == 'selector':
                try:
                    iframe_element = await self._main_page.wait_for_selector(
                        locator_value,
                        timeout=2000
                    )
                    if iframe_element:
                        frame = await iframe_element.content_frame()
                except Exception as e:
                    print(f"[get_current_frame] 通过选择器查找失败: {e}")
            
            if frame:
                print(f"[get_current_frame] 动态获取成功，更新context.page")
                self.page = frame
                self._current_frame = frame  # 保存引用
                return frame
            
            print(f"[WARNING] 无法获取iframe，返回主页面")
            self.page = self._main_page
            return self._main_page
            
        except Exception as e:
            print(f"[ERROR] 获取iframe失败: {e}")
            import traceback
            traceback.print_exc()
            return self.page
    
    async def send_progress(self, message: str, level: str = "info"):
        """发送进度日志到前端"""
        if self._progress_callback:
            try:
                await self._progress_callback(message, level)
            except Exception as e:
                print(f"发送进度日志失败: {e}")
    
    def add_log(self, level: str, message: str, node_id: Optional[str] = None, 
                duration: Optional[float] = None, timestamp: Optional[str] = None):
        """添加日志到日志列表（用于导出日志模块）"""
        from datetime import datetime
        log_entry = {
            'timestamp': timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'level': level,
            'message': message,
            'nodeId': node_id,
            'duration': duration
        }
        self._logs.append(log_entry)
    
    def get_logs(self) -> list[dict[str, Any]]:
        """获取所有日志"""
        return self._logs.copy()
    
    def clear_logs(self):
        """清空日志"""
        self._logs.clear()
    
    async def switch_to_latest_page(self) -> bool:
        """切换到最新的页面（处理新标签页打开的情况）
        
        注意：如果当前在iframe中，会刷新iframe引用而不是切换页面
        
        Returns:
            bool: 是否切换了页面
        """
        # 如果在iframe中，刷新iframe引用
        if self._in_iframe:
            await self.get_current_frame()
            return False
        
        if self.browser_context is None:
            return False
        
        try:
            # 获取所有页面
            pages = self.browser_context.pages
            if not pages:
                return False
            
            # 获取最新的页面（最后一个）
            latest_page = pages[-1]
            
            # 如果最新页面不是当前页面，切换过去
            if self.page != latest_page:
                self.page = latest_page
                return True
            
            return False
        except Exception:
            return False
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值，支持${var}语法"""
        if name.startswith('${') and name.endswith('}'):
            name = name[2:-1]
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any):
        """设置变量值"""
        self.variables[name] = value
        # 通知变量更新
        if self._variable_update_callback:
            import asyncio
            try:
                # 在异步上下文中调用回调
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._variable_update_callback(name, value))
            except Exception as e:
                print(f"通知变量更新失败: {e}")
    
    def resolve_value(self, value: Any) -> Any:
        """解析值中的变量引用
        
        支持格式：
        - ${varName} - 标准格式
        - {varName} - 简化格式
        - {listName[0]} - 列表索引访问
        - {dictName[key]} 或 {dictName["key"]} - 字典键访问
        - {data[0][name]} - 嵌套访问
        - {listName[{indexVar}]} - 嵌套变量引用（索引本身是变量）
        """
        if isinstance(value, str):
            import re
            
            def resolve_nested_variables(text: str, max_depth: int = 5) -> str:
                """递归解析嵌套的变量引用，最多解析max_depth层"""
                if max_depth <= 0:
                    return text
                
                # 查找所有 {xxx} 格式的变量引用
                pattern = r'(?<!\$)\{([^{}]+)\}'
                matches = list(re.finditer(pattern, text))
                
                if not matches:
                    return text
                
                # 从后向前替换，避免索引偏移问题
                for match in reversed(matches):
                    var_expr = match.group(1).strip()
                    resolved = resolve_access_path(var_expr)
                    if resolved is not None:
                        # 如果是复杂类型，转为JSON字符串
                        if isinstance(resolved, (list, dict)):
                            import json
                            replacement = json.dumps(resolved, ensure_ascii=False)
                        else:
                            replacement = str(resolved)
                        text = text[:match.start()] + replacement + text[match.end():]
                
                # 递归处理，以支持多层嵌套
                if re.search(pattern, text):
                    return resolve_nested_variables(text, max_depth - 1)
                
                return text
            
            def resolve_access_path(var_name: str) -> Any:
                """解析变量访问路径，支持索引和键访问
                
                支持嵌套变量引用，例如：
                - test[{loop_index}] - 先解析 loop_index，再用其值作为索引
                - data[{i}][{j}] - 多层嵌套变量引用
                """
                var_name = var_name.strip()
                
                # 先解析变量名中的嵌套变量引用
                # 例如：test[{loop_index}] -> 先将 {loop_index} 替换为其值
                var_name = resolve_nested_variables(var_name, max_depth=3)
                
                # 解析基础变量名和访问路径
                # 匹配: varName 或 varName[...][...]...
                base_match = re.match(r'^([a-zA-Z_\u4e00-\u9fa5][a-zA-Z0-9_\u4e00-\u9fa5]*)((?:\[[^\]]+\])*)', var_name)
                if not base_match:
                    return None
                
                base_name = base_match.group(1)
                access_path = base_match.group(2)
                
                # 获取基础变量
                if base_name not in self.variables:
                    return None
                result = self.variables[base_name]
                # 深拷贝以避免并发修改问题
                if isinstance(result, (list, dict)):
                    import copy
                    result = copy.deepcopy(result)
                
                # 如果没有访问路径，直接返回
                if not access_path:
                    return result
                
                # 解析所有的 [xxx] 访问
                bracket_pattern = r'\[([^\]]+)\]'
                accessors = re.findall(bracket_pattern, access_path)
                
                for accessor in accessors:
                    accessor = accessor.strip()
                    
                    # 移除引号（如果有）
                    if (accessor.startswith('"') and accessor.endswith('"')) or \
                       (accessor.startswith("'") and accessor.endswith("'")):
                        accessor = accessor[1:-1]
                    
                    try:
                        if isinstance(result, list):
                            # 列表索引访问（支持负数索引，如 -1 表示最后一个元素）
                            index = int(accessor)
                            if -len(result) <= index < len(result):
                                result = result[index]
                            else:
                                return None
                        elif isinstance(result, dict):
                            # 字典键访问 - 先尝试原始键，再尝试数字键
                            if accessor in result:
                                result = result[accessor]
                            else:
                                # 尝试将键转为数字
                                try:
                                    num_key = int(accessor)
                                    if num_key in result:
                                        result = result[num_key]
                                    else:
                                        return None
                                except ValueError:
                                    return None
                        else:
                            # 不支持的类型
                            return None
                    except (ValueError, IndexError, KeyError, TypeError):
                        return None
                
                return result
            
            # 先替换 ${varName} 格式
            pattern1 = r'\$\{([^}]+)\}'
            result = value
            for match in reversed(list(re.finditer(pattern1, result))):
                var_expr = match.group(1).strip()
                resolved = resolve_access_path(var_expr)
                if resolved is not None:
                    if isinstance(resolved, (list, dict)):
                        import json
                        replacement = json.dumps(resolved, ensure_ascii=False)
                    else:
                        replacement = str(resolved)
                    result = result[:match.start()] + replacement + result[match.end():]
            
            # 再替换 {varName} 格式（但不匹配已经有$的）
            # 使用递归解析支持嵌套变量引用
            result = resolve_nested_variables(result, max_depth=5)
            
            return result
        return value
    
    def add_data_value(self, column: str, value: Any):
        """添加数据值到当前行
        
        如果当前行已经有该列的数据，则自动提交当前行并开始新行
        """
        # 如果当前行已经有这个列的数据，先提交当前行
        if column in self.current_row:
            self._commit_row_internal()
        self.current_row[column] = value
    
    def _commit_row_internal(self):
        """内部提交方法"""
        if self.current_row:
            self.data_rows.append(self.current_row.copy())
            self.current_row = {}
    
    def commit_row(self):
        """提交当前行到数据集"""
        self._commit_row_internal()


@dataclass
class ModuleResult:
    """模块执行结果"""
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None
    branch: Optional[str] = None  # 用于条件分支，值为 "true" 或 "false"
    duration: float = 0  # 执行耗时（毫秒）
    log_level: Optional[str] = None  # 自定义日志级别（用于打印日志模块）


@dataclass
class LogMessage:
    """日志消息"""
    level: LogLevel
    message: str
    node_id: Optional[str] = None
    details: Optional[dict] = None
    duration: Optional[float] = None


class ModuleExecutor(ABC):
    """模块执行器基类 - 纯异步版本"""
    
    @property
    @abstractmethod
    def module_type(self) -> str:
        """返回此执行器处理的模块类型"""
        pass
    
    @abstractmethod
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """执行模块逻辑（异步版本）"""
        pass
    
    def validate_config(self, config: dict) -> tuple[bool, str]:
        """验证配置有效性，子类可重写"""
        return True, ""


class ExecutorRegistry:
    """执行器注册表"""
    
    def __init__(self):
        self._executors: dict[str, ModuleExecutor] = {}
    
    def register(self, executor_class: Type[ModuleExecutor]):
        """注册执行器类 - 每次都创建新实例"""
        executor = executor_class()
        self._executors[executor.module_type] = executor
    
    def get(self, module_type: str) -> Optional[ModuleExecutor]:
        """获取指定类型的执行器"""
        return self._executors.get(module_type)
    
    def get_all_types(self) -> list[str]:
        """获取所有已注册的模块类型"""
        return list(self._executors.keys())
    
    def clear(self):
        """清空注册表"""
        self._executors.clear()


# 全局注册表实例
registry = ExecutorRegistry()


def register_executor(cls: Type[ModuleExecutor]) -> Type[ModuleExecutor]:
    """装饰器：注册执行器 - 每次都重新注册"""
    registry.register(cls)
    return cls
