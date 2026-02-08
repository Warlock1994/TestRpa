from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class Position(BaseModel):
    """节点位置"""
    x: float
    y: float


class ModuleType(str, Enum):
    """模块类型枚举"""
    # 基础模块
    OPEN_PAGE = "open_page"
    CLICK_ELEMENT = "click_element"
    INPUT_TEXT = "input_text"
    GET_ELEMENT_INFO = "get_element_info"
    WAIT = "wait"
    CLOSE_PAGE = "close_page"
    
    # 高级模块
    SELECT_DROPDOWN = "select_dropdown"
    SET_CHECKBOX = "set_checkbox"
    DRAG_ELEMENT = "drag_element"
    SCROLL_PAGE = "scroll_page"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    SAVE_IMAGE = "save_image"
    
    # 验证码模块
    OCR_CAPTCHA = "ocr_captcha"
    SLIDER_CAPTCHA = "slider_captcha"
    
    # 流程控制模块
    CONDITION = "condition"
    LOOP = "loop"
    FOREACH = "foreach"
    BREAK_LOOP = "break_loop"
    CONTINUE_LOOP = "continue_loop"


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str
    type: str
    position: Position
    data: dict[str, Any] = Field(default_factory=dict)
    style: Optional[dict[str, Any]] = None  # 节点样式（包含宽高等）


class WorkflowEdge(BaseModel):
    """工作流边（连接）"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class VariableType(str, Enum):
    """变量类型"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class Variable(BaseModel):
    """变量定义"""
    name: str
    value: Any = None
    type: VariableType = VariableType.STRING
    scope: str = "global"
    
    @model_validator(mode='before')
    @classmethod
    def parse_value(cls, data):
        """确保value与type匹配"""
        import json
        
        if isinstance(data, dict):
            value = data.get('value')
            var_type = data.get('type', 'string')
            
            # 如果value是字符串但type不是string，尝试解析
            if isinstance(value, str) and var_type != 'string':
                try:
                    if var_type == 'number':
                        data['value'] = float(value) if '.' in value else int(value)
                    elif var_type == 'boolean':
                        data['value'] = value.lower() in ('true', '1', 'yes')
                    elif var_type in ('array', 'object'):
                        data['value'] = json.loads(value)
                except (ValueError, json.JSONDecodeError):
                    pass  # 保持原值
        
        return data


class Workflow(BaseModel):
    """工作流定义"""
    id: str
    name: str
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    variables: list[Variable] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ExecutionResult(BaseModel):
    """执行结果"""
    workflow_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_nodes: int = 0
    executed_nodes: int = 0
    failed_nodes: int = 0
    error_message: Optional[str] = None
    data_file: Optional[str] = None


class LogLevel(str, Enum):
    """日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class LogEntry(BaseModel):
    """日志条目"""
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel = LogLevel.INFO
    node_id: Optional[str] = None
    message: str
    details: Optional[dict[str, Any]] = None
    duration: Optional[float] = None  # 毫秒
