"""屏幕共享模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float


@register_executor
class StartScreenShareExecutor(ModuleExecutor):
    """开始屏幕共享模块执行器 - 启动局域网屏幕共享服务"""

    @property
    def module_type(self) -> str:
        return "start_screen_share"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.services.screen_share import start_screen_share, get_local_ip
        
        port = to_int(config.get("port", 9000), 9000, context)
        fps = to_int(config.get("fps", 30), 30, context)
        quality = to_int(config.get("quality", 70), 70, context)
        scale = to_float(config.get("scale", 1.0), 1.0, context)
        result_variable = config.get("resultVariable", "screen_share_url")
        
        # 参数范围限制
        fps = min(max(fps, 1), 60)
        quality = min(max(quality, 10), 100)
        scale = min(max(scale, 0.1), 1.0)
        
        try:
            result = start_screen_share(
                port=port,
                fps=fps,
                quality=quality,
                scale=scale
            )
            
            if not result['success']:
                return ModuleResult(success=False, error=result.get('error', '启动屏幕共享服务失败'))
            
            share_url = result['url']
            local_ip = result['ip']
            
            if result_variable:
                context.set_variable(result_variable, share_url)
            
            # 计算预估带宽
            estimated_bandwidth = self._estimate_bandwidth(fps, quality, scale)
            
            message = f"🖥️ 屏幕共享已启动！\n" \
                      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                      f"📡 访问地址: {share_url}\n" \
                      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                      f"⚙️ 参数设置:\n" \
                      f"   帧率: {fps} FPS\n" \
                      f"   画质: {quality}%\n" \
                      f"   缩放: {int(scale * 100)}%\n" \
                      f"   预估带宽: {estimated_bandwidth}\n" \
                      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                      f"💡 同局域网的设备可以使用浏览器访问上述地址\n" \
                      f"   实时观看此电脑的屏幕画面"
            
            return ModuleResult(
                success=True,
                message=message,
                data={
                    'url': share_url,
                    'ip': local_ip,
                    'port': port,
                    'fps': fps,
                    'quality': quality,
                    'scale': scale,
                }
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"启动屏幕共享失败: {str(e)}")
    
    def _estimate_bandwidth(self, fps: int, quality: int, scale: float) -> str:
        """估算带宽需求"""
        # 假设 1080p 全质量单帧约 200KB
        base_size = 200 * 1024  # bytes
        
        # 根据质量调整
        size_per_frame = base_size * (quality / 100) * (scale ** 2)
        
        # 计算每秒数据量
        bytes_per_second = size_per_frame * fps
        
        # 转换为 Mbps
        mbps = (bytes_per_second * 8) / (1024 * 1024)
        
        if mbps < 1:
            return f"{int(mbps * 1000)} Kbps"
        else:
            return f"{mbps:.1f} Mbps"


@register_executor
class StopScreenShareExecutor(ModuleExecutor):
    """停止屏幕共享模块执行器"""

    @property
    def module_type(self) -> str:
        return "stop_screen_share"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.services.screen_share import stop_screen_share
        
        port = to_int(config.get("port", 9000), 9000, context)
        
        try:
            result = stop_screen_share(port)
            
            if not result['success']:
                return ModuleResult(success=False, error=result.get('error', '停止屏幕共享服务失败'))
            
            return ModuleResult(
                success=True,
                message=f"🖥️ 屏幕共享已停止 (端口 {port})",
                data={'port': port}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"停止屏幕共享失败: {str(e)}")
