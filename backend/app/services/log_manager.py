"""日志管理器"""
from datetime import datetime
from typing import Optional, Callable, Awaitable
from uuid import uuid4

from app.models.workflow import LogLevel, LogEntry


class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.logs: list[LogEntry] = []
        self.session_id: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self._on_log: Optional[Callable[[LogEntry], Awaitable[None]]] = None
    
    def start_session(self) -> str:
        """开始新的日志会话"""
        self.session_id = str(uuid4())
        self.session_start = datetime.now()
        self.logs = []
        return self.session_id
    
    def set_callback(self, callback: Callable[[LogEntry], Awaitable[None]]):
        """设置日志回调"""
        self._on_log = callback
    
    async def log(
        self,
        level: LogLevel,
        message: str,
        node_id: Optional[str] = None,
        details: Optional[dict] = None,
        duration: Optional[float] = None,
    ) -> LogEntry:
        """记录日志"""
        entry = LogEntry(
            id=str(uuid4()),
            timestamp=datetime.now(),
            level=level,
            node_id=node_id,
            message=message,
            details=details,
            duration=duration,
        )
        
        self.logs.append(entry)
        
        if self._on_log:
            await self._on_log(entry)
        
        return entry
    
    async def info(self, message: str, node_id: Optional[str] = None, **kwargs) -> LogEntry:
        """记录信息日志"""
        return await self.log(LogLevel.INFO, message, node_id, **kwargs)
    
    async def warning(self, message: str, node_id: Optional[str] = None, **kwargs) -> LogEntry:
        """记录警告日志"""
        return await self.log(LogLevel.WARNING, message, node_id, **kwargs)
    
    async def error(self, message: str, node_id: Optional[str] = None, **kwargs) -> LogEntry:
        """记录错误日志"""
        return await self.log(LogLevel.ERROR, message, node_id, **kwargs)
    
    async def success(self, message: str, node_id: Optional[str] = None, **kwargs) -> LogEntry:
        """记录成功日志"""
        return await self.log(LogLevel.SUCCESS, message, node_id, **kwargs)
    
    def get_logs(self) -> list[LogEntry]:
        """获取所有日志"""
        return self.logs
    
    def get_logs_by_level(self, level: LogLevel) -> list[LogEntry]:
        """按级别获取日志"""
        return [log for log in self.logs if log.level == level]
    
    def get_logs_by_node(self, node_id: str) -> list[LogEntry]:
        """按节点获取日志"""
        return [log for log in self.logs if log.node_id == node_id]
    
    def clear(self):
        """清空日志"""
        self.logs = []
    
    def export_text(self) -> str:
        """导出为文本格式"""
        lines = []
        
        if self.session_start:
            lines.append(f"=== 日志会话 {self.session_id} ===")
            lines.append(f"开始时间: {self.session_start.isoformat()}")
            lines.append("")
        
        for log in self.logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            level = log.level.value.upper()
            node_info = f" [节点: {log.node_id}]" if log.node_id else ""
            duration_info = f" ({log.duration:.0f}ms)" if log.duration else ""
            
            lines.append(f"[{timestamp}] [{level}]{node_info} {log.message}{duration_info}")
            
            if log.details:
                for key, value in log.details.items():
                    lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def get_summary(self) -> dict:
        """获取日志摘要"""
        return {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "total_logs": len(self.logs),
            "info_count": len(self.get_logs_by_level(LogLevel.INFO)),
            "warning_count": len(self.get_logs_by_level(LogLevel.WARNING)),
            "error_count": len(self.get_logs_by_level(LogLevel.ERROR)),
            "success_count": len(self.get_logs_by_level(LogLevel.SUCCESS)),
        }
