"""文件共享HTTP请求处理器"""
import os
import json
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from .file_share_utils import format_size


class FileShareHandler(BaseHTTPRequestHandler):
    """文件共享HTTP请求处理器"""
    share_config = {}
    allow_write = True
    
    def log_message(self, format, *args):
        """禁用默认日志"""
        pass
    
    def do_GET(self):
        """处理GET请求"""
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        
        if path == '/' or path == '':
            self._serve_index()
        elif path.startswith('/download/'):
            self._serve_file(path[10:])
        elif path.startswith('/preview/'):
            self._serve_preview(path[9:])
        elif path == '/api/files':
            self._serve_file_list()
        else:
            self._send_404()
    
    def do_POST(self):
        """处理POST请求"""
        if not self.allow_write:
            self._send_json({'error': '不允许写操作'}, 403)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/upload':
            self._handle_upload()
        elif parsed.path == '/api/delete':
            self._handle_delete()
        else:
            self._send_404()
    
    def _serve_index(self):
        """返回主页"""
        html = self._generate_index_html()
        self._send_html(html)
    
    def _serve_file_list(self):
        """返回文件列表JSON"""
        config = self.share_config
        if config.get('type') == 'file':
            path = Path(config['path'])
            files = [{
                'name': path.name,
                'size': path.stat().st_size,
                'size_str': format_size(path.stat().st_size),
                'is_dir': False,
                'path': path.name
            }]
        else:
            base_path = Path(config['path'])
            files = []
            for item in base_path.iterdir():
                stat = item.stat()
                files.append({
                    'name': item.name,
                    'size': stat.st_size if item.is_file() else 0,
                    'size_str': format_size(stat.st_size) if item.is_file() else '-',
                    'is_dir': item.is_dir(),
                    'path': item.name
                })
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        self._send_json({'files': files, 'name': config.get('name', '共享')})
    
    def _serve_file(self, file_path: str):
        """提供文件下载"""
        config = self.share_config
        if config.get('type') == 'file':
            full_path = Path(config['path'])
        else:
            full_path = Path(config['path']) / file_path
        
        if not full_path.exists() or not full_path.is_file():
            self._send_404()
            return
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{full_path.name}"')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _serve_preview(self, file_path: str):
        """提供文件预览"""
        config = self.share_config
        if config.get('type') == 'file':
            full_path = Path(config['path'])
        else:
            full_path = Path(config['path']) / file_path
        
        if not full_path.exists() or not full_path.is_file():
            self._send_404()
            return
        
        ext = full_path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain', '.html': 'text/html', '.css': 'text/css',
            '.js': 'application/javascript', '.json': 'application/json',
            '.xml': 'application/xml', '.py': 'text/plain', '.md': 'text/plain',
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
            '.mp4': 'video/mp4', '.webm': 'video/webm', '.ogg': 'video/ogg',
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.flac': 'audio/flac',
            '.pdf': 'application/pdf',
        }
        
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_upload(self):
        """处理文件上传"""
        # 简化实现
        self._send_json({'error': '上传功能暂未实现'}, 501)
    
    def _handle_delete(self):
        """处理文件删除"""
        # 简化实现
        self._send_json({'error': '删除功能暂未实现'}, 501)
    
    def _generate_index_html(self):
        """生成主页HTML"""
        config = self.share_config
        return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{config.get('name', '文件共享')}</title>
<style>body{{font-family:sans-serif;margin:20px}}table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}a{{color:#0066cc;text-decoration:none}}</style>
</head><body><h1>{config.get('name', '文件共享')}</h1><div id="files"></div>
<script>
fetch('/api/files').then(r=>r.json()).then(data=>{{
  let html='<table><tr><th>名称</th><th>大小</th><th>操作</th></tr>';
  data.files.forEach(f=>{{
    html+=`<tr><td>${{f.name}}</td><td>${{f.size_str}}</td>
    <td><a href="/download/${{f.path}}">下载</a> | <a href="/preview/${{f.path}}" target="_blank">预览</a></td></tr>`;
  }});
  html+='</table>';
  document.getElementById('files').innerHTML=html;
}});
</script></body></html>'''
    
    def _send_html(self, html: str, status: int = 200):
        """发送HTML响应"""
        content = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def _send_json(self, data: dict, status: int = 200):
        """发送JSON响应"""
        content = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def _send_404(self):
        """发送404响应"""
        self._send_html('<h1>404 Not Found</h1>', 404)
