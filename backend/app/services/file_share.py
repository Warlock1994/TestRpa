"""文件网络共享服务 - 提供局域网文件共享功能"""
import asyncio
import os
import socket
import threading
import mimetypes
import shutil
import subprocess
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote, unquote, urlparse
import json
import html


# 视频缩略图缓存目录
_thumb_cache_dir: Optional[Path] = None

def get_thumb_cache_dir() -> Path:
    """获取缩略图缓存目录"""
    global _thumb_cache_dir
    if _thumb_cache_dir is None:
        _thumb_cache_dir = Path(tempfile.gettempdir()) / "webrpa_video_thumbs"
        _thumb_cache_dir.mkdir(exist_ok=True)
    return _thumb_cache_dir


def generate_video_thumbnail(video_path: Path) -> Optional[Path]:
    """使用 ffmpeg 生成视频缩略图"""
    try:
        # 生成缓存文件名
        file_hash = hashlib.md5(str(video_path).encode()).hexdigest()
        mtime = int(video_path.stat().st_mtime)
        thumb_name = f"{file_hash}_{mtime}.jpg"
        thumb_path = get_thumb_cache_dir() / thumb_name
        
        # 如果缓存存在，直接返回
        if thumb_path.exists():
            return thumb_path
        
        # 查找 ffmpeg
        ffmpeg_path = "ffmpeg"
        # 检查 backend 目录是否有 ffmpeg.exe
        backend_ffmpeg = Path(__file__).resolve().parent.parent.parent / "ffmpeg.exe"
        if backend_ffmpeg.exists():
            ffmpeg_path = str(backend_ffmpeg)
        
        # 使用 ffmpeg 生成缩略图
        cmd = [
            ffmpeg_path,
            "-i", str(video_path),
            "-ss", "00:00:01",  # 跳到1秒位置
            "-vframes", "1",
            "-vf", "scale=96:96:force_original_aspect_ratio=increase,crop=96:96",
            "-y",
            str(thumb_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if thumb_path.exists():
            return thumb_path
        return None
    except Exception:
        return None


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


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class FileShareHandler(SimpleHTTPRequestHandler):
    """自定义文件共享处理器"""
    
    # 类变量，用于存储共享配置
    share_config: Dict[str, Any] = {}
    allow_write: bool = True
    
    def __init__(self, *args, **kwargs):
        # 设置共享目录
        self.share_path = self.share_config.get('path', '.')
        self.share_type = self.share_config.get('type', 'folder')  # folder 或 file
        self.share_name = self.share_config.get('name', '共享')
        super().__init__(*args, directory=self.share_path if self.share_type == 'folder' else str(Path(self.share_path).parent), **kwargs)
    
    def log_message(self, format, *args):
        """静默日志"""
        pass
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求（上传文件、创建文件夹）"""
        path = unquote(self.path)
        
        if not self.allow_write:
            self._send_json({'success': False, 'error': '此共享不允许写操作'}, 403)
            return
        
        if path == '/api/upload':
            self._handle_upload()
        elif path == '/api/mkdir':
            self._handle_mkdir()
        else:
            self.send_error(404, "Not found")
    
    def do_DELETE(self):
        """处理 DELETE 请求（删除文件/文件夹）"""
        path = unquote(self.path)
        
        if not self.allow_write:
            self._send_json({'success': False, 'error': '此共享不允许写操作'}, 403)
            return
        
        if path.startswith('/api/delete/'):
            file_path = path[12:]
            self._handle_delete(file_path)
        else:
            self.send_error(404, "Not found")
    
    def _send_json(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def _handle_upload(self):
        """处理文件上传"""
        try:
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            
            if 'multipart/form-data' not in content_type:
                self._send_json({'success': False, 'error': '无效的 Content-Type'}, 400)
                return
            
            # 解析 boundary
            boundary = None
            for part in content_type.split(';'):
                part = part.strip()
                if part.startswith('boundary='):
                    boundary = part[9:].strip('"')
                    break
            
            if not boundary:
                self._send_json({'success': False, 'error': '无法解析 boundary'}, 400)
                return
            
            # 读取请求体
            body = self.rfile.read(content_length)
            boundary_bytes = ('--' + boundary).encode()
            parts = body.split(boundary_bytes)
            
            upload_path = '/'
            uploaded_files = []
            
            for part in parts:
                if not part or part == b'--\r\n' or part == b'--':
                    continue
                
                if b'\r\n\r\n' not in part:
                    continue
                
                header_end = part.index(b'\r\n\r\n')
                headers_raw = part[:header_end].decode('utf-8', errors='ignore')
                content = part[header_end + 4:]
                
                if content.endswith(b'\r\n'):
                    content = content[:-2]
                
                # 解析 Content-Disposition
                filename = None
                field_name = None
                
                for line in headers_raw.split('\r\n'):
                    if line.lower().startswith('content-disposition:'):
                        for item in line.split(';'):
                            item = item.strip()
                            if item.startswith('name="'):
                                field_name = item[6:-1]
                            elif item.startswith('filename="'):
                                filename = item[10:-1]
                
                if field_name == 'path':
                    upload_path = content.decode('utf-8')
                elif field_name == 'file' and filename:
                    # 保存文件
                    base_path = Path(self.share_path)
                    target_dir = base_path / upload_path.lstrip('/')
                    
                    # 安全检查
                    try:
                        target_dir.resolve().relative_to(base_path.resolve())
                    except ValueError:
                        self._send_json({'success': False, 'error': '无效的上传路径'}, 400)
                        return
                    
                    if not target_dir.exists():
                        target_dir.mkdir(parents=True, exist_ok=True)
                    
                    file_path = target_dir / filename
                    
                    # 如果文件已存在，添加数字后缀
                    if file_path.exists():
                        base = file_path.stem
                        ext = file_path.suffix
                        counter = 1
                        while file_path.exists():
                            file_path = target_dir / f"{base}_{counter}{ext}"
                            counter += 1
                    
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    uploaded_files.append(filename)
            
            if uploaded_files:
                self._send_json({
                    'success': True,
                    'message': f'成功上传 {len(uploaded_files)} 个文件',
                    'files': uploaded_files
                })
            else:
                self._send_json({'success': False, 'error': '没有找到要上传的文件'}, 400)
                
        except Exception as e:
            self._send_json({'success': False, 'error': f'上传失败: {str(e)}'}, 500)
    
    def _handle_mkdir(self):
        """处理创建文件夹"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            parent_path = data.get('path', '/')
            folder_name = data.get('name', '')
            
            if not folder_name:
                self._send_json({'success': False, 'error': '文件夹名称不能为空'}, 400)
                return
            
            # 检查文件夹名称是否合法
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                if char in folder_name:
                    self._send_json({'success': False, 'error': f'文件夹名称不能包含字符: {char}'}, 400)
                    return
            
            base_path = Path(self.share_path)
            target_dir = base_path / parent_path.lstrip('/')
            
            # 安全检查
            try:
                target_dir.resolve().relative_to(base_path.resolve())
            except ValueError:
                self._send_json({'success': False, 'error': '无效的路径'}, 400)
                return
            
            new_folder = target_dir / folder_name
            
            if new_folder.exists():
                self._send_json({'success': False, 'error': '文件夹已存在'}, 400)
                return
            
            new_folder.mkdir(parents=True, exist_ok=True)
            
            self._send_json({
                'success': True,
                'message': f'文件夹 "{folder_name}" 创建成功'
            })
            
        except json.JSONDecodeError:
            self._send_json({'success': False, 'error': '无效的 JSON 数据'}, 400)
        except Exception as e:
            self._send_json({'success': False, 'error': f'创建文件夹失败: {str(e)}'}, 500)
    
    def _handle_delete(self, file_path: str):
        """处理删除文件/文件夹"""
        import shutil
        
        try:
            base_path = Path(self.share_path)
            target_path = base_path / file_path
            
            # 安全检查
            try:
                target_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                self._send_json({'success': False, 'error': '无效的路径'}, 400)
                return
            
            if not target_path.exists():
                self._send_json({'success': False, 'error': '文件或文件夹不存在'}, 404)
                return
            
            # 不允许删除根目录
            if target_path.resolve() == base_path.resolve():
                self._send_json({'success': False, 'error': '不能删除根目录'}, 400)
                return
            
            if target_path.is_file():
                target_path.unlink()
                self._send_json({
                    'success': True,
                    'message': f'文件 "{target_path.name}" 已删除'
                })
            else:
                shutil.rmtree(target_path)
                self._send_json({
                    'success': True,
                    'message': f'文件夹 "{target_path.name}" 已删除'
                })
                
        except PermissionError:
            self._send_json({'success': False, 'error': '没有权限删除此文件/文件夹'}, 403)
        except Exception as e:
            self._send_json({'success': False, 'error': f'删除失败: {str(e)}'}, 500)
    
    def do_GET(self):
        """处理GET请求"""
        # 解码URL路径
        path = unquote(self.path)
        
        # 如果是单文件共享
        if self.share_type == 'file':
            file_path = Path(self.share_config.get('path', ''))
            if path == '/' or path == '':
                # 返回文件下载页面
                self.send_file_download_page(file_path)
                return
            elif path == '/download' or path.endswith('/' + file_path.name):
                # 直接下载文件
                self.send_file(file_path)
                return
            else:
                self.send_error(404, "File not found")
                return
        
        # 文件夹共享
        if path == '/api/list' or path == '/api/list/':
            # API: 获取文件列表（根目录）
            self.send_file_list('/')
            return
        elif path.startswith('/api/list/'):
            # API: 获取子目录文件列表
            sub_path = path[10:]  # 移除 '/api/list/'
            if not sub_path or sub_path == '/':
                self.send_file_list('/')
            else:
                self.send_file_list(sub_path)
            return
        elif path.startswith('/thumb/'):
            # 视频缩略图
            file_path = path[7:]  # 移除 '/thumb/'
            self.send_video_thumbnail(file_path)
            return
        elif path.startswith('/download/'):
            # 下载文件
            file_path = path[10:]  # 移除 '/download/'
            self.send_file_download(file_path)
            return
        elif path.startswith('/preview/'):
            # 文档预览（Excel、Word、PPT）
            file_path = path[9:]  # 移除 '/preview/'
            self.send_document_preview(file_path)
            return
        elif path == '/' or path == '':
            # 返回文件浏览器页面
            self.send_browser_page()
            return
        else:
            # 尝试作为静态文件处理
            super().do_GET()
    
    def send_video_thumbnail(self, file_path: str):
        """发送视频缩略图"""
        try:
            base_path = Path(self.share_path)
            target_path = base_path / file_path
            
            # 安全检查
            try:
                target_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                self.send_error(403, "Access denied")
                return
            
            if not target_path.exists() or not target_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # 生成缩略图
            thumb_path = generate_video_thumbnail(target_path)
            if thumb_path and thumb_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(thumb_path.stat().st_size))
                self.send_header('Cache-Control', 'max-age=86400')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(thumb_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                # 返回空的透明图片或404
                self.send_error(404, "Thumbnail not available")
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception:
            self.send_error(500, "Internal Server Error")
    
    def send_file_list(self, sub_path: str):
        """发送文件列表JSON"""
        try:
            base_path = Path(self.share_path)
            target_path = base_path / sub_path.lstrip('/')
            
            # 安全检查：确保路径在共享目录内
            try:
                target_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                self.send_error(403, "Access denied")
                return
            
            if not target_path.exists():
                self.send_error(404, "Directory not found")
                return
            
            if not target_path.is_dir():
                self.send_error(400, "Not a directory")
                return
            
            items = []
            for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                try:
                    stat = item.stat()
                    items.append({
                        'name': item.name,
                        'type': 'folder' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else 0,
                        'modified': stat.st_mtime,
                        'path': str(item.relative_to(base_path)).replace('\\', '/')
                    })
                except (PermissionError, OSError):
                    continue
            
            response = json.dumps({
                'success': True,
                'path': sub_path,
                'items': items,
                'shareName': self.share_name
            }, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            # 客户端断开连接，静默处理
            pass
        except Exception as e:
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass
    
    def send_file_download(self, file_path: str):
        """发送文件下载（用于预览，不强制下载）"""
        try:
            base_path = Path(self.share_path)
            target_path = base_path / file_path
            
            # 安全检查
            try:
                target_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                self.send_error(403, "Access denied")
                return
            
            if not target_path.exists() or not target_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # 预览时不强制下载
            self.send_file(target_path, force_download=False)
            
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            # 客户端断开连接，静默处理
            pass
        except Exception as e:
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass
    
    def send_document_preview(self, file_path: str):
        """发送文档预览（Excel、Word、PPT）"""
        try:
            base_path = Path(self.share_path)
            target_path = base_path / file_path
            
            # 安全检查
            try:
                target_path.resolve().relative_to(base_path.resolve())
            except ValueError:
                self.send_error(403, "Access denied")
                return
            
            if not target_path.exists() or not target_path.is_file():
                self.send_error(404, "File not found")
                return
            
            # 导入文档预览服务
            from .file_preview import get_preview_content
            
            result = get_preview_content(target_path)
            if result:
                content_bytes, content_type = result
                self.send_response(200)
                self.send_header('Content-Type', f'{content_type}; charset=utf-8')
                self.send_header('Content-Length', str(len(content_bytes)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content_bytes)
            else:
                # 不支持的文件类型，返回提示
                error_html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>不支持预览</title>
<style>body{{font-family:sans-serif;background:#18181b;color:#fafafa;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;}}
.msg{{text-align:center;padding:40px;}}.msg h2{{margin-bottom:16px;}}</style></head>
<body><div class="msg"><h2>📄 {html.escape(target_path.name)}</h2><p>此文件类型暂不支持在线预览</p></div></body></html>'''
                content = error_html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass
        except Exception as e:
            try:
                error_html = f'<html><body><h1>预览失败</h1><p>{html.escape(str(e))}</p></body></html>'
                content = error_html.encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                pass
    
    def send_file(self, file_path: Path, force_download: bool = True):
        """发送文件"""
        try:
            file_size = file_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # 检查是否是 Range 请求（用于视频流）
            range_header = self.headers.get('Range')
            if range_header and range_header.startswith('bytes='):
                # 处理 Range 请求
                range_spec = range_header[6:]
                start, end = 0, file_size - 1
                if '-' in range_spec:
                    parts = range_spec.split('-')
                    if parts[0]:
                        start = int(parts[0])
                    if parts[1]:
                        end = int(parts[1])
                
                if start >= file_size:
                    self.send_error(416, "Range Not Satisfiable")
                    return
                
                end = min(end, file_size - 1)
                content_length = end - start + 1
                
                self.send_response(206)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(content_length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                            return
            else:
                # 普通请求
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                if force_download:
                    self.send_header('Content-Disposition', f'attachment; filename="{quote(file_path.name)}"')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                            return
                    
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            # 客户端断开连接，静默处理
            pass
        except Exception as e:
            try:
                self.send_error(500, "Internal Server Error")
            except Exception:
                pass
    
    def send_file_download_page(self, file_path: Path):
        """发送单文件下载页面"""
        file_size = file_path.stat().st_size
        size_str = format_size(file_size)
        
        html_content = get_single_file_page(file_path.name, size_str)
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def send_browser_page(self):
        """发送文件浏览器页面"""
        html_content = get_browser_page(self.share_name, self.share_config.get('allow_write', True))
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


def get_single_file_page(filename: str, size: str) -> str:
    """获取单文件下载页面HTML - 使用新模板"""
    from .file_share_page import get_single_file_page as _get_single_file_page
    return _get_single_file_page(filename, size)


def get_browser_page(share_name: str, allow_write: bool = True) -> str:
    """获取文件浏览器页面HTML - 使用新模板"""
    from .file_share_page import get_browser_page as _get_browser_page
    return _get_browser_page(share_name, allow_write)


# 全局共享服务管理
_share_servers: Dict[int, tuple] = {}  # port -> (server, thread, config)


class ThreadedHTTPServer(HTTPServer):
    """支持多线程的 HTTP 服务器，允许多个客户端同时访问"""
    allow_reuse_address = True
    
    def process_request(self, request, client_address):
        """为每个请求创建新线程"""
        thread = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        thread.daemon = True
        thread.start()
    
    def process_request_thread(self, request, client_address):
        """在线程中处理请求"""
        try:
            self.finish_request(request, client_address)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            # 客户端断开连接，静默处理
            pass
        except Exception:
            try:
                self.handle_error(request, client_address)
            except Exception:
                pass
        finally:
            try:
                self.shutdown_request(request)
            except Exception:
                pass


def start_file_share(path: str, port: int, share_type: str = 'folder', name: str = '共享', allow_write: bool = True) -> dict:
    """启动文件共享服务"""
    global _share_servers
    
    if port in _share_servers:
        stop_file_share(port)
    
    path_obj = Path(path)
    if not path_obj.exists():
        return {'success': False, 'error': f'路径不存在: {path}'}
    
    if share_type == 'file' and not path_obj.is_file():
        return {'success': False, 'error': f'不是文件: {path}'}
    
    if share_type == 'folder' and not path_obj.is_dir():
        return {'success': False, 'error': f'不是文件夹: {path}'}
    
    try:
        config = {
            'path': str(path_obj.resolve()),
            'type': share_type,
            'name': name,
            'allow_write': allow_write
        }
        
        FileShareHandler.share_config = config
        FileShareHandler.allow_write = allow_write
        
        # 使用多线程服务器，支持多个客户端同时访问
        server = ThreadedHTTPServer(('0.0.0.0', port), FileShareHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        
        _share_servers[port] = (server, thread, config)
        
        local_ip = get_local_ip()
        return {
            'success': True,
            'port': port,
            'ip': local_ip,
            'url': f'http://{local_ip}:{port}',
            'message': f'共享服务已启动，同局域网设备可访问: http://{local_ip}:{port}'
        }
        
    except OSError as e:
        if 'Address already in use' in str(e) or '10048' in str(e):
            return {'success': False, 'error': f'端口 {port} 已被占用，请更换端口'}
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def stop_file_share(port: int) -> dict:
    """停止文件共享服务"""
    global _share_servers
    
    if port not in _share_servers:
        return {'success': False, 'error': f'端口 {port} 没有运行共享服务'}
    
    try:
        server, thread, config = _share_servers[port]
        server.shutdown()
        del _share_servers[port]
        return {'success': True, 'message': f'端口 {port} 的共享服务已停止'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_active_shares() -> list:
    """获取所有活动的共享服务"""
    return [{'port': port, 'config': config} for port, (_, _, config) in _share_servers.items()]
