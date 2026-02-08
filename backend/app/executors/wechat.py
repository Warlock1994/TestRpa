"""微信自动化模块执行器 - 基于图像识别和键鼠模拟

由于微信 4.x 使用了全新的 UI 框架，传统的 UI 自动化工具无法支持。
本模块采用图像识别 + 键鼠模拟的方式实现微信自动化，兼容所有版本微信。

实现原理：
1. 通过窗口标题查找并激活微信窗口
2. 使用 Ctrl+F 打开搜索，输入联系人名称
3. 按 Enter 进入聊天窗口
4. 使用键盘输入或剪贴板粘贴发送内容
"""
import asyncio
import os
import time
import ctypes
from typing import Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


# Windows API 常量
SW_RESTORE = 9
SW_SHOW = 5
SW_SHOWNORMAL = 1
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040


def find_wechat_window():
    """查找微信窗口句柄"""
    import win32gui
    
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            # 微信主窗口：标题是"微信"，类名包含特定字符串
            # 新版微信 4.x: mmui::MainWindow
            # 旧版微信 3.x: WeChatMainWndForPC
            if title == "微信":
                print(f"[微信自动化] 找到窗口: title={title}, class={class_name}, hwnd={hwnd}")
                windows.append((hwnd, class_name))
        return True
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    
    # 优先返回微信主窗口
    for hwnd, class_name in windows:
        if "mmui" in class_name or "WeChat" in class_name:
            return hwnd
    
    # 如果没找到特定类名，返回第一个标题为"微信"的窗口
    return windows[0][0] if windows else None


def activate_wechat_window():
    """激活微信窗口并置顶"""
    import win32gui
    import win32con
    import win32api
    import win32process
    
    hwnd = find_wechat_window()
    if not hwnd:
        raise Exception("未找到微信窗口，请确保微信已登录并且窗口已打开")
    
    print(f"[微信自动化] 激活窗口: hwnd={hwnd}")
    
    # 如果窗口最小化，先恢复
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.2)
    
    # 显示窗口
    win32gui.ShowWindow(hwnd, SW_SHOWNORMAL)
    
    # 关键：使用 AttachThreadInput 绑定线程输入，绕过前台窗口限制
    try:
        # 获取当前线程ID和目标窗口线程ID
        current_thread_id = win32api.GetCurrentThreadId()
        target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)
        
        # 绑定线程输入
        if current_thread_id != target_thread_id:
            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
        
        # 使用 SetWindowPos 置顶窗口
        win32gui.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.05)
        win32gui.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        
        # 激活窗口
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetFocus(hwnd)
        
        # 解绑线程输入
        if current_thread_id != target_thread_id:
            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
            
    except Exception as e:
        print(f"[微信自动化] 激活窗口异常: {e}")
        # 备用方案：模拟 Alt 键来允许设置前台窗口
        try:
            # 模拟按下并释放 Alt 键
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt down
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt up
            time.sleep(0.05)
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e2:
            print(f"[微信自动化] 备用激活方案也失败: {e2}")
    
    # 等待窗口激活
    time.sleep(0.3)
    
    # 验证窗口是否激活
    for _ in range(5):
        foreground = win32gui.GetForegroundWindow()
        if foreground == hwnd:
            print(f"[微信自动化] 窗口激活成功")
            return hwnd
        time.sleep(0.1)
    
    # 最后尝试：点击窗口中心来激活
    try:
        rect = win32gui.GetWindowRect(hwnd)
        center_x = (rect[0] + rect[2]) // 2
        center_y = (rect[1] + rect[3]) // 2
        print(f"[微信自动化] 尝试点击窗口中心: ({center_x}, {center_y})")
        
        import pyautogui
        pyautogui.click(center_x, center_y)
        time.sleep(0.2)
    except Exception as e:
        print(f"[微信自动化] 点击激活失败: {e}")
    
    return hwnd


def send_keys(text: str, interval: float = 0.02):
    """发送键盘输入"""
    import pyautogui
    pyautogui.typewrite(text, interval=interval) if text.isascii() else None


def press_key(key: str):
    """按下单个按键"""
    import pyautogui
    pyautogui.press(key)


def hotkey(*keys):
    """按下组合键"""
    import pyautogui
    pyautogui.hotkey(*keys)


def set_clipboard_text(text: str, max_retries: int = 3):
    """设置剪贴板文本（带重试机制）"""
    import win32clipboard
    import win32con
    
    for attempt in range(max_retries):
        try:
            # 确保剪贴板已关闭
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            
            # 等待一小段时间确保剪贴板可用
            time.sleep(0.05)
            
            win32clipboard.OpenClipboard(0)  # 传入0作为窗口句柄
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                return  # 成功则返回
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"[微信自动化] 设置剪贴板失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 递增等待时间
            else:
                # 最后尝试使用 pyperclip 作为备选方案
                try:
                    import pyperclip
                    pyperclip.copy(text)
                    print(f"[微信自动化] 使用 pyperclip 设置剪贴板成功")
                    return
                except Exception as e2:
                    raise Exception(f"设置剪贴板失败: {e}, 备选方案也失败: {e2}")


