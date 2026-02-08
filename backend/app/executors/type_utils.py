"""类型转换工具函数"""


def to_int(value, default: int, context=None) -> int:
    """将值转换为整数，支持变量解析"""
    if value is None:
        return default
    
    # 如果提供了 context，先解析变量
    if context is not None and isinstance(value, str):
        value = context.resolve_value(value)
    
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            return int(float(value))
        return default
    except (ValueError, TypeError):
        return default


def to_float(value, default: float, context=None) -> float:
    """将值转换为浮点数，支持变量解析"""
    if value is None:
        return default
    
    # 如果提供了 context，先解析变量
    if context is not None and isinstance(value, str):
        value = context.resolve_value(value)
    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return default
            return float(value)
        return default
    except (ValueError, TypeError):
        return default


def to_bool(value, context=None) -> bool:
    """将值转换为布尔值，支持变量解析"""
    if value is None:
        return False
    
    # 如果提供了 context，先解析变量
    if context is not None and isinstance(value, str):
        value = context.resolve_value(value)
    
    # 如果已经是布尔值，直接返回
    if isinstance(value, bool):
        return value
    
    # 字符串转换
    if isinstance(value, str):
        value = value.strip().lower()
        return value in ('true', 'yes', '1', 'on', 'enabled')
    
    # 数字转换
    if isinstance(value, (int, float)):
        return bool(value)
    
    return False


def parse_search_region(search_region: dict) -> tuple:
    """
    解析搜索区域配置，支持两种格式：
    1. 两点模式: {x, y, x2, y2} - 左上角和右下角坐标
    2. 起点+宽高模式: {x, y, width, height} - 兼容旧格式
    
    返回: (x, y, width, height) 或 (0, 0, 0, 0) 如果无效
    """
    if not search_region or not isinstance(search_region, dict):
        return (0, 0, 0, 0)
    
    x = int(search_region.get('x', 0) or 0)
    y = int(search_region.get('y', 0) or 0)
    
    # 优先使用两点模式 (x, y, x2, y2)
    if 'x2' in search_region or 'y2' in search_region:
        x2 = int(search_region.get('x2', 0) or 0)
        y2 = int(search_region.get('y2', 0) or 0)
        
        # 确保坐标顺序正确（左上角和右下角）
        if x2 < x:
            x, x2 = x2, x
        if y2 < y:
            y, y2 = y2, y
        
        width = x2 - x
        height = y2 - y
    else:
        # 兼容旧的起点+宽高模式
        width = int(search_region.get('width', 0) or 0)
        height = int(search_region.get('height', 0) or 0)
    
    return (x, y, width, height)
