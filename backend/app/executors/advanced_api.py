"""高级模块执行器 - API请求、JSON解析、Base64处理"""
import base64
import json
from pathlib import Path

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int


@register_executor
class ApiRequestExecutor(ModuleExecutor):
    """API请求模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "api_request"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import httpx
        
        request_url = context.resolve_value(config.get('requestUrl', ''))
        request_method = context.resolve_value(config.get('requestMethod', 'GET')).upper()
        request_headers_str = context.resolve_value(config.get('requestHeaders', ''))
        request_body_str = context.resolve_value(config.get('requestBody', ''))
        variable_name = config.get('variableName', '')
        request_timeout = to_int(config.get('requestTimeout', 30), 30, context)
        
        if not request_url:
            return ModuleResult(success=False, error="请求地址不能为空")
        
        try:
            headers = {}
            if request_headers_str:
                try:
                    headers = json.loads(request_headers_str)
                except json.JSONDecodeError as e:
                    return ModuleResult(success=False, error=f"请求头JSON格式错误: {str(e)}")
            
            body = None
            if request_body_str:
                try:
                    body = json.loads(request_body_str)
                except json.JSONDecodeError:
                    body = request_body_str
            
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.request(
                    method=request_method, url=request_url, headers=headers,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                )
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            if variable_name:
                context.set_variable(variable_name, response_data)
            
            display_content = str(response_data)[:100] + '...' if len(str(response_data)) > 100 else str(response_data)
            return ModuleResult(success=True, message=f"请求成功 ({response.status_code}): {display_content}",
                              data={'status_code': response.status_code, 'response': response_data})
        
        except Exception as e:
            error_msg = "请求超时" if "timeout" in str(e).lower() else f"API请求失败: {str(e)}"
            return ModuleResult(success=False, error=error_msg)


@register_executor
class JsonParseExecutor(ModuleExecutor):
    """JSON解析模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "json_parse"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        source_variable = config.get('sourceVariable', '')
        json_path = context.resolve_value(config.get('jsonPath', ''))
        variable_name = config.get('variableName', '')
        column_name = config.get('columnName', '')
        
        if not source_variable:
            return ModuleResult(success=False, error="源数据变量不能为空")
        if not json_path:
            return ModuleResult(success=False, error="JSONPath表达式不能为空")
        
        source_data = context.get_variable(source_variable)
        if source_data is None:
            return ModuleResult(success=False, error=f"变量 '{source_variable}' 不存在")
        
        if isinstance(source_data, str):
            try:
                source_data = json.loads(source_data)
            except json.JSONDecodeError as e:
                return ModuleResult(success=False, error=f"源数据不是有效的JSON: {str(e)}")
        
        try:
            result = self._parse_jsonpath(source_data, json_path)
            if variable_name:
                context.set_variable(variable_name, result)
            if column_name:
                context.add_data_value(column_name, result)
            display = str(result)[:100] + '...' if len(str(result)) > 100 else str(result)
            return ModuleResult(success=True, message=f"解析成功: {display}", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"JSON解析失败: {str(e)}")
    
    def _parse_jsonpath(self, data, path: str):
        if path.startswith('$'):
            path = path[1:]
        if path.startswith('.'):
            path = path[1:]
        if not path:
            return data
        
        current = data
        for part in self._split_path(path):
            if current is None:
                return None
            if part.startswith('[') and part.endswith(']'):
                idx = part[1:-1]
                if idx == '*':
                    return current if isinstance(current, list) else None
                try:
                    i = int(idx)
                    current = current[i] if isinstance(current, list) and -len(current) <= i < len(current) else None
                except:
                    return None
            elif '[' in part:
                prop = part[:part.index('[')]
                arr = part[part.index('['):]
                current = self._parse_jsonpath(current.get(prop), arr) if isinstance(current, dict) and prop in current else None
            else:
                current = current.get(part) if isinstance(current, dict) else None
        return current
    
    def _split_path(self, path: str) -> list:
        parts, cur, bracket = [], '', False
        for c in path:
            if c == '[':
                if cur:
                    parts.append(cur)
                    cur = ''
                bracket = True
                cur = '['
            elif c == ']':
                cur += ']'
                parts.append(cur)
                cur = ''
                bracket = False
            elif c == '.' and not bracket:
                if cur:
                    parts.append(cur)
                    cur = ''
            else:
                cur += c
        if cur:
            parts.append(cur)
        return parts


@register_executor
class Base64Executor(ModuleExecutor):
    """Base64处理模块执行器"""

    @property
    def module_type(self) -> str:
        return "base64"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        operation = context.resolve_value(config.get("operation", "encode"))
        variable_name = config.get("variableName", "")

        try:
            if operation == "encode":
                input_text = context.resolve_value(config.get("inputText", ""))
                if not input_text:
                    return ModuleResult(success=False, error="输入文本不能为空")
                result = base64.b64encode(input_text.encode("utf-8")).decode("utf-8")
                if variable_name:
                    context.set_variable(variable_name, result)
                return ModuleResult(success=True, message=f"编码成功: {result[:50]}...", data=result)

            elif operation == "decode":
                input_base64 = context.resolve_value(config.get("inputBase64", ""))
                if not input_base64:
                    return ModuleResult(success=False, error="Base64字符串不能为空")
                if "," in input_base64:
                    input_base64 = input_base64.split(",", 1)[1]
                result = base64.b64decode(input_base64).decode("utf-8")
                if variable_name:
                    context.set_variable(variable_name, result)
                return ModuleResult(success=True, message=f"解码成功: {result[:50]}...", data=result)

            elif operation == "file_to_base64":
                file_path = context.resolve_value(config.get("filePath", ""))
                if not file_path:
                    return ModuleResult(success=False, error="文件路径不能为空")
                path = Path(file_path)
                if not path.exists():
                    return ModuleResult(success=False, error=f"文件不存在: {file_path}")
                with open(path, "rb") as f:
                    file_data = f.read()
                result = base64.b64encode(file_data).decode("utf-8")
                mime_types = {
                    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".gif": "image/gif", ".pdf": "application/pdf", ".txt": "text/plain"
                }
                mime_type = mime_types.get(path.suffix.lower(), "application/octet-stream")
                data_url = f"data:{mime_type};base64,{result}"
                if variable_name:
                    context.set_variable(variable_name, data_url)
                return ModuleResult(success=True, message=f"文件转换成功: {path.name}", data=data_url)

            elif operation == "base64_to_file":
                input_base64 = context.resolve_value(config.get("inputBase64", ""))
                output_path = context.resolve_value(config.get("outputPath", ""))
                file_name = context.resolve_value(config.get("fileName", "output.bin"))
                if not input_base64 or not output_path:
                    return ModuleResult(success=False, error="Base64字符串和保存路径不能为空")
                if "," in input_base64:
                    input_base64 = input_base64.split(",", 1)[1]
                file_data = base64.b64decode(input_base64)
                output_dir = Path(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
                full_path = output_dir / file_name
                with open(full_path, "wb") as f:
                    f.write(file_data)
                if variable_name:
                    context.set_variable(variable_name, str(full_path))
                return ModuleResult(success=True, message=f"文件保存成功: {full_path}", data=str(full_path))
            else:
                return ModuleResult(success=False, error=f"未知操作类型: {operation}")
        except Exception as e:
            return ModuleResult(success=False, error=f"Base64处理失败: {str(e)}")
