"""屏幕共享服务 - 提供局域网实时屏幕共享功能

使用 WebSocket + MJPEG 流实现低延迟屏幕共享
"""
import asyncio
import io
import socket
import threading
import time
import json
import struct
from pathlib import Path
from typing import Optional, Dict, Set
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mss
from PIL import Image


def get_local_ip() -> str:
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# 全局屏幕共享服务管理
_screen_share_servers: Dict[int, dict] = {}  # port -> {server, thread, stop_event, ...}


class ScreenCaptureThread(threading.Thread):
    """屏幕捕获线程 - 持续捕获屏幕并推送给所有客户端"""
    
    def __init__(self, port: int, fps: int = 30, quality: int = 70, scale: float = 1.0):
        super().__init__(daemon=True)
        self.port = port
        self.fps = min(max(fps, 1), 60)  # 限制 1-60 fps
        self.quality = min(max(quality, 10), 100)  # 限制 10-100
        self.scale = min(max(scale, 0.1), 1.0)  # 限制 0.1-1.0
        self.stop_event = threading.Event()
        self.clients: Set = set()  # 存储客户端连接
        self.clients_lock = threading.Lock()
        self.latest_frame: Optional[bytes] = None
        self.frame_lock = threading.Lock()
        self.frame_ready = threading.Event()
        self.frame_version = 0  # 帧版本号，用于检测新帧
    
    def add_client(self, client):
        with self.clients_lock:
            self.clients.add(client)
    
    def remove_client(self, client):
        with self.clients_lock:
            self.clients.discard(client)
    
    def get_client_count(self) -> int:
        with self.clients_lock:
            return len(self.clients)
    
    def run(self):
        """持续捕获屏幕"""
        frame_interval = 1.0 / self.fps
        
        with mss.mss() as sct:
            # 获取主显示器
            monitor = sct.monitors[1]  # 1 是主显示器
            
            while not self.stop_event.is_set():
                start_time = time.time()
                
                try:
                    # 捕获屏幕
                    screenshot = sct.grab(monitor)
                    
                    # 转换为 PIL Image
                    img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                    
                    # 缩放（如果需要）
                    if self.scale < 1.0:
                        new_size = (int(img.width * self.scale), int(img.height * self.scale))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # 压缩为 JPEG
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=self.quality, optimize=True)
                    frame_data = buffer.getvalue()
                    
                    # 更新最新帧
                    with self.frame_lock:
                        self.latest_frame = frame_data
                        self.frame_version += 1
                    
                    # 设置帧就绪事件
                    self.frame_ready.set()
                    
                except Exception as e:
                    print(f"[ScreenShare] 捕获错误: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 控制帧率
                elapsed = time.time() - start_time
                sleep_time = frame_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    def stop(self):
        self.stop_event.set()
        self.frame_ready.set()  # 唤醒等待的线程


class ScreenShareHandler(BaseHTTPRequestHandler):
    """屏幕共享 HTTP 处理器"""
    
    # 类变量 - 存储每个端口的捕获线程
    capture_threads: Dict[int, 'ScreenCaptureThread'] = {}
    
    def log_message(self, format, *args):
        """静默日志"""
        pass
    
    def get_capture_thread(self) -> Optional['ScreenCaptureThread']:
        """获取当前端口的捕获线程"""
        port = self.server.server_address[1]
        return self.capture_threads.get(port)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        print(f"[ScreenShare] 收到请求: {path}")
        
        if path == '/' or path == '':
            self.send_viewer_page()
        elif path == '/stream':
            self.send_mjpeg_stream()
        elif path == '/frame':
            self.send_single_frame()
        elif path == '/info':
            self.send_info()
        elif path == '/favicon.ico':
            self.send_favicon()
        else:
            self.send_error(404, "Not Found")
    
    def send_favicon(self):
        """发送 favicon"""
        # 简单的蓝色方块 favicon (16x16 ICO)
        # 使用 data URI 内嵌的 SVG 转 PNG 太复杂，直接返回空响应或简单图标
        self.send_response(204)  # No Content
        self.end_headers()
    
    def send_viewer_page(self):
        """发送观看页面"""
        html = get_viewer_page()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html)))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_mjpeg_stream(self):
        """发送 MJPEG 流"""
        capture_thread = self.get_capture_thread()
        if not capture_thread:
            print("[ScreenShare] No capture thread available")
            self.send_error(503, "Screen capture not available")
            return
        
        print(f"[ScreenShare] 客户端连接，开始发送 MJPEG 流")
        
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 注册客户端
        capture_thread.add_client(self)
        frame_count = 0
        last_version = -1  # 上次发送的帧版本
        
        try:
            while not capture_thread.stop_event.is_set():
                # 等待新帧
                capture_thread.frame_ready.wait(timeout=1.0)
                
                with capture_thread.frame_lock:
                    frame = capture_thread.latest_frame
                    current_version = capture_thread.frame_version
                
                # 只发送新帧
                if frame and current_version != last_version:
                    last_version = current_version
                    try:
                        self.wfile.write(b'--frame\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n')
                        self.wfile.write(f'Content-Length: {len(frame)}\r\n'.encode())
                        self.wfile.write(b'\r\n')
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                        self.wfile.flush()
                        frame_count += 1
                        if frame_count == 1:
                            print(f"[ScreenShare] 第一帧已发送，大小: {len(frame)} bytes")
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
                        print(f"[ScreenShare] 客户端断开: {e}")
                        break
                    except Exception as e:
                        print(f"[ScreenShare] 发送帧错误: {e}")
                        break
                else:
                    # 没有新帧，短暂等待避免 CPU 空转
                    time.sleep(0.01)
        finally:
            capture_thread.remove_client(self)
            print(f"[ScreenShare] 客户端断开，共发送 {frame_count} 帧")
    
    def send_single_frame(self):
        """发送单帧（用于首次加载或刷新）"""
        print("[ScreenShare] 请求单帧")
        capture_thread = self.get_capture_thread()
        if not capture_thread:
            print("[ScreenShare] 单帧请求失败: 没有捕获线程")
            self.send_error(503, "Screen capture not available")
            return
        
        # 等待帧可用
        print("[ScreenShare] 等待帧可用...")
        capture_thread.frame_ready.wait(timeout=2.0)
        
        with capture_thread.frame_lock:
            frame = capture_thread.latest_frame
        
        if frame:
            print(f"[ScreenShare] 发送单帧，大小: {len(frame)} bytes")
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(frame)))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(frame)
        else:
            print("[ScreenShare] 单帧请求失败: 没有可用帧")
            self.send_error(503, "No frame available")
        
        if frame:
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(frame)))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(frame)
        else:
            self.send_error(503, "No frame available")
    
    def send_info(self):
        """发送服务信息"""
        capture_thread = self.get_capture_thread()
        info = {
            'status': 'running' if capture_thread else 'stopped',
            'clients': capture_thread.get_client_count() if capture_thread else 0,
            'fps': capture_thread.fps if capture_thread else 0,
            'quality': capture_thread.quality if capture_thread else 0,
        }
        data = json.dumps(info).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)


