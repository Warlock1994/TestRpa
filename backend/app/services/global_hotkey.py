"""全局热键服务 - 支持后台快捷键控制工作流运行/停止"""
import asyncio
import threading
from typing import Callable, Optional
from pynput import keyboard


class GlobalHotkeyService:
    """全局热键服务，监听系统级快捷键"""
    
    _instance: Optional['GlobalHotkeyService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 回调函数
        self._on_run_workflow: Optional[Callable[[], None]] = None
        self._on_stop_workflow: Optional[Callable[[], None]] = None
        self._on_macro_start: Optional[Callable[[], None]] = None  # F9 - 开始录制宏
        self._on_macro_stop: Optional[Callable[[], None]] = None   # F10 - 停止录制宏
        
        # 当前按下的修饰键
        self._pressed_keys: set = set()
        
        # 热键配置 (默认: F5 运行, Shift+F5 停止)
        self._run_hotkey = {keyboard.Key.f5}  # F5
        self._stop_hotkey = {keyboard.Key.shift, keyboard.Key.f5}  # Shift+F5
        
        # 是否启用
        self._enabled = True
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """设置主事件循环"""
        self._main_loop = loop
    
    def set_callbacks(self, 
                      on_run: Optional[Callable[[], None]] = None,
                      on_stop: Optional[Callable[[], None]] = None,
                      on_macro_start: Optional[Callable[[], None]] = None,
                      on_macro_stop: Optional[Callable[[], None]] = None):
        """设置回调函数"""
        self._on_run_workflow = on_run
        self._on_stop_workflow = on_stop
        self._on_macro_start = on_macro_start
        self._on_macro_stop = on_macro_stop
    
    def set_enabled(self, enabled: bool):
        """启用/禁用热键"""
        self._enabled = enabled
        print(f"[GlobalHotkey] 热键已{'启用' if enabled else '禁用'}")
    
    def _normalize_key(self, key) -> Optional[keyboard.Key]:
        """标准化按键"""
        if isinstance(key, keyboard.Key):
            # 统一左右修饰键
            if key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
                return keyboard.Key.shift
            if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                return keyboard.Key.ctrl
            if key in (keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
                return keyboard.Key.alt
            return key
        return None
    
    def _on_press(self, key):
        """按键按下事件"""
        if not self._enabled:
            return
        
        normalized = self._normalize_key(key)
        if normalized:
            self._pressed_keys.add(normalized)
        
        # 检查是否匹配停止热键 (Shift+F5)
        if self._stop_hotkey.issubset(self._pressed_keys):
            print("[GlobalHotkey] 检测到停止热键: Shift+F5")
            self._trigger_stop()
            return
        
        # 检查是否匹配运行热键 (F5，但不能同时按Shift)
        if self._run_hotkey.issubset(self._pressed_keys) and keyboard.Key.shift not in self._pressed_keys:
            print("[GlobalHotkey] 检测到运行热键: F5")
            self._trigger_run()
            return
        
        # 检查F9 - 开始录制宏
        if normalized == keyboard.Key.f9:
            print("[GlobalHotkey] 检测到宏录制开始热键: F9")
            self._trigger_macro_start()
            return
        
        # 检查F10 - 停止录制宏
        if normalized == keyboard.Key.f10:
            print("[GlobalHotkey] 检测到宏录制停止热键: F10")
            self._trigger_macro_stop()
            return
    
    def _on_release(self, key):
        """按键释放事件"""
        normalized = self._normalize_key(key)
        if normalized:
            self._pressed_keys.discard(normalized)
    
    def _trigger_run(self):
        """触发运行工作流"""
        if self._on_run_workflow and self._main_loop:
            # 在主事件循环中执行回调
            asyncio.run_coroutine_threadsafe(
                self._async_run_callback(),
                self._main_loop
            )
    
    def _trigger_stop(self):
        """触发停止工作流"""
        if self._on_stop_workflow and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_stop_callback(),
                self._main_loop
            )
    
    def _trigger_macro_start(self):
        """触发开始录制宏"""
        if self._on_macro_start and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_macro_start_callback(),
                self._main_loop
            )
    
    def _trigger_macro_stop(self):
        """触发停止录制宏"""
        if self._on_macro_stop and self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._async_macro_stop_callback(),
                self._main_loop
            )
    
    async def _async_run_callback(self):
        """异步执行运行回调"""
        if self._on_run_workflow:
            try:
                result = self._on_run_workflow()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 运行回调异常: {e}")
    
    async def _async_stop_callback(self):
        """异步执行停止回调"""
        if self._on_stop_workflow:
            try:
                result = self._on_stop_workflow()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 停止回调异常: {e}")
    
    async def _async_macro_start_callback(self):
        """异步执行宏录制开始回调"""
        if self._on_macro_start:
            try:
                result = self._on_macro_start()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 宏录制开始回调异常: {e}")
    
    async def _async_macro_stop_callback(self):
        """异步执行宏录制停止回调"""
        if self._on_macro_stop:
            try:
                result = self._on_macro_stop()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[GlobalHotkey] 宏录制停止回调异常: {e}")
    
    def start(self):
        """启动热键监听"""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.start()
        print("[GlobalHotkey] 全局热键服务已启动 (F5=运行, Shift+F5=停止, F9=开始录制宏, F10=停止录制宏)")
    
    def stop(self):
        """停止热键监听"""
        if not self._running:
            return
        
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        print("[GlobalHotkey] 全局热键服务已停止")


# 全局单例
_hotkey_service: Optional[GlobalHotkeyService] = None


def get_hotkey_service() -> GlobalHotkeyService:
    """获取全局热键服务实例"""
    global _hotkey_service
    if _hotkey_service is None:
        _hotkey_service = GlobalHotkeyService()
    return _hotkey_service
