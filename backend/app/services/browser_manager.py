"""全局浏览器管理器 - 确保所有功能共享同一个浏览器实例"""
import subprocess
import json
import threading
import sys
from pathlib import Path
from typing import Optional, Callable

# 浏览器进程
_browser_proc: Optional[subprocess.Popen] = None
_browser_lock = threading.Lock()
_browser_open = False
_picker_active = False
_current_browser_type = 'msedge'  # 当前使用的浏览器类型
_current_executable_path = ''  # 当前使用的自定义浏览器路径
_current_fullscreen = False  # 当前是否全屏

# 用户数据目录
USER_DATA_DIR = Path(__file__).parent.parent.parent / "browser_data"
# 确保目录存在
USER_DATA_DIR.mkdir(exist_ok=True)


def get_user_data_dir() -> str:
    """获取用户数据目录"""
    return str(USER_DATA_DIR)


def is_browser_open() -> bool:
    """检查浏览器是否打开"""
    return _browser_open and _browser_proc is not None and _browser_proc.poll() is None


def get_browser_proc() -> Optional[subprocess.Popen]:
    """获取浏览器进程"""
    return _browser_proc


def start_browser(browser_type: str = 'msedge', executable_path: Optional[str] = None, user_data_dir: Optional[str] = None, fullscreen: bool = False) -> tuple[bool, str]:
    """启动浏览器进程，返回 (成功与否, 错误信息)
    
    Args:
        browser_type: 浏览器类型，支持 'msedge', 'chrome', 'chromium', 'firefox'
        executable_path: 自定义浏览器可执行文件路径（可选）
        user_data_dir: 自定义浏览器数据缓存目录（可选）
        fullscreen: 是否全屏启动（可选）
    """
    global _browser_proc, _browser_open, _current_browser_type, _current_executable_path, _current_fullscreen
    
    with _browser_lock:
        if is_browser_open():
            return True, ""
        
        script_path = Path(__file__).parent / "browser_process.py"
        print(f"[BrowserManager] Starting browser process: {script_path}")
        print(f"[BrowserManager] Browser type: {browser_type}, executable_path: {executable_path}, user_data_dir: {user_data_dir}, fullscreen: {fullscreen}")
        
        try:
            # 构建启动参数
            args = [sys.executable, str(script_path)]
            
            # 传递浏览器配置
            env_vars = {
                'BROWSER_TYPE': browser_type,
                'BROWSER_FULLSCREEN': '1' if fullscreen else '0',
            }
            if executable_path:
                env_vars['BROWSER_EXECUTABLE_PATH'] = executable_path
            if user_data_dir:
                env_vars['BROWSER_USER_DATA_DIR'] = user_data_dir
            
            import os
            env = os.environ.copy()
            env.update(env_vars)
            
            _browser_proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
            )
            
            _current_browser_type = browser_type
            _current_executable_path = executable_path or ''
            _current_fullscreen = fullscreen
            
            # 等待 playwright 启动（设置超时）
            import select
            import time
            
            start_time = time.time()
            timeout = 30  # 30秒超时
            
            while time.time() - start_time < timeout:
                line = _browser_proc.stdout.readline()
                print(f"[BrowserManager] Received: {line.strip()}")
                if line:
                    try:
                        data = json.loads(line)
                        if data.get('status') == 'playwright_started':
                            print("[BrowserManager] Playwright started, waiting for browser...")
                            continue
                        elif data.get('status') == 'browser_opened':
                            _browser_open = True
                            print("[BrowserManager] Browser started successfully")
                            return True, ""
                        elif data.get('status') == 'closed':
                            reason = data.get('reason', 'unknown')
                            print(f"[BrowserManager] Browser closed: {reason}")
                            return False, f"浏览器启动后立即关闭: {reason}"
                        elif data.get('status') == 'error':
                            error_msg = data.get('error', '未知错误')
                            print(f"[BrowserManager] Browser error: {error_msg}")
                            return False, error_msg
                    except json.JSONDecodeError:
                        print(f"[BrowserManager] Invalid JSON: {line}")
                        continue
                else:
                    # 检查进程是否还在运行
                    if _browser_proc.poll() is not None:
                        stderr = _browser_proc.stderr.read()
                        print(f"[BrowserManager] Process exited, stderr: {stderr}")
                        
                        # 详细的错误分类
                        if "user-data-dir" in stderr.lower() or "already in use" in stderr.lower():
                            error_detail = "❌ 浏览器数据目录被占用"
                            solution = f"\n\n💡 解决方案:\n1. 关闭所有 {browser_type} 浏览器窗口\n2. 打开任务管理器，结束所有 {browser_type}.exe 进程\n3. 如果问题仍然存在，重启电脑"
                            return False, error_detail + solution
                        
                        elif "executable doesn't exist" in stderr.lower() or "browser is not installed" in stderr.lower():
                            error_detail = f"❌ {browser_type} 浏览器驱动未安装"
                            solution = f"\n\n💡 解决方案:\n1. 运行命令安装浏览器驱动:\n   playwright install {browser_type}\n\n2. 或者安装所有浏览器:\n   playwright install\n\n3. 如果命令失败，请检查网络连接"
                            return False, error_detail + solution
                        
                        elif "permission denied" in stderr.lower() or "access denied" in stderr.lower():
                            error_detail = "❌ 权限不足"
                            solution = "\n\n💡 解决方案:\n1. 以管理员身份运行 WebRPA\n2. 检查杀毒软件是否阻止了浏览器启动\n3. 检查文件和目录的权限设置"
                            return False, error_detail + solution
                        
                        elif stderr:
                            error_detail = f"❌ 浏览器进程异常退出"
                            error_msg = stderr[:500] if len(stderr) > 500 else stderr
                            solution = f"\n\n原始错误:\n{error_msg}\n\n💡 解决方案:\n1. 检查系统资源是否充足\n2. 重启电脑后重试\n3. 查看完整日志以获取更多信息"
                            return False, error_detail + solution
                        else:
                            return False, "❌ 浏览器进程异常退出（无错误信息）\n\n💡 解决方案:\n1. 重启电脑后重试\n2. 检查系统日志\n3. 尝试使用其他浏览器类型"
                    time.sleep(0.1)
            
            print("[BrowserManager] Timeout waiting for browser to start")
            
            # 超时后检查进程状态
            if _browser_proc and _browser_proc.poll() is not None:
                stderr = _browser_proc.stderr.read()
                error_detail = "❌ 浏览器启动超时（进程已退出）"
                if stderr:
                    error_msg = stderr[:500] if len(stderr) > 500 else stderr
                    solution = f"\n\n原始错误:\n{error_msg}\n\n💡 解决方案:\n1. 检查系统资源是否充足（内存、CPU）\n2. 关闭其他占用资源的程序\n3. 重启电脑后重试"
                else:
                    solution = "\n\n💡 解决方案:\n1. 检查系统资源是否充足\n2. 重启电脑后重试\n3. 尝试使用其他浏览器类型"
                return False, error_detail + solution
            else:
                error_detail = "❌ 浏览器启动超时（30秒）"
                solution = "\n\n💡 解决方案:\n1. 系统配置较低，浏览器启动较慢，请稍后重试\n2. 检查系统资源是否充足（内存、磁盘空间）\n3. 关闭其他占用资源的程序\n4. 重启电脑后重试\n5. 如果是首次启动，可能正在下载浏览器驱动，请耐心等待"
                return False, error_detail + solution
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[BrowserManager] Failed to start browser: {e}")
            print(error_trace)
            
            # 详细的错误分类
            error_msg = str(e)
            error_detail = "❌ 启动浏览器进程失败"
            
            if "filenotfounderror" in error_msg.lower() or "no such file" in error_msg.lower():
                solution = "\n\n💡 解决方案:\n1. 检查 Python 环境是否正确\n2. 检查 browser_process.py 文件是否存在\n3. 重新安装 WebRPA"
            elif "permission" in error_msg.lower():
                solution = "\n\n💡 解决方案:\n1. 以管理员身份运行 WebRPA\n2. 检查文件权限设置\n3. 检查杀毒软件是否阻止了进程启动"
            else:
                solution = f"\n\n原始错误:\n{error_msg}\n\n💡 解决方案:\n1. 重启电脑后重试\n2. 检查系统日志\n3. 联系技术支持并提供完整错误信息"
            
            return False, error_detail + solution


