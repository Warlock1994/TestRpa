"""手机输入模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneInputTextExecutor(ModuleExecutor):
    """手机输入文本"""
    
    @property
    def module_type(self) -> str:
        return "phone_input_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        text = context.resolve_value(config.get('text', ''))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.input_text(text, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已输入文本")
        except Exception as e:
            return ModuleResult(success=False, error=f"输入文本失败: {str(e)}")


@register_executor
class PhonePressKeyExecutor(ModuleExecutor):
    """手机按键"""
    
    @property
    def module_type(self) -> str:
        return "phone_press_key"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        # 兼容旧的 'key' 字段和新的 'keycode' 字段
        keycode = config.get('keycode') or config.get('key')
        if not keycode:
            keycode = 'KEYCODE_HOME'
        
        keycode = context.resolve_value(keycode)
        
        # 如果 keycode 不是以 KEYCODE_ 开头，自动添加前缀（兼容旧格式）
        if keycode and not keycode.startswith('KEYCODE_'):
            keycode = f'KEYCODE_{keycode}'
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.press_key(keycode, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已按下 {keycode}")
        except Exception as e:
            return ModuleResult(success=False, error=f"按键失败: {str(e)}")