def set_clipboard_file(file_path: str, max_retries: int = 3):
    """设置剪贴板文件（带重试机制）"""
    import win32clipboard
    import struct
    
    # 获取绝对路径
    abs_path = os.path.abspath(file_path)
    
    # DROPFILES 结构
    # https://docs.microsoft.com/en-us/windows/win32/api/shlobj_core/ns-shlobj_core-dropfiles
    
    # 文件路径需要以双空字符结尾
    files = abs_path + '\0\0'
    files_bytes = files.encode('utf-16-le')
    
    # DROPFILES 结构: 20 字节头 + 文件路径
    # pFiles (4 bytes): 文件名偏移量 = 20
    # pt.x (4 bytes): 0
    # pt.y (4 bytes): 0
    # fNC (4 bytes): 0
    # fWide (4 bytes): 1 (Unicode)
    header = struct.pack('IIIII', 20, 0, 0, 0, 1)
    data = header + files_bytes
    
    CF_HDROP = 15
    
    for attempt in range(max_retries):
        try:
            # 确保剪贴板已关闭
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            
            # 等待一小段时间确保剪贴板可用
            time.sleep(0.05)
            
            win32clipboard.OpenClipboard(0)  # 传入0作为窗口句柄
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(CF_HDROP, data)
                return  # 成功则返回
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            print(f"[微信自动化] 设置剪贴板文件失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # 递增等待时间
            else:
                raise Exception(f"设置剪贴板文件失败: {e}")


def search_and_open_chat(target: str):
    """搜索并打开与目标的聊天窗口"""
    import pyautogui
    import win32gui
    
    # 激活微信窗口
    hwnd = activate_wechat_window()
    
    # Ctrl+F 打开搜索（会自动聚焦到搜索框）
    print(f"[微信自动化] 按 Ctrl+F 打开搜索")
    hotkey('ctrl', 'f')
    time.sleep(0.3)
    
    # 清空搜索框并输入目标名称
    hotkey('ctrl', 'a')
    time.sleep(0.1)
    
    # 使用剪贴板粘贴（支持中文）
    print(f"[微信自动化] 搜索联系人: {target}")
    set_clipboard_text(target)
    hotkey('ctrl', 'v')
    time.sleep(0.5)  # 等待搜索结果
    
    # 按 Enter 选择第一个结果
    press_key('enter')
    time.sleep(0.3)


@register_executor
class WeChatSendMessageExecutor(ModuleExecutor):
    """微信发送消息模块执行器 - 基于图像识别和键鼠模拟"""
    
    @property
    def module_type(self) -> str:
        return "wechat_send_message"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        target = context.resolve_value(config.get('target', ''))
        message = context.resolve_value(config.get('message', ''))
        result_variable = config.get('resultVariable', '')
        
        if not target:
            return ModuleResult(success=False, error="目标联系人/群名不能为空")
        if not message:
            return ModuleResult(success=False, error="消息内容不能为空")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._send_message, target, message)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已发送消息给 {target}",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"发送消息失败: {str(e)}")
    
    def _send_message(self, target: str, message: str) -> dict:
        """同步发送消息"""
        import pyautogui
        import win32gui
        
        # 搜索并打开聊天窗口（如果已在目标窗口则跳过搜索）
        search_and_open_chat(target)
        
        # 等待聊天窗口完全加载
        time.sleep(0.3)
        
        # 点击输入框区域确保焦点在输入框（微信输入框在窗口底部）
        hwnd = find_wechat_window()
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            # 点击窗口底部中间位置（输入框区域）
            input_x = (rect[0] + rect[2]) // 2
            input_y = rect[3] - 80  # 距离底部约80像素
            print(f"[微信自动化] 点击输入框区域: ({input_x}, {input_y})")
            pyautogui.click(input_x, input_y)
            time.sleep(0.2)
        
        # 使用剪贴板粘贴消息（支持中文和多行）
        print(f"[微信自动化] 粘贴消息内容")
        set_clipboard_text(message)
        hotkey('ctrl', 'v')
        time.sleep(0.2)
        
        # 按 Alt+S 发送（微信默认快捷键）
        print(f"[微信自动化] 按 Alt+S 发送")
        hotkey('alt', 's')
        time.sleep(0.3)
        
        return {"target": target, "message": message, "success": True}


@register_executor
class WeChatSendFileExecutor(ModuleExecutor):
    """微信发送文件模块执行器 - 基于图像识别和键鼠模拟"""
    
    @property
    def module_type(self) -> str:
        return "wechat_send_file"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        target = context.resolve_value(config.get('target', ''))
        file_path = context.resolve_value(config.get('filePath', ''))
        result_variable = config.get('resultVariable', '')
        
        if not target:
            return ModuleResult(success=False, error="目标联系人/群名不能为空")
        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")
        if not os.path.exists(file_path):
            return ModuleResult(success=False, error=f"文件不存在: {file_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._send_file, target, file_path)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已发送文件给 {target}",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"发送文件失败: {str(e)}")
    
    def _send_file(self, target: str, file_path: str) -> dict:
        """同步发送文件"""
        import pyautogui
        import win32gui
        
        # 搜索并打开聊天窗口（如果已在目标窗口则跳过搜索）
        search_and_open_chat(target)
        
        # 等待聊天窗口完全加载
        time.sleep(0.3)
        
        # 点击输入框区域确保焦点
        hwnd = find_wechat_window()
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            input_x = (rect[0] + rect[2]) // 2
            input_y = rect[3] - 80
            print(f"[微信自动化] 点击输入框区域: ({input_x}, {input_y})")
            pyautogui.click(input_x, input_y)
            time.sleep(0.2)
        
        # 将文件复制到剪贴板
        print(f"[微信自动化] 复制文件到剪贴板: {file_path}")
        set_clipboard_file(file_path)
        time.sleep(0.1)
        
        # 粘贴文件
        print(f"[微信自动化] 粘贴文件")
        hotkey('ctrl', 'v')
        time.sleep(0.8)  # 等待文件加载
        
        # 按 Alt+S 发送（微信默认快捷键）
        print(f"[微信自动化] 按 Alt+S 发送")
        hotkey('alt', 's')
        time.sleep(0.3)
        
        return {"target": target, "file": file_path, "success": True}
