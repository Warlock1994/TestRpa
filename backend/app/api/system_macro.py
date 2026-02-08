"""系统宏录制相关API"""
import time
import ctypes
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# 全局录制状态
macro_recording_state = {
    "is_recording": False,
    "actions": [],
    "start_time": 0,
    "options": {},
    "mouse_listener": None,
    "keyboard_listener": None,
    "last_move_time": 0,
    "hotkey_listener": None,
    "pending_start": False,
    "pending_stop": False,
}


class MacroStartRequest(BaseModel):
    recordMouseMove: bool = True
    recordMouseClick: bool = True
    recordKeyboard: bool = True
    recordScroll: bool = True
    mouseMoveInterval: int = 16


@router.post("/macro/start")
async def start_macro_recording(request: MacroStartRequest):
    """开始宏录制"""
    global macro_recording_state
    
    if macro_recording_state["is_recording"]:
        return {"success": False, "error": "已经在录制中"}
    
    try:
        from pynput import mouse, keyboard
    except ImportError:
        return {"success": False, "error": "pynput 库未安装，请运行: pip install pynput"}
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    def get_real_cursor_pos():
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    
    macro_recording_state["is_recording"] = True
    macro_recording_state["actions"] = []
    macro_recording_state["start_time"] = time.time() * 1000
    macro_recording_state["last_move_time"] = 0
    macro_recording_state["pending_start"] = False
    macro_recording_state["pending_stop"] = False
    macro_recording_state["options"] = {
        "recordMouseMove": request.recordMouseMove,
        "recordMouseClick": request.recordMouseClick,
        "recordKeyboard": request.recordKeyboard,
        "recordScroll": request.recordScroll,
        "mouseMoveInterval": request.mouseMoveInterval,
    }
    
    options = macro_recording_state["options"]
    
    def get_time():
        return int(time.time() * 1000 - macro_recording_state["start_time"])
    
    def on_mouse_move(x, y):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordMouseMove"]:
            return True
        
        current_time = get_time()
        if current_time - macro_recording_state["last_move_time"] >= options["mouseMoveInterval"]:
            macro_recording_state["last_move_time"] = current_time
            real_x, real_y = get_real_cursor_pos()
            macro_recording_state["actions"].append({"type": "mouse_move", "time": current_time, "x": real_x, "y": real_y})
        return True
    
    def on_mouse_click(x, y, button, pressed):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordMouseClick"]:
            return True
        
        button_name = "left"
        if button == mouse.Button.right:
            button_name = "right"
        elif button == mouse.Button.middle:
            button_name = "middle"
        
        real_x, real_y = get_real_cursor_pos()
        macro_recording_state["actions"].append({"type": "mouse_click", "time": get_time(), "x": real_x, "y": real_y, "button": button_name, "pressed": pressed})
        return True
    
    def on_mouse_scroll(x, y, dx, dy):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordScroll"]:
            return True
        
        delta = int(dy * 120)
        real_x, real_y = get_real_cursor_pos()
        macro_recording_state["actions"].append({"type": "mouse_scroll", "time": get_time(), "x": real_x, "y": real_y, "delta": delta})
        return True
    
    def on_key_press(key):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordKeyboard"]:
            return True
        
        try:
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                vk_code = ord(key.char.upper()) if hasattr(key, 'char') and key.char else 0
        except:
            vk_code = 0
        
        if vk_code in (0x78, 0x79):
            return True
        
        if vk_code > 0:
            macro_recording_state["actions"].append({"type": "key_press", "time": get_time(), "keyCode": vk_code, "pressed": True})
        return True
    
    def on_key_release(key):
        if not macro_recording_state["is_recording"]:
            return False
        if not options["recordKeyboard"]:
            return True
        
        try:
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                vk_code = ord(key.char.upper()) if hasattr(key, 'char') and key.char else 0
        except:
            vk_code = 0
        
        if vk_code in (0x78, 0x79):
            return True
        
        if vk_code > 0:
            macro_recording_state["actions"].append({"type": "key_press", "time": get_time(), "keyCode": vk_code, "pressed": False})
        return True
    
    mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll)
    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    macro_recording_state["mouse_listener"] = mouse_listener
    macro_recording_state["keyboard_listener"] = keyboard_listener
    
    return {"success": True, "message": "录制已开始"}


@router.post("/macro/stop")
async def stop_macro_recording():
    """停止宏录制"""
    global macro_recording_state
    
    if not macro_recording_state["is_recording"]:
        return {"success": False, "error": "没有正在进行的录制"}
    
    macro_recording_state["is_recording"] = False
    
    if macro_recording_state["mouse_listener"]:
        macro_recording_state["mouse_listener"].stop()
        macro_recording_state["mouse_listener"] = None
    
    if macro_recording_state["keyboard_listener"]:
        macro_recording_state["keyboard_listener"].stop()
        macro_recording_state["keyboard_listener"] = None
    
    actions = macro_recording_state["actions"]
    
    return {"success": True, "actions": actions, "count": len(actions)}


@router.get("/macro/data")
async def get_macro_data():
    """获取当前录制的数据和快捷键触发状态"""
    global macro_recording_state
    
    pending_start = macro_recording_state.get("pending_start", False)
    pending_stop = macro_recording_state.get("pending_stop", False)
    
    if pending_start:
        macro_recording_state["pending_start"] = False
    if pending_stop:
        macro_recording_state["pending_stop"] = False
    
    return {
        "success": True,
        "isRecording": macro_recording_state["is_recording"],
        "actions": macro_recording_state["actions"],
        "count": len(macro_recording_state["actions"]),
        "pendingStart": pending_start,
        "pendingStop": pending_stop,
    }


@router.post("/macro/hotkey/start")
async def start_macro_hotkey_listener():
    """启动全局快捷键监听器（F9开始录制，F10停止录制）"""
    global macro_recording_state
    
    if macro_recording_state.get("hotkey_listener"):
        try:
            macro_recording_state["hotkey_listener"].stop()
        except:
            pass
        macro_recording_state["hotkey_listener"] = None
    
    try:
        from pynput import keyboard
    except ImportError:
        return {"success": False, "error": "pynput 库未安装"}
    
    def on_hotkey_press(key):
        try:
            if hasattr(key, 'vk'):
                vk_code = key.vk
            elif hasattr(key, 'value'):
                vk_code = key.value.vk
            else:
                return True
            
            if vk_code == 0x78:
                if not macro_recording_state["is_recording"]:
                    macro_recording_state["pending_start"] = True
            elif vk_code == 0x79:
                if macro_recording_state["is_recording"]:
                    macro_recording_state["pending_stop"] = True
        except:
            pass
        return True
    
    hotkey_listener = keyboard.Listener(on_press=on_hotkey_press)
    hotkey_listener.start()
    
    macro_recording_state["hotkey_listener"] = hotkey_listener
    
    return {"success": True, "message": "全局快捷键监听已启动 (F9开始, F10停止)"}


@router.post("/macro/hotkey/stop")
async def stop_macro_hotkey_listener():
    """停止全局快捷键监听器"""
    global macro_recording_state
    
    if macro_recording_state.get("hotkey_listener"):
        try:
            macro_recording_state["hotkey_listener"].stop()
        except:
            pass
        macro_recording_state["hotkey_listener"] = None
    
    return {"success": True, "message": "全局快捷键监听已停止"}
