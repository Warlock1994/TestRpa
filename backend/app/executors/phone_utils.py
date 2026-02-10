"""手机操作模块的共享工具函数"""
from .base import ExecutionContext
from ..services.adb_manager import get_adb_manager


def ensure_phone_connected(context: ExecutionContext) -> tuple[bool, str, str]:
    """确保手机已连接，如果未连接则自动连接
    
    Args:
        context: 执行上下文
        
    Returns:
        (成功与否, 设备ID, 错误信息)
    """
    # 如果已经有设备ID，直接返回
    if hasattr(context, 'phone_device_id') and context.phone_device_id:
        return True, context.phone_device_id, ""
    
    # 自动连接设备
    adb = get_adb_manager()
    success, device_id, error = adb.auto_connect_device()
    
    if success and device_id:
        # 保存设备ID到上下文
        context.phone_device_id = device_id
        return True, device_id, ""
    else:
        return False, "", error or "未知错误"
