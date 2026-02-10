"""手机设置模块执行器 - 音量、亮度等系统设置"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager
from .type_utils import to_int


@register_executor
class PhoneSetVolumeExecutor(ModuleExecutor):
    """手机设置音量"""
    
    @property
    def module_type(self) -> str:
        return "phone_set_volume"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        volume = to_int(config.get('volume', 10), 10, context)
        stream_type = context.resolve_value(config.get('streamType', 'music'))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.set_volume(volume, stream_type, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            stream_names = {
                'music': '媒体',
                'ring': '铃声',
                'alarm': '闹钟',
                'notification': '通知',
                'system': '系统'
            }
            stream_name = stream_names.get(stream_type, stream_type)
            
            return ModuleResult(
                success=True,
                message=f"已设置{stream_name}音量为 {volume}/15"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"设置音量失败: {str(e)}")


@register_executor
class PhoneSetBrightnessExecutor(ModuleExecutor):
    """手机设置亮度"""
    
    @property
    def module_type(self) -> str:
        return "phone_set_brightness"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        brightness = to_int(config.get('brightness', 128), 128, context)
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.set_brightness(brightness, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            # 计算百分比
            percentage = round(brightness / 255 * 100)
            
            return ModuleResult(
                success=True,
                message=f"已设置屏幕亮度为 {brightness}/255 ({percentage}%)"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"设置亮度失败: {str(e)}")
