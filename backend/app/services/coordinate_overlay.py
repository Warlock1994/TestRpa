"""鼠标坐标实时显示服务 - 使用独立进程"""
import subprocess
import sys
import os
import atexit
from pathlib import Path

# 全局变量
_overlay_process = None


def _cleanup_overlay():
    """清理坐标显示进程"""
    global _overlay_process
    if _overlay_process and _overlay_process.poll() is None:
        try:
            _overlay_process.terminate()
            _overlay_process.wait(timeout=1)
        except:
            try:
                _overlay_process.kill()
            except:
                pass
        _overlay_process = None


# 注册退出时清理
atexit.register(_cleanup_overlay)


def start_coordinate_overlay():
    """启动坐标显示"""
    global _overlay_process
    
    if _overlay_process and _overlay_process.poll() is None:
        return {"success": True, "message": "坐标显示已在运行"}
    
    # 获取 Python 解释器路径
    python_path = Path(__file__).parent.parent.parent.parent / "Python313" / "python.exe"
    if not python_path.exists():
        python_path = sys.executable
    
    # 获取脚本路径
    script_path = Path(__file__).parent / "coordinate_overlay_process.py"
    
    try:
        # 传递父进程 PID，让子进程能检测父进程是否退出
        _overlay_process = subprocess.Popen(
            [str(python_path), str(script_path), str(os.getpid())],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return {"success": True, "message": "坐标显示已启动"}
    except Exception as e:
        return {"success": False, "message": f"启动失败: {e}"}


def stop_coordinate_overlay():
    """停止坐标显示"""
    global _overlay_process
    
    if _overlay_process:
        try:
            _overlay_process.terminate()
            _overlay_process = None
        except:
            pass
    
    return {"success": True, "message": "坐标显示已停止"}


def is_overlay_running():
    """检查坐标显示是否在运行"""
    global _overlay_process
    return _overlay_process is not None and _overlay_process.poll() is None
