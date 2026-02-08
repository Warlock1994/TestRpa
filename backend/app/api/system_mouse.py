"""系统鼠标相关API - 坐标拾取、追踪"""
import subprocess
import sys
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

# 鼠标坐标拾取器进程
mouse_picker_process = None


@router.post("/pick-mouse-position")
async def pick_mouse_position():
    """启动鼠标坐标拾取器，返回用户点击的屏幕坐标"""
    global mouse_picker_process
    
    try:
        if mouse_picker_process and mouse_picker_process.poll() is None:
            mouse_picker_process.terminate()
            mouse_picker_process = None
        
        python_path = Path(__file__).parent.parent.parent.parent / "Python313" / "python.exe"
        if not python_path.exists():
            python_path = sys.executable
        
        picker_script = Path(__file__).parent.parent / "services" / "mouse_picker" / "picker_process.py"
        
        mouse_picker_process = subprocess.Popen(
            [str(python_path), str(picker_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        result = {"success": False, "x": None, "y": None, "cancelled": False}
        
        while True:
            line = mouse_picker_process.stdout.readline()
            if not line:
                break
            
            try:
                data = json.loads(line.decode('utf-8').strip())
                
                if data.get("status") == "started":
                    continue
                elif data.get("status") == "ready":
                    continue
                elif data.get("type") == "position":
                    pos = data.get("data", {})
                    result = {
                        "success": True,
                        "x": pos.get("x"),
                        "y": pos.get("y"),
                        "button": pos.get("button")
                    }
                    break
                elif data.get("type") == "cancelled":
                    result = {"success": False, "cancelled": True, "x": None, "y": None}
                    break
                elif data.get("status") == "closed":
                    break
                elif data.get("error"):
                    result = {"success": False, "error": data.get("error")}
                    break
            except json.JSONDecodeError:
                continue
        
        if mouse_picker_process.poll() is None:
            mouse_picker_process.terminate()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/get-current-mouse-position")
async def get_current_mouse_position():
    """获取当前鼠标位置（不需要点击）"""
    try:
        import ctypes
        
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        
        return {"success": True, "x": pt.x, "y": pt.y}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/mouse-position")
async def get_mouse_position():
    """获取当前鼠标位置"""
    import ctypes
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    
    return {"x": pt.x, "y": pt.y}


# 鼠标坐标实时显示服务
_mouse_tracker_running = False


@router.post("/mouse-tracker/start")
async def start_mouse_tracker():
    """启动鼠标坐标追踪（通过WebSocket推送）"""
    global _mouse_tracker_running
    _mouse_tracker_running = True
    return {"success": True, "message": "鼠标追踪已启动"}


@router.post("/mouse-tracker/stop")
async def stop_mouse_tracker():
    """停止鼠标坐标追踪"""
    global _mouse_tracker_running
    _mouse_tracker_running = False
    return {"success": True, "message": "鼠标追踪已停止"}


@router.get("/mouse-tracker/status")
async def get_mouse_tracker_status():
    """获取鼠标追踪状态"""
    return {"running": _mouse_tracker_running}


@router.post("/coordinate-overlay/start")
async def start_coordinate_overlay():
    """启动鼠标坐标实时显示（置顶窗口）"""
    from app.services.coordinate_overlay import start_coordinate_overlay
    return start_coordinate_overlay()


@router.post("/coordinate-overlay/stop")
async def stop_coordinate_overlay():
    """停止鼠标坐标实时显示"""
    from app.services.coordinate_overlay import stop_coordinate_overlay
    return stop_coordinate_overlay()


@router.get("/coordinate-overlay/status")
async def get_coordinate_overlay_status():
    """获取坐标显示状态"""
    from app.services.coordinate_overlay import is_overlay_running
    return {"running": is_overlay_running()}
