"""手机坐标选择器 - 最终方案：正确的坐标转换"""
from typing import Optional, Tuple, Callable
import win32gui
import ctypes
from pynput import mouse, keyboard

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass


class PhoneCoordinatePicker:
    """坐标选择器 - 正确处理坐标转换"""
    
    def __init__(self):
        self.is_active = False
        self.ctrl_pressed = False
        self.scrcpy_hwnd: Optional[int] = None
        self.picked_coordinate: Optional[Tuple[int, int]] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.callback: Optional[Callable[[int, int], None]] = None
        # 手机分辨率
        self.phone_width: Optional[int] = None
        self.phone_height: Optional[int] = None
        
    def set_phone_resolution(self, width: int, height: int):
        """设置手机分辨率"""
        self.phone_width = width
        self.phone_height = height
        print(f"[坐标选择器] 手机分辨率: {width}x{height}")
        
    def find_scrcpy_window(self) -> Optional[int]:
        """查找 Scrcpy 窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "手机" in title:
                    windows.append((hwnd, title))
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0][0] if windows else None
    
    def on_click(self, x: int, y: int, button, pressed: bool):
        """鼠标点击"""
        if not self.is_active or button != mouse.Button.left or not pressed or not self.ctrl_pressed:
            return
        
        if not self.scrcpy_hwnd:
            self.scrcpy_hwnd = self.find_scrcpy_window()
        
        if self.scrcpy_hwnd and self.phone_width and self.phone_height:
            try:
                # 获取窗口客户区坐标
                point = win32gui.ClientToScreen(self.scrcpy_hwnd, (0, 0))
                client_rect = win32gui.GetClientRect(self.scrcpy_hwnd)
                window_width = client_rect[2]
                window_height = client_rect[3]
                
                relative_x = x - point[0]
                relative_y = y - point[1]
                
                if 0 <= relative_x < window_width and 0 <= relative_y < window_height:
                    # 核心思路：根据窗口方向来判断手机分辨率应该如何使用
                    # 
                    # 如果窗口是横屏（宽>高），说明 Scrcpy 显示的是横屏内容
                    # 此时手机的实际分辨率也应该是横屏格式（宽>高）
                    # 
                    # 如果 API 传入的分辨率是竖屏格式（宽<高），我们需要交换宽高
                    
                    window_is_landscape = window_width > window_height
                    phone_is_landscape = self.phone_width > self.phone_height
                    
                    # 确定实际使用的手机分辨率
                    if window_is_landscape != phone_is_landscape:
                        # 窗口和分辨率方向不一致，交换宽高
                        actual_phone_width = self.phone_height
                        actual_phone_height = self.phone_width
                    else:
                        # 窗口和分辨率方向一致，直接使用
                        actual_phone_width = self.phone_width
                        actual_phone_height = self.phone_height
                    
                    # 按比例映射坐标
                    phone_x = int(relative_x * actual_phone_width / window_width)
                    phone_y = int(relative_y * actual_phone_height / window_height)
                    
                    # 确保在范围内
                    phone_x = max(0, min(phone_x, actual_phone_width - 1))
                    phone_y = max(0, min(phone_y, actual_phone_height - 1))
                    
                    print(f"[坐标选择器] ✅ 已获取坐标: ({phone_x}, {phone_y})")
                    
                    self.picked_coordinate = (phone_x, phone_y)
                    
                    if self.callback:
                        self.callback(phone_x, phone_y)
            except Exception as e:
                print(f"[坐标选择器] 错误: {e}")
                import traceback
                traceback.print_exc()
    
    def on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.esc:
                self.stop()
        except:
            pass
    
    def on_key_release(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
        except:
            pass
    
    def start(self, callback: Optional[Callable[[int, int], None]] = None):
        if self.is_active:
            return
        
        self.is_active = True
        self.picked_coordinate = None
        self.callback = callback
        self.scrcpy_hwnd = self.find_scrcpy_window()
        
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
        
        print("[坐标选择器] 已启动")
    
    def stop(self):
        if not self.is_active:
            return
        
        self.is_active = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        print("[坐标选择器] 已停止")
    
    def get_picked_coordinate(self) -> Optional[Tuple[int, int]]:
        return self.picked_coordinate


_picker: Optional[PhoneCoordinatePicker] = None

def get_coordinate_picker() -> PhoneCoordinatePicker:
    global _picker
    if _picker is None:
        _picker = PhoneCoordinatePicker()
    return _picker
