"""基础模块执行器 - 变量和工具相关"""
import asyncio
import re

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor, escape_css_selector
from .type_utils import to_int, to_float


@register_executor
class GroupExecutor(ModuleExecutor):
    """备注分组模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "group"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        return ModuleResult(success=True, message="备注分组（跳过）")


@register_executor
class SetVariableExecutor(ModuleExecutor):
    """设置变量模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "set_variable"
    
    def _evaluate_expression(self, expr: str, context: ExecutionContext):
        """安全地计算表达式"""
        def replace_var(match):
            var_name = match.group(1).strip()
            value = context.variables.get(var_name, 0)
            try:
                if isinstance(value, (int, float)):
                    return str(value)
                return str(float(value))
            except (ValueError, TypeError):
                return str(value)
        
        resolved = re.sub(r'\{([^}]+)\}', replace_var, expr)
        
        if re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', resolved):
            try:
                result = eval(resolved, {"__builtins__": {}}, {})
                if isinstance(result, float) and result.is_integer():
                    return int(result)
                return result
            except:
                pass
        
        try:
            if '.' in resolved:
                return float(resolved)
            return int(resolved)
        except ValueError:
            return resolved
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        variable_name = config.get('variableName', '')
        variable_value = context.resolve_value(config.get('variableValue', ''))
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            resolved_value = self._evaluate_expression(variable_value, context)
            context.set_variable(variable_name, resolved_value)
            
            return ModuleResult(success=True, message=f"已设置变量 {variable_name} = {resolved_value}",
                              data=resolved_value)
        except Exception as e:
            return ModuleResult(success=False, error=f"设置变量失败: {str(e)}")


@register_executor
class PrintLogExecutor(ModuleExecutor):
    """打印日志模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "print_log"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        log_message = context.resolve_value(config.get('logMessage', '')) or '(空日志)'
        log_level = context.resolve_value(config.get('logLevel', 'info'))
        
        try:
            return ModuleResult(success=True, message=log_message,
                              data={'level': log_level, 'message': log_message}, log_level=log_level)
        except Exception as e:
            return ModuleResult(success=False, error=f"打印日志失败: {str(e)}")


@register_executor
class RandomNumberExecutor(ModuleExecutor):
    """生成随机数模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "random_number"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import random
        
        random_type = context.resolve_value(config.get('randomType', 'integer'))
        min_value = to_float(config.get('minValue', 0), 0, context)
        max_value = to_float(config.get('maxValue', 100), 100, context)
        decimal_places = to_int(config.get('decimalPlaces', 2), 2, context)
        variable_name = config.get('variableName', '')
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            if min_value > max_value:
                min_value, max_value = max_value, min_value
            
            if random_type == 'integer':
                result = random.randint(int(min_value), int(max_value))
            else:
                result = random.uniform(float(min_value), float(max_value))
                result = round(result, decimal_places)
            
            context.set_variable(variable_name, result)
            
            return ModuleResult(success=True, message=f"已生成随机数: {result}", data={'value': result})
        except Exception as e:
            return ModuleResult(success=False, error=f"生成随机数失败: {str(e)}")


@register_executor
class GetTimeExecutor(ModuleExecutor):
    """获取时间模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "get_time"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from datetime import datetime
        
        time_format = context.resolve_value(config.get('timeFormat', 'datetime'))
        custom_format = context.resolve_value(config.get('customFormat', ''))
        variable_name = config.get('variableName', '')
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            now = datetime.now()
            
            if time_format == 'datetime':
                result = now.strftime('%Y-%m-%d %H:%M:%S')
            elif time_format == 'date':
                result = now.strftime('%Y-%m-%d')
            elif time_format == 'time':
                result = now.strftime('%H:%M:%S')
            elif time_format == 'timestamp':
                result = int(now.timestamp() * 1000)
            elif time_format == 'custom' and custom_format:
                result = now.strftime(custom_format)
            else:
                result = now.strftime('%Y-%m-%d %H:%M:%S')
            
            context.set_variable(variable_name, result)
            
            return ModuleResult(success=True, message=f"已获取时间: {result}", data={'value': result})
        except Exception as e:
            return ModuleResult(success=False, error=f"获取时间失败: {str(e)}")


@register_executor
class WaitExecutor(ModuleExecutor):
    """等待模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "wait"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        wait_type = context.resolve_value(config.get('waitType', 'time'))
        
        try:
            if wait_type == 'time':
                duration = to_int(config.get('duration', 1000), 1000, context)
                await asyncio.sleep(duration / 1000)
                return ModuleResult(success=True, message=f"已等待 {duration}ms")
            
            elif wait_type == 'selector':
                selector = context.resolve_value(config.get('selector', ''))
                state = context.resolve_value(config.get('state', 'visible'))
                
                if not selector:
                    return ModuleResult(success=False, error="选择器不能为空")
                
                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")
                
                await context.switch_to_latest_page()
                await context.page.wait_for_selector(escape_css_selector(selector), state=state)
                return ModuleResult(success=True, message=f"元素已{state}: {selector}")
            
            elif wait_type == 'navigation':
                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")
                
                await context.switch_to_latest_page()
                await context.page.wait_for_load_state('networkidle')
                return ModuleResult(success=True, message="页面导航完成")
            
            return ModuleResult(success=False, error=f"未知的等待类型: {wait_type}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"等待失败: {str(e)}")


@register_executor
class WaitElementExecutor(ModuleExecutor):
    """等待元素模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "wait_element"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        wait_condition = context.resolve_value(config.get('waitCondition', 'visible'))
        wait_timeout = to_int(config.get('waitTimeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            state_map = {'visible': 'visible', 'hidden': 'hidden', 'attached': 'attached', 'detached': 'detached'}
            state = state_map.get(wait_condition, 'visible')
            
            escaped_selector = escape_css_selector(selector)
            
            # 调试：打印当前页面信息
            if context.page:
                print(f"[DEBUG wait_element] 当前页面 URL: {context.page.url}")
                print(f"[DEBUG wait_element] 选择器: {selector[:100]}...")
                print(f"[DEBUG wait_element] 转义后: {escaped_selector[:100]}...")
                
                # 尝试直接查找元素，看看能找到几个
                try:
                    locator = context.page.locator(escaped_selector)
                    count = await locator.count()
                    print(f"[DEBUG wait_element] 找到元素数量: {count}")
                    if count > 0:
                        is_visible = await locator.first.is_visible()
                        print(f"[DEBUG wait_element] 第一个元素是否可见: {is_visible}")
                except Exception as e:
                    print(f"[DEBUG wait_element] 查找元素出错: {e}")
            
            await context.page.wait_for_selector(escaped_selector, state=state, timeout=wait_timeout)
            
            condition_labels = {'visible': '可见', 'hidden': '隐藏/消失', 'attached': '存在于DOM', 'detached': '从DOM移除'}
            label = condition_labels.get(wait_condition, wait_condition)
            
            return ModuleResult(success=True, message=f"元素已{label}: {selector}",
                              data={'selector': selector, 'condition': wait_condition})
        
        except Exception as e:
            error_msg = str(e)
            if 'Timeout' in error_msg:
                return ModuleResult(success=False, error=f"等待超时 ({wait_timeout}ms): 元素 {selector} 未满足条件 '{wait_condition}'")
            return ModuleResult(success=False, error=f"等待元素失败: {error_msg}")
