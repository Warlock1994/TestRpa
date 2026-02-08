"""鼠标坐标拾取器进程 - 使用 pynput 进行全局键鼠监听
用户按住 Ctrl+左键 获取坐标，Ctrl+右键 或 ESC 取消
"""
import json
import sys
import threading
import ctypes

# 设置 DPI 感知，确保获取真实物理像素坐标
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# 全局状态
ctrl_pressed = False
result_sent = False
result_lock = threading.Lock()


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_pos():
    """获取当前鼠标位置（使用 Windows API 更准确）"""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def send_result(data):
    """发送结果并退出"""
    global result_sent
    with result_lock:
        if result_sent:
            return
        result_sent = True
    print(json.dumps(data), flush=True)
    # 停止监听器
    return False


def on_click(x, y, button, pressed):
    """鼠标点击回调"""
    global ctrl_pressed
    
    # 只处理释放事件
    if pressed:
        return True
    
    from pynput.mouse import Button
    
    # Ctrl + 左键释放 = 确认坐标
    if ctrl_pressed and button == Button.left:
        # 使用 Windows API 获取更准确的坐标
        real_x, real_y = get_cursor_pos()
        send_result({
            "type": "position",
            "data": {"x": real_x, "y": real_y, "button": "left"}
        })
        return False  # 停止监听
    
    # Ctrl + 右键释放 = 取消
    if ctrl_pressed and button == Button.right:
        send_result({"type": "cancelled"})
        return False  # 停止监听
    
    return True


def on_press(key):
    """键盘按下回调"""
    global ctrl_pressed
    
    from pynput.keyboard import Key
    
    if key in (Key.ctrl_l, Key.ctrl_r):
        ctrl_pressed = True
    elif key == Key.esc:
        send_result({"type": "cancelled"})
        return False  # 停止监听
    
    return True


def on_release(key):
    """键盘释放回调"""
    global ctrl_pressed
    
    from pynput.keyboard import Key
    
    if key in (Key.ctrl_l, Key.ctrl_r):
        ctrl_pressed = False
    
    return True


def main():
    """主函数"""
    global result_sent
    
    try:
        from pynput import mouse, keyboard
    except ImportError:
        print(json.dumps({"error": "pynput 未安装，请运行: pip install pynput"}), flush=True)
        print(json.dumps({"status": "closed"}), flush=True)
        return
    
    print(json.dumps({"status": "started"}), flush=True)
    print(json.dumps({"status": "ready"}), flush=True)
    
    try:
        # 创建监听器
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        
        # 启动监听器
        mouse_listener.start()
        keyboard_listener.start()
        
        # 等待监听器结束
        mouse_listener.join()
        keyboard_listener.stop()
        
    except Exception as e:
        if not result_sent:
            print(json.dumps({"error": str(e)}), flush=True)
    finally:
        print(json.dumps({"status": "closed"}), flush=True)


if __name__ == '__main__':
    main()
