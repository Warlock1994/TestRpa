"""手机应用管理模块执行器"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .phone_utils import ensure_phone_connected
from ..services.adb_manager import get_adb_manager


@register_executor
class PhoneInstallAppExecutor(ModuleExecutor):
    """安装手机应用"""
    
    @property
    def module_type(self) -> str:
        return "phone_install_app"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        apk_path = context.resolve_value(config.get('apkPath', ''))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        if not apk_path:
            return ModuleResult(success=False, error="APK路径不能为空")
        
        try:
            adb = get_adb_manager()
            success, error = adb.install_apk(apk_path, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            return ModuleResult(success=True, message=f"应用安装成功")
        except Exception as e:
            return ModuleResult(success=False, error=f"安装应用失败: {str(e)}")


@register_executor
class PhoneStartAppExecutor(ModuleExecutor):
    """启动手机应用"""
    
    @property
    def module_type(self) -> str:
        return "phone_start_app"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        package_name = context.resolve_value(config.get('packageName', ''))
        activity_name = context.resolve_value(config.get('activityName', ''))
        
        # 自动连接设备
        success, device_id, error = ensure_phone_connected(context)
        if not success:
            return ModuleResult(success=False, error=error)
        
        if not package_name:
            return ModuleResult(success=False, error="应用包名或名称不能为空")
        
        try:
            adb = get_adb_manager()
            
            # 判断是包名还是应用名称
            # 包名通常包含点号，如 com.tencent.mm
            if '.' in package_name:
                # 看起来是包名，直接使用
                actual_package = package_name
                context.log(f"使用包名启动: {actual_package}")
            else:
                # 看起来是应用名称，需要查找对应的包名
                context.log(f"通过应用名称查找包名: {package_name}")
                success, actual_package, error, matches = adb.find_package_by_name(package_name, device_id)
                
                if not success:
                    return ModuleResult(success=False, error=error)
                
                context.log(f"找到包名: {actual_package}")
            
            # 启动应用
            success, error = adb.start_app(actual_package, activity_name, device_id)
            if not success:
                return ModuleResult(success=False, error=error)
            
            return ModuleResult(success=True, message=f"应用已启动: {actual_package}")
        except Exception as e:
            return ModuleResult(success=False, error=f"启动应用失败: {str(e)}")
