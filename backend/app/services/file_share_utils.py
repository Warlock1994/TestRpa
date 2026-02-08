"""文件共享工具函数"""
import socket


def get_local_ip() -> str:
    """获取本机局域网IP地址，优先返回私有网络IP"""
    try:
        # 获取所有网络接口的IP
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        
        # 优先级：192.168.x.x > 10.x.x.x > 172.16-31.x.x > 其他
        private_ips = []
        for ip in ip_list:
            if ip.startswith('192.168.'):
                return ip  # 最优先
            elif ip.startswith('10.'):
                private_ips.insert(0, ip)  # 次优先
            elif ip.startswith('172.'):
                # 检查是否是172.16-31.x.x
                parts = ip.split('.')
                if len(parts) >= 2:
                    second = int(parts[1])
                    if 16 <= second <= 31:
                        private_ips.append(ip)
        
        if private_ips:
            return private_ips[0]
        
        # 如果没有找到私有IP，尝试通过连接获取
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
