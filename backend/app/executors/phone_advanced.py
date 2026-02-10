"""手机高级操作模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneLongPressExecutor(ModuleExecutor):
    """手机长按"""
    
    @property
    def module_type(self) -> str:
        return "phone_long_press"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        x = to_int(config.get('x', 0), 0, context)
        y = to_int(config.get('y', 0), 0, context)
        duration = to_int(config.get('duration', 1000), 1000, context)
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        try:
            adb = get_adb_manager()
            success, error = adb.long_press(x, y, duration, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"已长按坐标 ({x}, {y})")
        except Exception as e:
            return ModuleResult(success=False, error=f"长按失败: {str(e)}")


@register_executor
class PhoneStopAppExecutor(ModuleExecutor):
    """停止手机应用"""
    
    @property
    def module_type(self) -> str:
        return "phone_stop_app"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        package_name = context.resolve_value(config.get('packageName', ''))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        if not package_name:
            return ModuleResult(success=False, error="应用包名或名称不能为空")
        
        try:
            adb = get_adb_manager()
            
            # 判断是包名还是应用名称
            if '.' in package_name:
                # 看起来是包名，直接使用
                actual_package = package_name
                context.log(f"使用包名停止: {actual_package}")
            else:
                # 看起来是应用名称，需要查找对应的包名
                context.log(f"通过应用名称查找包名: {package_name}")
                success, actual_package, error, matches = adb.find_package_by_name(package_name, device_id)
                
                if not success:
                    return ModuleResult(success=False, error=error)
                
                context.log(f"找到包名: {actual_package}")
            
            success, error = adb.stop_app(actual_package, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"应用已停止: {actual_package}")
        except Exception as e:
            return ModuleResult(success=False, error=f"停止应用失败: {str(e)}")


@register_executor
class PhoneUninstallAppExecutor(ModuleExecutor):
    """卸载手机应用"""
    
    @property
    def module_type(self) -> str:
        return "phone_uninstall_app"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        package_name = context.resolve_value(config.get('packageName', ''))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        if not package_name:
            return ModuleResult(success=False, error="应用包名或名称不能为空")
        
        try:
            adb = get_adb_manager()
            
            # 判断是包名还是应用名称
            if '.' in package_name:
                # 看起来是包名，直接使用
                actual_package = package_name
                context.log(f"使用包名卸载: {actual_package}")
            else:
                # 看起来是应用名称，需要查找对应的包名
                context.log(f"通过应用名称查找包名: {package_name}")
                success, actual_package, error, matches = adb.find_package_by_name(package_name, device_id)
                
                if not success:
                    return ModuleResult(success=False, error=error)
                
                context.log(f"找到包名: {actual_package}")
            
            success, error = adb.uninstall_app(actual_package, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"应用已卸载: {actual_package}")
        except Exception as e:
            return ModuleResult(success=False, error=f"卸载应用失败: {str(e)}")
