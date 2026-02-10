"""
配置工具模块
提供配置读取和 URL 生成功能
"""
import json
import os
from typing import Optional


_config_cache: Optional[dict] = None


def load_config() -> dict:
    """加载配置文件（带缓存）"""
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'WebRPAConfig.json'
    )
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                _config_cache = json.load(f)
                return _config_cache
    except Exception as e:
        print(f"[Config] 读取配置文件失败: {e}")
    
    # 返回默认配置
    _config_cache = {
        'backend': {
            'host': '0.0.0.0',
            'port': 8000,
            'reload': False
        },
        'frontend': {
            'host': '0.0.0.0',
            'port': 5173
        }
    }
    return _config_cache


def get_backend_config() -> dict:
    """获取后端配置"""
    config = load_config()
    return config.get('backend', {
        'host': '0.0.0.0',
        'port': 8000,
        'reload': False
    })


def get_backend_port() -> int:
    """获取后端端口"""
    config = get_backend_config()
    return config.get('port', 8000)


def get_backend_url(use_localhost: bool = True) -> str:
    """
    获取后端基础 URL
    
    Args:
        use_localhost: 是否使用 localhost（默认 True）
                      False 时使用 0.0.0.0 或配置的 host
    
    Returns:
        后端基础 URL，如 http://localhost:8000
    """
    config = get_backend_config()
    port = config.get('port', 8000)
    
    if use_localhost:
        return f"http://localhost:{port}"
    else:
        host = config.get('host', '0.0.0.0')
        return f"http://{host}:{port}"


def reload_config():
    """重新加载配置（清除缓存）"""
    global _config_cache
    _config_cache = None
