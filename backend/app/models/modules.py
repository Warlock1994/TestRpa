from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class BaseModuleConfig(BaseModel):
    """模块配置基类"""
    name: Optional[str] = None
    description: Optional[str] = None
    timeout: int = 30000  # 毫秒
    retry_count: int = 0


# ============ 基础模块配置 ============

class WaitUntil(str, Enum):
    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"


class OpenPageConfig(BaseModuleConfig):
    """打开网页模块配置"""
    url: str
    wait_until: WaitUntil = WaitUntil.LOAD


class ClickType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    RIGHT = "right"


class ClickElementConfig(BaseModuleConfig):
    """点击元素模块配置"""
    selector: str
    click_type: ClickType = ClickType.SINGLE
    wait_for_selector: bool = True


class InputTextConfig(BaseModuleConfig):
    """输入文本模块配置"""
    selector: str
    text: str
    clear_before: bool = True


class ElementAttribute(str, Enum):
    TEXT = "text"
    INNER_HTML = "innerHTML"
    VALUE = "value"
    HREF = "href"
    SRC = "src"
    CUSTOM = "custom"


class GetElementInfoConfig(BaseModuleConfig):
    """获取元素信息模块配置"""
    selector: str
    attribute: ElementAttribute = ElementAttribute.TEXT
    custom_attribute: Optional[str] = None  # 当attribute为CUSTOM时使用
    variable_name: str
    column_name: Optional[str] = None  # 用于数据导出时的列名


class WaitType(str, Enum):
    TIME = "time"
    SELECTOR = "selector"
    NAVIGATION = "navigation"


class WaitConfig(BaseModuleConfig):
    """等待模块配置"""
    wait_type: WaitType = WaitType.TIME
    duration: int = 1000  # 毫秒，用于TIME类型
    selector: Optional[str] = None  # 用于SELECTOR类型
    state: Optional[str] = "visible"  # visible, hidden, attached, detached


class ClosePageConfig(BaseModuleConfig):
    """关闭网页模块配置"""
    pass  # 无额外配置


# ============ 高级模块配置 ============

class SelectBy(str, Enum):
    VALUE = "value"
    LABEL = "label"
    INDEX = "index"


class SelectDropdownConfig(BaseModuleConfig):
    """下拉框选择模块配置"""
    selector: str
    select_by: SelectBy = SelectBy.VALUE
    value: str


class SetCheckboxConfig(BaseModuleConfig):
    """设置复选框模块配置"""
    selector: str
    checked: bool = True


class DragElementConfig(BaseModuleConfig):
    """拖拽元素模块配置"""
    source_selector: str
    target_selector: Optional[str] = None
    target_position: Optional[dict] = None  # {"x": 100, "y": 200}


class ScrollDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class ScrollPageConfig(BaseModuleConfig):
    """滚动页面模块配置"""
    direction: ScrollDirection = ScrollDirection.DOWN
    distance: int = 500  # 像素
    selector: Optional[str] = None  # 如果指定，则滚动该元素


class UploadFileConfig(BaseModuleConfig):
    """上传文件模块配置"""
    selector: str
    file_path: str


class DownloadFileConfig(BaseModuleConfig):
    """下载文件模块配置"""
    trigger_selector: str
    save_path: Optional[str] = None
    variable_name: Optional[str] = None  # 存储下载文件路径的变量


class SaveImageConfig(BaseModuleConfig):
    """保存图片模块配置"""
    selector: str
    save_path: Optional[str] = None
    variable_name: Optional[str] = None


# ============ 验证码模块配置 ============

class OCRCaptchaConfig(BaseModuleConfig):
    """文本验证码识别模块配置"""
    image_selector: str
    input_selector: str
    variable_name: Optional[str] = None
    auto_submit: bool = False
    submit_selector: Optional[str] = None


class SliderCaptchaConfig(BaseModuleConfig):
    """滑块验证码模块配置"""
    slider_selector: str
    background_selector: Optional[str] = None
    gap_selector: Optional[str] = None


# ============ 流程控制模块配置 ============

class ConditionType(str, Enum):
    VARIABLE = "variable"
    ELEMENT_EXISTS = "element_exists"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_TEXT = "element_text"


class Operator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUALS = ">="
    LESS_EQUALS = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class ConditionConfig(BaseModuleConfig):
    """条件判断模块配置"""
    condition_type: ConditionType = ConditionType.VARIABLE
    left_operand: str  # 变量名或选择器
    operator: Operator = Operator.EQUALS
    right_operand: str  # 比较值


class LoopType(str, Enum):
    COUNT = "count"
    WHILE = "while"


class LoopConfig(BaseModuleConfig):
    """循环执行模块配置"""
    loop_type: LoopType = LoopType.COUNT
    count: int = 10  # 用于COUNT类型
    condition: Optional[str] = None  # 用于WHILE类型，变量名
    max_iterations: int = 1000  # 最大迭代次数，防止无限循环
    index_variable: str = "loop_index"


class ForeachConfig(BaseModuleConfig):
    """遍历列表模块配置"""
    data_source: str  # 变量名，指向数组
    item_variable: str = "item"
    index_variable: str = "index"
