"""AI模块执行器实现 - 异步版本"""
import asyncio
import base64
from pathlib import Path

import httpx

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)
from .type_utils import to_int, to_float


@register_executor
class AIChatExecutor(ModuleExecutor):
    """AI大脑模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "ai_chat"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        api_url = context.resolve_value(config.get('apiUrl', ''))
        api_key = context.resolve_value(config.get('apiKey', ''))
        model = context.resolve_value(config.get('model', ''))
        system_prompt = context.resolve_value(config.get('systemPrompt', ''))
        user_prompt = context.resolve_value(config.get('userPrompt', ''))
        variable_name = config.get('variableName', '')
        temperature = to_float(config.get('temperature', 0.7), 0.7, context)  # 支持变量引用
        max_tokens = to_int(config.get('maxTokens', 2000), 2000, context)  # 支持变量引用
        
        if not api_url:
            return ModuleResult(success=False, error="API地址不能为空")
        if not api_key:
            return ModuleResult(success=False, error="API密钥不能为空")
        if not model:
            return ModuleResult(success=False, error="模型名称不能为空")
        if not user_prompt:
            return ModuleResult(success=False, error="用户提示词不能为空")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
            
            request_body = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(api_url, json=request_body, headers=headers)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', error_msg)
                except:
                    pass
                return ModuleResult(success=False, error=f"API请求失败 ({response.status_code}): {error_msg}")
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return ModuleResult(success=False, error="API返回格式异常")
            
            ai_response = result['choices'][0].get('message', {}).get('content', '')
            
            if not ai_response:
                return ModuleResult(success=False, error="AI返回内容为空")
            
            if variable_name:
                context.set_variable(variable_name, ai_response)
            
            display_content = ai_response[:100] + '...' if len(ai_response) > 100 else ai_response
            
            return ModuleResult(
                success=True, 
                message=f"AI回复: {display_content}",
                data={'response': ai_response, 'model': model, 'usage': result.get('usage', {})}
            )
        
        except httpx.TimeoutException:
            return ModuleResult(success=False, error="API请求超时")
        except httpx.ConnectError:
            return ModuleResult(success=False, error="无法连接到API服务器")
        except Exception as e:
            return ModuleResult(success=False, error=f"AI调用失败: {str(e)}")


@register_executor
class AIVisionExecutor(ModuleExecutor):
    """AI视觉模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "ai_vision"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        api_url = context.resolve_value(config.get('apiUrl', ''))
        api_key = context.resolve_value(config.get('apiKey', ''))
        model = context.resolve_value(config.get('model', ''))
        user_prompt = context.resolve_value(config.get('userPrompt', ''))
        variable_name = config.get('variableName', '')
        max_tokens = to_int(config.get('maxTokens', 1000), 1000, context)  # 支持变量引用
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)  # 支持变量引用
        
        image_source = context.resolve_value(config.get('imageSource', 'element'))  # 支持变量引用
        image_selector = context.resolve_value(config.get('imageSelector', ''))
        image_url = context.resolve_value(config.get('imageUrl', ''))
        image_variable = config.get('imageVariable', '')
        
        if not api_url:
            return ModuleResult(success=False, error="API地址不能为空")
        if not api_key:
            return ModuleResult(success=False, error="API密钥不能为空")
        if not model:
            return ModuleResult(success=False, error="模型名称不能为空")
        if not user_prompt:
            return ModuleResult(success=False, error="提问内容不能为空")
        
        try:
            image_base64 = None
            image_url_final = None
            
            if image_source == 'element':
                if not image_selector:
                    return ModuleResult(success=False, error="请指定图片元素选择器")
                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")
                
                try:
                    await context.page.wait_for_selector(image_selector, state='visible', timeout=timeout_ms)
                    element = context.page.locator(image_selector).first
                    
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == 'img':
                        src = await element.get_attribute('src')
                        if src and src.startswith('data:'):
                            _, data = src.split(',', 1)
                            image_base64 = data
                        elif src and (src.startswith('http://') or src.startswith('https://')):
                            image_url_final = src
                        else:
                            screenshot_bytes = await element.screenshot()
                            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    else:
                        screenshot_bytes = await element.screenshot()
                        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        
                except Exception as e:
                    return ModuleResult(success=False, error=f"获取元素截图失败: {str(e)}")
            
            elif image_source == 'screenshot':
                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")
                
                try:
                    screenshot_bytes = await context.page.screenshot(full_page=False)
                    image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception as e:
                    return ModuleResult(success=False, error=f"页面截图失败: {str(e)}")
            
            elif image_source == 'url':
                if not image_url:
                    return ModuleResult(success=False, error="请指定图片URL")
                image_url_final = image_url
            
            elif image_source == 'variable':
                if not image_variable:
                    return ModuleResult(success=False, error="请指定图片变量名")
                
                var_value = context.get_variable(image_variable)
                if not var_value:
                    return ModuleResult(success=False, error=f"变量 '{image_variable}' 不存在或为空")
                
                var_value_str = str(var_value)
                
                if var_value_str.startswith('data:'):
                    _, data = var_value_str.split(',', 1)
                    image_base64 = data
                elif var_value_str.startswith('http://') or var_value_str.startswith('https://'):
                    image_url_final = var_value_str
                elif Path(var_value_str).exists():
                    with open(var_value_str, 'rb') as f:
                        image_base64 = base64.b64encode(f.read()).decode('utf-8')
                else:
                    image_base64 = var_value_str
            
            else:
                return ModuleResult(success=False, error=f"不支持的图片来源: {image_source}")
            
            content = []
            
            if image_base64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                })
            elif image_url_final:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url_final}
                })
            else:
                return ModuleResult(success=False, error="无法获取图片数据")
            
            content.append({"type": "text", "text": user_prompt})
            
            request_body = {
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": max_tokens
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(api_url, json=request_body, headers=headers)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', error_msg)
                except:
                    pass
                return ModuleResult(success=False, error=f"API请求失败 ({response.status_code}): {error_msg}")
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return ModuleResult(success=False, error="API返回格式异常")
            
            ai_response = result['choices'][0].get('message', {}).get('content', '')
            
            if not ai_response:
                return ModuleResult(success=False, error="AI返回内容为空")
            
            if variable_name:
                context.set_variable(variable_name, ai_response)
            
            display_content = ai_response[:100] + '...' if len(ai_response) > 100 else ai_response
            
            return ModuleResult(
                success=True, 
                message=f"AI视觉回复: {display_content}",
                data={'response': ai_response, 'model': model, 'image_source': image_source}
            )
        
        except httpx.TimeoutException:
            return ModuleResult(success=False, error="API请求超时")
        except httpx.ConnectError:
            return ModuleResult(success=False, error="无法连接到API服务器")
        except Exception as e:
            return ModuleResult(success=False, error=f"AI视觉调用失败: {str(e)}")