def stop_browser():
    """停止浏览器进程"""
    global _browser_proc, _browser_open, _picker_active
    
    with _browser_lock:
        if _browser_proc:
            try:
                _browser_proc.stdin.write(json.dumps({"action": "quit"}) + "\n")
                _browser_proc.stdin.flush()
                _browser_proc.wait(timeout=5)
            except:
                try:
                    _browser_proc.terminate()
                except:
                    pass
            _browser_proc = None
        
        _browser_open = False
        _picker_active = False


def send_command(action: str, **kwargs) -> dict:
    """发送命令到浏览器进程"""
    global _browser_proc, _browser_open
    
    if not is_browser_open():
        return {"success": False, "error": "浏览器未打开"}
    
    try:
        cmd = json.dumps({"action": action, **kwargs})
        _browser_proc.stdin.write(cmd + "\n")
        _browser_proc.stdin.flush()
        
        line = _browser_proc.stdout.readline()
        if line:
            result = json.loads(line)
            # 检查是否浏览器已关闭
            if result.get("status") == "closed":
                _browser_open = False
                return {"success": False, "error": "浏览器已关闭"}
            return result
        return {"success": False, "error": "无响应"}
    except Exception as e:
        # 如果发生异常，可能是进程已终止
        if _browser_proc and _browser_proc.poll() is not None:
            _browser_open = False
        return {"success": False, "error": str(e)}


