"""高级模块执行器 - advanced_network"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
import asyncio
import re
import time


@register_executor
class NetworkCaptureExecutor(ModuleExecutor):
    """网络抓包模块执行器 - 支持浏览器抓包、系统抓包和代理抓包"""

    @property
    def module_type(self) -> str:
        return "network_capture"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        capture_mode = context.resolve_value(config.get("captureMode", "browser"))  # browser, system, proxy
        filter_type = context.resolve_value(config.get("filterType", "all"))  # all, img, media, m3u8
        search_keyword = context.resolve_value(config.get("searchKeyword", ""))
        capture_duration = to_int(config.get("captureDuration", 5000), 5000, context)  # 毫秒
        variable_name = config.get("variableName", "")
        
        # 全局抓包特有参数
        target_process = context.resolve_value(config.get("targetProcess", ""))  # 目标进程名
        target_ports = context.resolve_value(config.get("targetPorts", ""))  # 目标端口，逗号分隔
        
        # 代理抓包特有参数
        proxy_port = to_int(config.get("proxyPort", 8888), 8888, context)

        if not variable_name:
            return ModuleResult(success=False, error="请指定存储变量名")

        try:
            if capture_mode == "proxy":
                # 代理抓包模式（用于模拟器/手机APP）
                return await self._capture_proxy(
                    context, variable_name, capture_duration,
                    filter_type, search_keyword, proxy_port
                )
            elif capture_mode == "system":
                # 全局系统抓包模式
                return await self._capture_system(
                    context, variable_name, capture_duration, 
                    search_keyword, target_process, target_ports
                )
            else:
                # 浏览器抓包模式
                return await self._capture_browser(
                    context, variable_name, capture_duration,
                    filter_type, search_keyword
                )

        except Exception as e:
            return ModuleResult(success=False, error=f"网络抓包启动失败: {str(e)}")
    
    async def _capture_proxy(self, context: 'ExecutionContext', variable_name: str,
                              capture_duration: int, filter_type: str, 
                              search_keyword: str, proxy_port: int) -> ModuleResult:
        """代理抓包模式 - 用于抓取模拟器/手机APP的HTTP请求"""
        from ..services.proxy_capture import proxy_capture_service
        from ..services.file_share import get_local_ip
        
        local_ip = get_local_ip()
        
        # 启动代理服务（如果未启动）
        if not proxy_capture_service.is_running:
            if not proxy_capture_service.start(proxy_port):
                return ModuleResult(
                    success=False, 
                    error="代理服务启动失败，请确保已安装 mitmproxy: pip install mitmproxy"
                )
        
        # 记录开始时间
        start_time = asyncio.get_event_loop().time()
        capture_start = asyncio.get_event_loop().time()
        
        # 清空之前的捕获（可选，这里选择不清空以便累积）
        # proxy_capture_service.clear_captured()
        
        # 等待抓包时间
        await asyncio.sleep(capture_duration / 1000)
        
        # 获取捕获的URL
        captured = proxy_capture_service.get_captured_urls(
            keyword=search_keyword,
            filter_type=filter_type,
            since=capture_start
        )
        
        # 提取URL列表
        urls = [item["url"] for item in captured]
        unique_urls = list(dict.fromkeys(urls))  # 去重保持顺序
        
        context.set_variable(variable_name, unique_urls)
        
        filter_desc = filter_type if filter_type != "all" else "全部"
        if search_keyword:
            filter_desc += f"，关键词={search_keyword}"
        
        return ModuleResult(
            success=True,
            message=f"代理抓包完成，捕获到 {len(unique_urls)} 个URL（过滤: {filter_desc}），已存入变量 {{{variable_name}}}。代理地址: {local_ip}:{proxy_port}",
            data={
                "status": "completed", 
                "mode": "proxy",
                "count": len(unique_urls), 
                "urls": unique_urls[:20],
                "proxy_ip": local_ip,
                "proxy_port": proxy_port
            }
        )
    
    async def _capture_browser(self, context: 'ExecutionContext', variable_name: str, 
                                capture_duration: int, filter_type: str, search_keyword: str) -> ModuleResult:
        """浏览器抓包模式 - 使用 Playwright 监听页面请求"""
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面，浏览器抓包需要先打开网页")

        await context.switch_to_latest_page()
        
        # 存储捕获到的请求URL
        captured_urls = []
        
        # 定义资源类型过滤
        def should_capture(request) -> bool:
            url = request.url
            resource_type = request.resource_type
            
            # 根据过滤类型筛选
            if filter_type == "img":
                if resource_type not in ["image"]:
                    return False
            elif filter_type == "media":
                if resource_type not in ["media", "video", "audio"]:
                    return False
            # all 类型不过滤
            
            # 模糊搜索筛选
            if search_keyword:
                if search_keyword.lower() not in url.lower():
                    return False
            
            return True
        
        # 请求处理函数
        def on_request(request):
            if should_capture(request):
                captured_urls.append(request.url)
        
        # 注册请求监听器
        context.page.on("request", on_request)
        
        # 等待抓包时间（阻塞）
        await asyncio.sleep(capture_duration / 1000)
        
        # 移除监听器
        context.page.remove_listener("request", on_request)
        
        # 去重并存储结果
        unique_urls = list(dict.fromkeys(captured_urls))
        context.set_variable(variable_name, unique_urls)
        
        return ModuleResult(
            success=True,
            message=f"浏览器抓包完成，捕获到 {len(unique_urls)} 个URL，已存入变量 {{{variable_name}}}",
            data={"status": "completed", "mode": "browser", "count": len(unique_urls), "urls": unique_urls[:10]}
        )
    
    async def _capture_system(self, context: 'ExecutionContext', variable_name: str,
                               capture_duration: int, search_keyword: str,
                               target_process: str, target_ports: str) -> ModuleResult:
        """全局系统抓包模式 - 监控系统网络连接"""
        import psutil
        
        # 解析目标端口
        port_filter = set()
        if target_ports:
            for p in target_ports.replace('，', ',').split(','):
                p = p.strip()
                if p.isdigit():
                    port_filter.add(int(p))
        
        # 存储捕获到的连接信息
        captured_connections = []
        seen_connections = set()  # 用于去重
        
        def get_process_name(pid: int) -> str:
            """获取进程名"""
            try:
                proc = psutil.Process(pid)
                return proc.name()
            except:
                return ""
        
        def capture_connections():
            """捕获当前网络连接"""
            try:
                connections = psutil.net_connections(kind='inet')
                for conn in connections:
                    # 只关注已建立的连接
                    if conn.status != 'ESTABLISHED':
                        continue
                    
                    # 获取远程地址
                    if not conn.raddr:
                        continue
                    
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    local_port = conn.laddr.port if conn.laddr else 0
                    pid = conn.pid or 0
                    
                    # 端口过滤
                    if port_filter:
                        if remote_port not in port_filter and local_port not in port_filter:
                            continue
                    
                    # 进程过滤
                    proc_name = get_process_name(pid) if pid else ""
                    if target_process:
                        if target_process.lower() not in proc_name.lower():
                            continue
                    
                    # 构建连接标识用于去重
                    conn_key = f"{remote_ip}:{remote_port}:{pid}"
                    if conn_key in seen_connections:
                        continue
                    seen_connections.add(conn_key)
                    
                    # 构建连接信息
                    conn_info = {
                        "remote_ip": remote_ip,
                        "remote_port": remote_port,
                        "local_port": local_port,
                        "pid": pid,
                        "process": proc_name,
                        "address": f"{remote_ip}:{remote_port}"
                    }
                    
                    # 关键词过滤
                    if search_keyword:
                        search_str = f"{remote_ip}:{remote_port} {proc_name}".lower()
                        if search_keyword.lower() not in search_str:
                            continue
                    
                    captured_connections.append(conn_info)
            except Exception as e:
                print(f"[DEBUG] 捕获连接异常: {e}")
        
        # 创建异步任务来持续抓包
        async def capture_task():
            import time
            start_time = time.time()
            duration_sec = capture_duration / 1000
            
            while time.time() - start_time < duration_sec:
                # 在线程池中执行连接捕获
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, capture_connections)
                await asyncio.sleep(0.5)  # 每500ms扫描一次
            
            # 存储结果
            context.set_variable(variable_name, captured_connections)
        
        # 等待抓包完成（阻塞）
        await capture_task()
        
        filter_desc = []
        if target_process:
            filter_desc.append(f"进程={target_process}")
        if target_ports:
            filter_desc.append(f"端口={target_ports}")
        if search_keyword:
            filter_desc.append(f"关键词={search_keyword}")
        filter_str = "，".join(filter_desc) if filter_desc else "无"
        
        return ModuleResult(
            success=True,
            message=f"全局抓包完成，过滤条件: {filter_str}，捕获到 {len(captured_connections)} 个连接，已存入变量 {{{variable_name}}}",
            data={"status": "completed", "mode": "system", "count": len(captured_connections), "connections": captured_connections[:10]}
        )