"""变量管理器"""
import re
from typing import Any, Optional


class VariableManager:
    """变量管理器"""
    
    def __init__(self):
        self._global_vars: dict[str, Any] = {}
        self._local_vars: dict[str, Any] = {}
        self._scope_stack: list[dict[str, Any]] = []
    
    def set(self, name: str, value: Any, scope: str = "global"):
        """设置变量值"""
        if scope == "global":
            self._global_vars[name] = value
        else:
            self._local_vars[name] = value
    
    def get(self, name: str, default: Any = None) -> Any:
        """获取变量值，优先查找局部变量"""
        # 先查找局部变量
        if name in self._local_vars:
            return self._local_vars[name]
        # 再查找全局变量
        return self._global_vars.get(name, default)
    
    def delete(self, name: str):
        """删除变量"""
        if name in self._local_vars:
            del self._local_vars[name]
        if name in self._global_vars:
            del self._global_vars[name]
    
    def exists(self, name: str) -> bool:
        """检查变量是否存在"""
        return name in self._local_vars or name in self._global_vars
    
    def get_all(self) -> dict[str, Any]:
        """获取所有变量"""
        result = self._global_vars.copy()
        result.update(self._local_vars)
        return result
    
    def get_global_vars(self) -> dict[str, Any]:
        """获取所有全局变量"""
        return self._global_vars.copy()
    
    def get_local_vars(self) -> dict[str, Any]:
        """获取所有局部变量"""
        return self._local_vars.copy()
    
    def clear_local(self):
        """清空局部变量"""
        self._local_vars = {}
    
    def clear_all(self):
        """清空所有变量"""
        self._global_vars = {}
        self._local_vars = {}
    
    def push_scope(self):
        """压入新的作用域"""
        self._scope_stack.append(self._local_vars.copy())
        self._local_vars = {}
    
    def pop_scope(self):
        """弹出作用域"""
        if self._scope_stack:
            self._local_vars = self._scope_stack.pop()
    
    def resolve(self, value: Any) -> Any:
        """解析值中的变量引用"""
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value
    
    def _resolve_string(self, text: str) -> str:
        """解析字符串中的变量引用
        
        支持两种格式：
        - ${varName} - 标准格式
        - {varName} - 简化格式
        """
        # 先匹配 ${varName} 格式
        pattern1 = r'\$\{([^}]+)\}'
        # 再匹配 {varName} 格式（但不匹配已经有$的）
        pattern2 = r'(?<!\$)\{([^}]+)\}'
        
        def replacer(match):
            var_name = match.group(1).strip()
            var_value = self.get(var_name)
            if var_value is None:
                return match.group(0)  # 保持原样
            return str(var_value)
        
        # 先处理 ${} 格式
        result = re.sub(pattern1, replacer, text)
        # 再处理 {} 格式
        result = re.sub(pattern2, replacer, result)
        
        return result
    
    def evaluate_expression(self, expression: str) -> Any:
        """计算简单表达式"""
        # 先解析变量
        resolved = self._resolve_string(expression)
        
        # 尝试计算数学表达式
        try:
            # 只允许安全的操作
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in resolved):
                return eval(resolved)
        except:
            pass
        
        # 返回解析后的字符串
        return resolved
