"""手机触摸操作模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneTapExecutor(ModuleExecutor):
    """手机点击坐标"""
    
    @property
    def module_type(self) -> str:
        return "phone_tap"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        x = to_int(config.get('x', 0), 0, context)
        y = to_int(config.get('y', 0), 0, context)
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.tap(x, y, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已点击坐标 ({x}, {y})")
        except Exception as e:
            return ModuleResult(success=False, error=f"点击失败: {str(e)}")


@register_executor
class PhoneSwipeExecutor(ModuleExecutor):
    """手机滑动"""
    
    @property
    def module_type(self) -> str:
        return "phone_swipe"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        swipe_mode = config.get('swipeMode', 'coordinate')  # coordinate 或 offset
        x1 = to_int(config.get('x1', 0), 0, context)
        y1 = to_int(config.get('y1', 0), 0, context)
        duration = to_int(config.get('duration', 300), 300, context)
        
        # 根据模式计算终点坐标
        if swipe_mode == 'offset':
            # 偏移模式：起点 + 偏移量 = 终点
            offset_x = to_int(config.get('offsetX', 0), 0, context)
            offset_y = to_int(config.get('offsetY', 0), 0, context)
            x2 = x1 + offset_x
            y2 = y1 + offset_y
        else:
            # 坐标模式：直接使用终点坐标
            x2 = to_int(config.get('x2', 0), 0, context)
            y2 = to_int(config.get('y2', 0), 0, context)
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.swipe(x1, y1, x2, y2, duration, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            if swipe_mode == 'offset':
                offset_x = x2 - x1
                offset_y = y2 - y1
                return ModuleResult(success=True, message=f"已滑动 ({x1},{y1}) 偏移 ({offset_x:+d},{offset_y:+d})")
            else:
                return ModuleResult(success=True, message=f"已滑动 ({x1},{y1}) → ({x2},{y2})")
        except Exception as e:
            return ModuleResult(success=False, error=f"滑动失败: {str(e)}")
        except Exception as e:
            return ModuleResult(success=False, error=f"滑动失败: {str(e)}")
