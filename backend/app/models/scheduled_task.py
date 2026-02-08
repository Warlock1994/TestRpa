"""计划任务数据模型"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ScheduledTaskTrigger(BaseModel):
    """触发器配置"""
    type: str  # 'time' | 'hotkey' | 'startup'
    
    # 时间触发器配置
    schedule_type: Optional[str] = None  # 'once' | 'daily' | 'weekly' | 'monthly' | 'interval'
    start_date: Optional[str] = None  # YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM:SS
    end_date: Optional[str] = None  # YYYY-MM-DD (可选，结束日期)
    
    # 重复配置
    repeat_enabled: bool = False
    repeat_count: Optional[int] = None  # None表示无限重复
    repeat_interval: Optional[int] = None  # 重复间隔（秒）
    
    # 每日触发配置
    daily_time: Optional[str] = None  # HH:MM:SS
    
    # 每周触发配置
    weekly_days: Optional[List[int]] = None  # [0-6] 0=周日, 1=周一, ...
    weekly_time: Optional[str] = None  # HH:MM:SS
    
    # 每月触发配置
    monthly_day: Optional[int] = None  # 1-31
    monthly_time: Optional[str] = None  # HH:MM:SS
    
    # 间隔触发配置
    interval_seconds: Optional[int] = None  # 间隔秒数
    
    # 热键触发器配置
    hotkey: Optional[str] = None  # 例如: "ctrl+shift+f1"
    
    # 启动触发器配置
    startup_delay: Optional[int] = 0  # 启动延迟（秒）


class ScheduledTask(BaseModel):
    """计划任务模型"""
    id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    name: str
    description: Optional[str] = None
    workflow_id: str  # 关联的工作流ID
    workflow_name: Optional[str] = None  # 工作流名称（冗余字段，方便显示）
    
    # 触发器配置
    trigger: ScheduledTaskTrigger
    
    # 状态
    enabled: bool = True
    
    # 执行统计
    total_executions: int = 0
    success_executions: int = 0
    failed_executions: int = 0
    last_execution_time: Optional[str] = None
    last_execution_status: Optional[str] = None  # 'success' | 'failed'
    last_execution_error: Optional[str] = None
    next_execution_time: Optional[str] = None  # 下次执行时间（仅时间触发器）
    
    # 时间戳
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # 内部状态（不持久化）
    is_running: bool = False  # 当前是否正在执行
    current_repeat_count: int = 0  # 当前重复次数


class ScheduledTaskCreate(BaseModel):
    """创建计划任务请求"""
    name: str
    description: Optional[str] = None
    workflow_id: str
    workflow_name: Optional[str] = None
    trigger: ScheduledTaskTrigger
    enabled: bool = True


class ScheduledTaskUpdate(BaseModel):
    """更新计划任务请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    trigger: Optional[ScheduledTaskTrigger] = None
    enabled: Optional[bool] = None


class ScheduledTaskExecutionLog(BaseModel):
    """计划任务执行日志"""
    id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    task_id: str
    task_name: str
    workflow_id: str
    workflow_name: str
    
    # 执行信息
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[float] = None  # 执行时长（秒）
    status: str  # 'running' | 'success' | 'failed'
    error: Optional[str] = None
    
    # 触发信息
    trigger_type: str  # 'time' | 'hotkey' | 'startup' | 'manual'
    trigger_time: str
    
    # 执行结果
    executed_nodes: int = 0
    failed_nodes: int = 0
    collected_data_count: int = 0


class ScheduledTaskExecutionLogCreate(BaseModel):
    """创建执行日志请求"""
    task_id: str
    task_name: str
    workflow_id: str
    workflow_name: str
    trigger_type: str
    trigger_time: str = Field(default_factory=lambda: datetime.now().isoformat())