class ThreadedScreenShareServer(HTTPServer):
    """支持多线程的屏幕共享服务器"""
    allow_reuse_address = True
    
    def process_request(self, request, client_address):
        thread = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        thread.daemon = True
        thread.start()
    
    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            pass
        finally:
            try:
                self.shutdown_request(request)
            except Exception:
                pass


def get_viewer_page() -> str:
    """获取屏幕共享观看页面"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>屏幕共享 - WebRPA</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect fill='%233b82f6' rx='4' width='24' height='24'/><path fill='white' d='M21,16H3V4H21M21,2H3C1.89,2 1,2.89 1,4V16A2,2 0 0,0 3,18H10V20H8V22H16V20H14V18H21A2,2 0 0,0 23,16V4C23,2.89 22.1,2 21,2Z'/></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: #000; 
            color: #fff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(24, 24, 27, 0.95);
            padding: 8px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #333;
            flex-shrink: 0;
            backdrop-filter: blur(10px);
        }
        .title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 12px;
            color: #a1a1aa;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse 2s infinite;
        }
        .status-dot.error { background: #ef4444; animation: none; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .controls {
            display: flex;
            gap: 8px;
        }
        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            background: #27272a;
            color: #fff;
            transition: background 0.2s;
        }
        .btn:hover { background: #3f3f46; }
        .btn:active { background: #52525b; }
        .viewer {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }
        #screen {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        .loading {
            position: absolute;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            color: #71717a;
        }
        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid #333;
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .fullscreen .header { display: none; }
        .fullscreen .viewer { height: 100vh; }
        .fullscreen #screen { max-height: 100vh; }
        .error-text { color: #ef4444; }
        @media (max-width: 640px) {
            .header { padding: 6px 12px; }
            .title { font-size: 13px; }
            .status { font-size: 11px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">
            <span>🖥️</span>
            <span>屏幕共享</span>
        </div>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">屏幕共享中...</span>
        </div>
        <div class="controls">
            <button class="btn" id="fullscreenBtn">全屏</button>
            <button class="btn" id="refreshBtn">刷新</button>
        </div>
    </div>
    <div class="viewer">
        <div class="loading" id="loading" style="display:none;">
            <div class="spinner"></div>
            <span>正在加载屏幕画面...</span>
        </div>
        <img id="screen1、更新一下教学文档，把当前项目的实际情况更新进去
2、确保所有模块的拼音模糊搜索和拼音首字母模糊搜索功能都完善好了
3、更新一下README文档中的内容，主要把模块总数更新一下
4、FrameworkHub需要更新吗？若需要更新一下！尤其是模块校验部分的功能，确保所有模块里面都有。" src="/stream" alt="屏幕共享">
    </div>
    <script>
        var screen = document.getElementById('screen');
        var loading = document.getElementById('loading');
        var statusText = document.getElementById('statusText');
        var statusDot = document.getElementById('statusDot');
        var fullscreenBtn = document.getElementById('fullscreenBtn');
        var refreshBtn = document.getElementById('refreshBtn');
        
        // 直接设置状态为已连接
        statusText.textContent = '实时共享中';
        statusDot.classList.remove('error');
        
        function doRefresh() {
            screen.src = '/stream?' + Date.now();
        }
        
        function toggleFullscreen() {
            var elem = document.documentElement;
            if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                if (elem.requestFullscreen) {
                    elem.requestFullscreen();
                } else if (elem.webkitRequestFullscreen) {
                    elem.webkitRequestFullscreen();
                }
                document.body.classList.add('fullscreen');
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                }
                document.body.classList.remove('fullscreen');
            }
        }
        
        fullscreenBtn.onclick = toggleFullscreen;
        refreshBtn.onclick = doRefresh;
        
        document.addEventListener('fullscreenchange', function() {
            if (!document.fullscreenElement) {
                document.body.classList.remove('fullscreen');
            }
        });
        document.addEventListener('webkitfullscreenchange', function() {
            if (!document.webkitFullscreenElement) {
                document.body.classList.remove('fullscreen');
            }
        });
    </script>
</body>
</html>'''


def start_screen_share(port: int = 9000, fps: int = 30, quality: int = 70, scale: float = 1.0) -> dict:
    """启动屏幕共享服务
    
    Args:
        port: 服务端口
        fps: 帧率 (1-60)
        quality: JPEG 质量 (10-100)
        scale: 缩放比例 (0.1-1.0)，降低可减少带宽
    
    Returns:
        包含 success, url, ip, port 等信息的字典
    """
    global _screen_share_servers
    
    # 如果已存在，先停止
    if port in _screen_share_servers:
        stop_screen_share(port)
    
    try:
        # 创建屏幕捕获线程
        capture_thread = ScreenCaptureThread(port, fps, quality, scale)
        
        # 注册到 Handler 的类变量中（按端口区分）
        ScreenShareHandler.capture_threads[port] = capture_thread
        
        # 创建 HTTP 服务器
        server = ThreadedScreenShareServer(('0.0.0.0', port), ScreenShareHandler)
        
        # 启动捕获线程
        capture_thread.start()
        
        # 等待第一帧准备好
        capture_thread.frame_ready.wait(timeout=3.0)
        
        # 启动服务器线程
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # 保存服务信息
        _screen_share_servers[port] = {
            'server': server,
            'server_thread': server_thread,
            'capture_thread': capture_thread,
            'fps': fps,
            'quality': quality,
            'scale': scale,
        }
        
        local_ip = get_local_ip()
        return {
            'success': True,
            'port': port,
            'ip': local_ip,
            'url': f'http://{local_ip}:{port}',
            'fps': fps,
            'quality': quality,
            'scale': scale,
        }
        
    except OSError as e:
        if 'Address already in use' in str(e) or '10048' in str(e):
            return {'success': False, 'error': f'端口 {port} 已被占用，请更换端口'}
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def stop_screen_share(port: int) -> dict:
    """停止屏幕共享服务"""
    global _screen_share_servers
    
    if port not in _screen_share_servers:
        return {'success': False, 'error': f'端口 {port} 没有运行屏幕共享服务'}
    
    try:
        info = _screen_share_servers[port]
        
        # 停止捕获线程
        capture_thread = info.get('capture_thread')
        if capture_thread:
            capture_thread.stop()
        
        # 停止服务器
        server = info.get('server')
        if server:
            server.shutdown()
        
        # 清理 Handler 类变量中的引用
        if port in ScreenShareHandler.capture_threads:
            del ScreenShareHandler.capture_threads[port]
        
        del _screen_share_servers[port]
        
        return {'success': True, 'message': f'屏幕共享服务已停止 (端口 {port})'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_screen_share_status(port: int) -> dict:
    """获取屏幕共享服务状态"""
    if port not in _screen_share_servers:
        return {'running': False}
    
    info = _screen_share_servers[port]
    capture_thread = info.get('capture_thread')
    
    return {
        'running': True,
        'port': port,
        'fps': info.get('fps', 0),
        'quality': info.get('quality', 0),
        'scale': info.get('scale', 1.0),
        'clients': capture_thread.get_client_count() if capture_thread else 0,
    }


def stop_all_screen_shares():
    """停止所有屏幕共享服务"""
    global _screen_share_servers
    ports = list(_screen_share_servers.keys())
    for port in ports:
        stop_screen_share(port)
