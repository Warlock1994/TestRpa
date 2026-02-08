"""
代理抓包服务 - 用于抓取模拟器/手机APP的HTTP请求
使用 mitmproxy 作为代理服务器
"""
import asyncio
import threading
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class CapturedRequest:
    """捕获的请求信息"""
    url: str
    method: str
    host: str
    path: str
    content_type: str
    timestamp: float
    size: int = 0


class ProxyCaptureService:
    """代理抓包服务"""
    
    _instance: Optional['ProxyCaptureService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.proxy_port = 8888
        self.is_running = False
        self.captured_requests: deque = deque(maxlen=1000)  # 最多保存1000条
        self._proxy_thread: Optional[threading.Thread] = None
        self._master = None
        self._stop_event = threading.Event()
    
    def start(self, port: int = 8888) -> bool:
        """启动代理服务"""
        if self.is_running:
            return True
        
        self.proxy_port = port
        self._stop_event.clear()
        self.captured_requests.clear()
        
        try:
            self._proxy_thread = threading.Thread(target=self._run_proxy, daemon=True)
            self._proxy_thread.start()
            
            # 等待代理启动
            time.sleep(1)
            self.is_running = True
            return True
        except Exception as e:
            print(f"[ProxyCapture] 启动失败: {e}")
            return False
    
    def stop(self):
        """停止代理服务"""
        if not self.is_running:
            return
        
        self._stop_event.set()
        if self._master:
            try:
                self._master.shutdown()
            except:
                pass
        
        self.is_running = False
        self._master = None
    
    def _run_proxy(self):
        """在独立线程中运行代理"""
        try:
            from mitmproxy import options
            from mitmproxy.tools.dump import DumpMaster
            from mitmproxy import http
            
            # 创建自定义 addon 来捕获请求
            service = self
            
            class CaptureAddon:
                def request(self, flow: http.HTTPFlow):
                    """捕获请求"""
                    req = flow.request
                    content_type = req.headers.get("content-type", "")
                    
                    captured = CapturedRequest(
                        url=req.pretty_url,
                        method=req.method,
                        host=req.host,
                        path=req.path,
                        content_type=content_type,
                        timestamp=time.time(),
                        size=len(req.content) if req.content else 0
                    )
                    service.captured_requests.append(captured)
                
                def response(self, flow: http.HTTPFlow):
                    """捕获响应（更新 content-type）"""
                    # 可以在这里更新响应的 content-type
                    pass
            
            # 配置 mitmproxy
            opts = options.Options(
                listen_host='0.0.0.0',
                listen_port=self.proxy_port,
                ssl_insecure=True,  # 忽略 SSL 证书错误
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self._master = DumpMaster(opts)
            self._master.addons.add(CaptureAddon())
            
            # 运行代理
            try:
                loop.run_until_complete(self._master.run())
            except:
                pass
            finally:
                loop.close()
                
        except ImportError:
            print("[ProxyCapture] mitmproxy 未安装，请运行: pip install mitmproxy")
        except Exception as e:
            print(f"[ProxyCapture] 代理运行异常: {e}")
    
    def get_captured_urls(self, keyword: str = "", filter_type: str = "all", 
                          since: float = 0) -> List[Dict]:
        """获取捕获的URL列表"""
        results = []
        
        for req in self.captured_requests:
            # 时间过滤
            if since > 0 and req.timestamp < since:
                continue
            
            url = req.url.lower()
            content_type = req.content_type.lower()
            
            # 类型过滤
            if filter_type == "m3u8":
                if ".m3u8" not in url and "application/vnd.apple.mpegurl" not in content_type:
                    continue
            elif filter_type == "media":
                media_exts = ['.m3u8', '.mp4', '.mp3', '.flv', '.ts', '.m4a', '.m4v', '.webm']
                media_types = ['video/', 'audio/', 'mpegurl']
                if not any(ext in url for ext in media_exts) and not any(t in content_type for t in media_types):
                    continue
            elif filter_type == "img":
                img_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
                if not any(ext in url for ext in img_exts) and 'image/' not in content_type:
                    continue
            
            # 关键词过滤
            if keyword and keyword.lower() not in url:
                continue
            
            results.append({
                "url": req.url,
                "method": req.method,
                "host": req.host,
                "path": req.path,
                "content_type": req.content_type,
                "timestamp": req.timestamp
            })
        
        return results
    
    def clear_captured(self):
        """清空捕获的请求"""
        self.captured_requests.clear()
    
    def get_status(self) -> Dict:
        """获取代理状态"""
        return {
            "running": self.is_running,
            "port": self.proxy_port,
            "captured_count": len(self.captured_requests)
        }


# 全局单例
proxy_capture_service = ProxyCaptureService()
