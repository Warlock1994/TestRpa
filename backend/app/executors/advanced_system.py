"""高级模块执行器 - advanced_system"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
import asyncio
import ctypes
import os
import re
import subprocess
import time


@register_executor
class ShutdownSystemExecutor(ModuleExecutor):
    """关机/重启模块执行器"""

    @property
    def module_type(self) -> str:
        return "shutdown_system"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import subprocess
        
        action = context.resolve_value(config.get("action", "shutdown"))  # 支持变量引用
        delay = to_int(config.get("delay", 0), 0, context)
        force_raw = config.get("force", False)
        # 支持变量引用
        if isinstance(force_raw, str):
            force_raw = context.resolve_value(force_raw)
        force = force_raw in [True, 'true', 'True', '1', 1]

        try:
            # 构建命令
            if action == "shutdown":
                cmd = f"shutdown /s /t {delay}"
                if force:
                    cmd += " /f"
                action_text = "关机"
            elif action == "restart":
                cmd = f"shutdown /r /t {delay}"
                if force:
                    cmd += " /f"
                action_text = "重启"
            elif action == "logout":
                cmd = "shutdown /l"
                action_text = "注销"
            elif action == "hibernate":
                cmd = "shutdown /h"
                action_text = "休眠"
            elif action == "sleep":
                # 使用 PowerShell 进入睡眠模式
                cmd = "powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)\""
                action_text = "睡眠"
            else:
                return ModuleResult(success=False, error=f"未知操作类型: {action}")

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(cmd, shell=True, capture_output=True, text=True)
            )

            if result.returncode != 0 and result.stderr:
                return ModuleResult(success=False, error=f"执行失败: {result.stderr}")

            if delay > 0:
                return ModuleResult(success=True, message=f"系统将在 {delay} 秒后{action_text}")
            else:
                return ModuleResult(success=True, message=f"正在执行{action_text}...")

        except Exception as e:
            return ModuleResult(success=False, error=f"系统操作失败: {str(e)}")

@register_executor
class LockScreenExecutor(ModuleExecutor):
    """锁定屏幕模块执行器"""

    @property
    def module_type(self) -> str:
        return "lock_screen"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes

        try:
            # 调用 Windows API 锁定屏幕
            ctypes.windll.user32.LockWorkStation()
            return ModuleResult(success=True, message="屏幕已锁定")
        except Exception as e:
            return ModuleResult(success=False, error=f"锁定屏幕失败: {str(e)}")

@register_executor
class WindowFocusExecutor(ModuleExecutor):
    """窗口聚焦模块执行器 - 将指定窗口置顶到最前面"""

    @property
    def module_type(self) -> str:
        return "window_focus"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes
        from ctypes import wintypes
        import time
        
        window_title = context.resolve_value(config.get("windowTitle", ""))
        match_mode = context.resolve_value(config.get("matchMode", "contains"))  # exact, contains, startswith
        
        if not window_title:
            return ModuleResult(success=False, error="窗口标题不能为空")
        
        try:
            user32 = ctypes.windll.user32
            
            # 定义回调函数类型
            EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            
            found_hwnd = None
            found_title = None
            
            def enum_windows_callback(hwnd, lParam):
                nonlocal found_hwnd, found_title
                
                # 获取窗口标题
                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0:
                    return True
                
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
                
                # 检查窗口是否可见
                if not user32.IsWindowVisible(hwnd):
                    return True
                
                # 根据匹配模式检查标题
                matched = False
                if match_mode == "exact":
                    matched = title == window_title
                elif match_mode == "contains":
                    matched = window_title.lower() in title.lower()
                elif match_mode == "startswith":
                    matched = title.lower().startswith(window_title.lower())
                
                if matched:
                    found_hwnd = hwnd
                    found_title = title
                    return False  # 停止枚举
                
                return True
            
            # 枚举所有窗口
            callback = EnumWindowsProc(enum_windows_callback)
            user32.EnumWindows(callback, 0)
            
            if not found_hwnd:
                return ModuleResult(success=False, error=f"未找到匹配的窗口: {window_title}")
            
            # 定义常量
            SW_RESTORE = 9
            SW_SHOW = 5
            SW_SHOWNORMAL = 1
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040
            SWP_NOACTIVATE = 0x0010
            
            # 如果窗口最小化，先恢复
            if user32.IsIconic(found_hwnd):
                user32.ShowWindow(found_hwnd, SW_RESTORE)
                time.sleep(0.1)
            
            # 方法1: 使用 AttachThreadInput 绕过前台窗口限制
            # 获取目标窗口的线程ID
            target_thread_id = user32.GetWindowThreadProcessId(found_hwnd, None)
            # 获取当前线程ID
            current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            
            # 附加到目标线程的输入队列
            attached = False
            if target_thread_id != current_thread_id:
                attached = user32.AttachThreadInput(current_thread_id, target_thread_id, True)
            
            try:
                # 先将窗口设为最顶层
                user32.SetWindowPos(found_hwnd, HWND_TOPMOST, 0, 0, 0, 0, 
                                   SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                
                # 显示窗口
                user32.ShowWindow(found_hwnd, SW_SHOW)
                
                # 激活窗口
                user32.BringWindowToTop(found_hwnd)
                user32.SetForegroundWindow(found_hwnd)
                
                # 模拟 Alt 键按下释放，这可以帮助绕过 Windows 的前台窗口限制
                # VK_MENU = 0x12 (Alt键)
                user32.keybd_event(0x12, 0, 0, 0)  # Alt down
                user32.keybd_event(0x12, 0, 2, 0)  # Alt up
                
                # 再次尝试设置前台窗口
                user32.SetForegroundWindow(found_hwnd)
                user32.SetActiveWindow(found_hwnd)
                
                # 取消最顶层（这样窗口不会一直置顶）
                user32.SetWindowPos(found_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, 
                                   SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                
            finally:
                # 分离线程输入
                if attached:
                    user32.AttachThreadInput(current_thread_id, target_thread_id, False)
            
            return ModuleResult(
                success=True, 
                message=f"已聚焦窗口: {found_title}",
                data={'hwnd': found_hwnd, 'title': found_title}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"窗口聚焦失败: {str(e)}")

@register_executor
class RunCommandExecutor(ModuleExecutor):
    """执行命令模块执行器"""

    @property
    def module_type(self) -> str:
        return "run_command"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import subprocess

        command = context.resolve_value(config.get("command", ""))
        shell = context.resolve_value(config.get("shell", "cmd"))  # 支持变量引用
        timeout = to_int(config.get("timeout", 30), 30, context)
        variable_name = config.get("variableName", "")

        if not command:
            return ModuleResult(success=False, error="命令不能为空")

        try:
            if shell == "powershell":
                full_command = ["powershell", "-Command", command]
            else:
                full_command = ["cmd", "/c", command]

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    full_command,
                    capture_output=True,
                    timeout=timeout
                )
            )

            # 尝试解码输出
            try:
                stdout = result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                stdout = result.stdout.decode('gbk', errors='ignore')

            try:
                stderr = result.stderr.decode('utf-8')
            except UnicodeDecodeError:
                stderr = result.stderr.decode('gbk', errors='ignore')

            output = stdout.strip() if stdout else stderr.strip()

            if variable_name:
                context.set_variable(variable_name, output)

            if result.returncode != 0:
                return ModuleResult(
                    success=False, 
                    error=f"命令执行失败 (返回码: {result.returncode}): {stderr or stdout}"
                )

            display_output = output[:100] + "..." if len(output) > 100 else output
            return ModuleResult(
                success=True, 
                message=f"命令执行成功: {display_output}",
                data={"output": output, "return_code": result.returncode}
            )

        except subprocess.TimeoutExpired:
            return ModuleResult(success=False, error=f"命令执行超时 ({timeout}秒)")
        except Exception as e:
            return ModuleResult(success=False, error=f"命令执行失败: {str(e)}")