def navigate(url: str) -> dict:
    """导航到指定URL"""
    return send_command("navigate", url=url)


def start_picker() -> dict:
    """启动元素选择器"""
    global _picker_active
    result = send_command("start_picker")
    if result.get("success"):
        _picker_active = True
    return result


def stop_picker() -> dict:
    """停止元素选择器"""
    global _picker_active
    result = send_command("stop_picker")
    _picker_active = False
    return result


def get_selected_element() -> dict:
    """获取选中的元素"""
    return send_command("get_selected")


def get_similar_elements() -> dict:
    """获取相似元素"""
    return send_command("get_similar")


def is_picker_active() -> bool:
    """检查选择器是否激活"""
    return _picker_active


def find_page_by_url(url: str) -> dict:
    """查找是否有页面已打开指定URL"""
    return send_command("find_page_by_url", url=url)


def switch_to_page(page_index: int) -> dict:
    """切换到指定索引的页面"""
    return send_command("switch_to_page", pageIndex=page_index)


def ensure_browser_open(browser_type: str = 'msedge', executable_path: Optional[str] = None, fullscreen: bool = False) -> bool:
    """确保浏览器已打开，如果没有则启动。如果浏览器配置变化，会先关闭再重新打开。
    
    Args:
        browser_type: 浏览器类型
        executable_path: 自定义浏览器路径
        fullscreen: 是否全屏启动
    """
    global _current_browser_type, _current_executable_path, _current_fullscreen
    
    exec_path = executable_path or ''
    
    # 如果浏览器已打开，检查配置是否一致
    if is_browser_open():
        # 配置一致，直接返回
        if _current_browser_type == browser_type and _current_executable_path == exec_path and _current_fullscreen == fullscreen:
            return True
        # 配置不一致，需要关闭重新打开
        print(f"[BrowserManager] 浏览器配置已变化，重新启动浏览器")
        stop_browser()
    
    success, _ = start_browser(browser_type, executable_path, fullscreen)
    return success
