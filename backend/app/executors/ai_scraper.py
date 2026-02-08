"""AI智能爬虫模块执行器 - 基于 ScrapeGraphAI"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
import json

# 尝试导入 nest_asyncio 以支持嵌套事件循环
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # 如果未安装，继续执行（可能会遇到事件循环问题）


@register_executor
class AISmartScraperExecutor(ModuleExecutor):
    """AI智能爬虫模块执行器
    
    使用 ScrapeGraphAI 的能力，通过自然语言描述来提取网页数据。
    优点：适应网页结构变化，减少维护成本
    缺点：速度比传统爬虫慢，需要 LLM 支持
    """
    
    @property
    def module_type(self) -> str:
        return "ai_smart_scraper"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            # 检查是否安装了 scrapegraphai
            try:
                from scrapegraphai.graphs import SmartScraperGraph
            except ImportError:
                return ModuleResult(
                    success=False, 
                    error="未安装 scrapegraphai 库。请运行: pip install scrapegraphai"
                )
            
            # 获取配置
            url = context.resolve_value(config.get('url', ''))
            prompt = context.resolve_value(config.get('prompt', ''))
            variable_name = config.get('variableName', '')
            wait_time = config.get('waitTime', 3)  # 默认等待3秒
            
            # LLM 配置
            llm_provider = context.resolve_value(config.get('llmProvider', 'ollama'))
            api_url = context.resolve_value(config.get('apiUrl', ''))
            llm_model = context.resolve_value(config.get('llmModel', 'llama3.2'))
            api_key = context.resolve_value(config.get('apiKey', ''))
            
            # 参数验证
            if not url:
                return ModuleResult(success=False, error="URL 不能为空")
            
            if not prompt:
                return ModuleResult(success=False, error="提取提示词不能为空")
            
            if not variable_name:
                return ModuleResult(success=False, error="变量名不能为空")
            
            # 如果有打开的浏览器页面，使用页面内容；否则使用 URL
            html_content = None
            if context.page is not None:
                try:
                    # 尝试获取当前页面的 HTML 内容
                    await context.switch_to_latest_page()
                    current_url = context.page.url
                    # 如果当前页面的 URL 与目标 URL 匹配，使用页面内容
                    if url in current_url or current_url in url:
                        html_content = await context.page.content()
                        await context.send_progress(f"使用已打开的浏览器页面内容", "info")
                except Exception as e:
                    # 如果获取失败，继续使用 URL
                    await context.send_progress(f"无法获取浏览器页面内容，将直接访问 URL", "info")
            
            # 构建 LLM 配置
            llm_config = {
                "max_tokens": 8192,
            }
            
            if llm_provider == 'ollama':
                llm_config["model"] = f"ollama/{llm_model}"
                llm_config["format"] = "json"  # Ollama 支持 format 参数
            elif llm_provider in ['openai', 'zhipu', 'deepseek', 'custom']:
                # OpenAI 兼容的 API - ScrapeGraphAI 需要 openai/ 前缀
                if not api_key:
                    return ModuleResult(success=False, error=f"使用 {llm_provider} 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"openai/{llm_model}"  # 使用 openai/ 前缀
                # 如果提供了自定义 API URL，使用它
                if api_url:
                    # ScrapeGraphAI 会自动添加 /chat/completions，所以如果 URL 已包含，需要去掉
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'groq':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Groq 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"groq/{llm_model}"
                if api_url:
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'gemini':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Gemini 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"gemini/{llm_model}"
                if api_url:
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'azure':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Azure 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"azure/{llm_model}"
                # Azure 可能需要额外配置
                azure_endpoint = context.resolve_value(config.get('azureEndpoint', ''))
                if azure_endpoint:
                    llm_config["azure_endpoint"] = azure_endpoint
            
            # 构建完整配置
            graph_config = {
                "llm": llm_config,
                "verbose": config.get('verbose', False),
                "headless": config.get('headless', True),
            }
            
            # 发送进度日志
            await context.send_progress(f"正在使用 AI 智能爬虫提取数据...", "info")
            await context.send_progress(f"LLM: {llm_provider}/{llm_model}", "info")
            await context.send_progress(f"URL: {url}", "info")
            
            # 等待页面加载
            if wait_time > 0:
                await context.send_progress(f"⏳ 等待页面加载 {wait_time} 秒...", "info")
                import asyncio
                await asyncio.sleep(wait_time)
            
            # 使用 HTML 内容或 URL 作为数据源
            source = html_content if html_content else url
            
            # 创建智能爬虫
            smart_scraper = SmartScraperGraph(
                prompt=prompt,
                source=source,
                config=graph_config
            )
            
            # 执行爬取（nest_asyncio 允许在已有事件循环中运行）
            result = smart_scraper.run()
            
            # 保存结果到变量
            context.set_variable(variable_name, result)
            
            # 格式化结果用于显示
            result_str = json.dumps(result, ensure_ascii=False, indent=2)
            if len(result_str) > 500:
                result_preview = result_str[:500] + "..."
            else:
                result_preview = result_str
            
            return ModuleResult(
                success=True,
                message=f"AI 智能爬虫成功提取数据，已保存到变量 {variable_name}",
                data=result_preview
            )
        
        except Exception as e:
            error_msg = str(e)
            # 提供更友好的错误提示
            if "ollama" in error_msg.lower():
                error_msg += "\n提示：请确保 Ollama 已安装并运行，且已下载对应模型"
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                error_msg += "\n提示：请检查 API Key 是否正确"
            
            return ModuleResult(success=False, error=f"AI 智能爬虫失败: {error_msg}")


@register_executor
class AIElementSelectorExecutor(ModuleExecutor):
    """AI智能元素选择器模块执行器
    
    使用 AI 能力，通过自然语言描述来获取元素的 Selector。
    即使网页结构变化，也能准确找到元素。
    """
    
    @property
    def module_type(self) -> str:
        return "ai_element_selector"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            # 检查是否安装了 scrapegraphai
            try:
                from scrapegraphai.graphs import SmartScraperGraph
            except ImportError:
                return ModuleResult(
                    success=False, 
                    error="未安装 scrapegraphai 库。请运行: pip install scrapegraphai"
                )
            
            import json  # 移到顶部，避免作用域问题
            
            # 获取配置
            url = context.resolve_value(config.get('url', ''))
            element_description = context.resolve_value(config.get('elementDescription', ''))
            variable_name = config.get('variableName', '')
            wait_time = config.get('waitTime', 3)  # 默认等待3秒
            
            # LLM 配置
            llm_provider = context.resolve_value(config.get('llmProvider', 'ollama'))
            api_url = context.resolve_value(config.get('apiUrl', ''))
            llm_model = context.resolve_value(config.get('llmModel', 'llama3.2'))
            api_key = context.resolve_value(config.get('apiKey', ''))
            
            # 参数验证
            if not url:
                return ModuleResult(success=False, error="URL 不能为空")
            
            if not element_description:
                return ModuleResult(success=False, error="元素描述不能为空")
            
            if not variable_name:
                return ModuleResult(success=False, error="变量名不能为空")
            
            # 构建 LLM 配置
            llm_config = {
                "max_tokens": 8192,
            }
            
            if llm_provider == 'ollama':
                llm_config["model"] = f"ollama/{llm_model}"
                llm_config["format"] = "json"  # Ollama 支持 format 参数
            elif llm_provider in ['openai', 'zhipu', 'deepseek', 'custom']:
                # OpenAI 兼容的 API - ScrapeGraphAI 需要 openai/ 前缀
                if not api_key:
                    return ModuleResult(success=False, error=f"使用 {llm_provider} 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"openai/{llm_model}"  # 使用 openai/ 前缀
                # 如果提供了自定义 API URL，使用它
                if api_url:
                    # ScrapeGraphAI 会自动添加 /chat/completions，所以如果 URL 已包含，需要去掉
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'groq':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Groq 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"groq/{llm_model}"
                if api_url:
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'gemini':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Gemini 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"gemini/{llm_model}"
                if api_url:
                    if api_url.endswith('/chat/completions'):
                        api_url = api_url.rsplit('/chat/completions', 1)[0]
                    llm_config["base_url"] = api_url
            elif llm_provider == 'azure':
                if not api_key:
                    return ModuleResult(success=False, error="使用 Azure 需要提供 API Key")
                llm_config["api_key"] = api_key
                llm_config["model"] = f"azure/{llm_model}"
                azure_endpoint = context.resolve_value(config.get('azureEndpoint', ''))
                if azure_endpoint:
                    llm_config["azure_endpoint"] = azure_endpoint
            
            # 构建完整配置
            graph_config = {
                "llm": llm_config,
                "verbose": config.get('verbose', False),
                "headless": True,
            }
            
            # 构建提示词，要求返回 CSS 选择器
            prompt = f"""
请分析这个网页，找到符合以下描述的元素：{element_description}

请返回一个 JSON 对象，包含以下字段：
- selector: 该元素的 CSS 选择器（尽可能简洁且唯一）
- description: 对找到的元素的简短描述
- confidence: 置信度（0-100）

如果找到多个匹配的元素，返回最可能的那个。
"""
            
            # 发送进度日志
            await context.send_progress(f"正在使用 AI 智能查找元素...", "info")
            await context.send_progress(f"URL: {url}", "info")
            await context.send_progress(f"元素描述: {element_description}", "info")
            
            # 等待页面加载
            if wait_time > 0:
                await context.send_progress(f"⏳ 等待页面加载 {wait_time} 秒...", "info")
                import asyncio
                await asyncio.sleep(wait_time)
            
            # 创建智能爬虫 - 使用 URL
            smart_scraper = SmartScraperGraph(
                prompt=prompt,
                source=url,  # 使用 URL
                config=graph_config
            )
            
            # 执行查找（nest_asyncio 允许在已有事件循环中运行）
            result = smart_scraper.run()
            
            # 如果开启详细日志，显示原始返回结果
            if config.get('verbose', False):
                await context.send_progress(f"📊 AI原始返回: {json.dumps(result, ensure_ascii=False)}", "info")
            
            # 提取选择器
            selector = None
            confidence = 0
            description = ""
            
            # ScrapeGraphAI 可能返回不同的结构
            if isinstance(result, dict):
                # 尝试从 content 字段获取（新版本格式）
                if 'content' in result and isinstance(result['content'], dict):
                    content = result['content']
                    selector = content.get('selector')
                    confidence = content.get('confidence', 0)
                    description = content.get('description', '')
                # 或者直接从顶层获取（旧版本格式）
                else:
                    selector = result.get('selector')
                    confidence = result.get('confidence', 0)
                    description = result.get('description', '')
            elif isinstance(result, str):
                selector = result
                confidence = 50
                description = "AI 返回的选择器"
            
            # 检查是否返回了 NA（表示未找到）
            if not selector or selector == 'NA':
                return ModuleResult(
                    success=False,
                    error=f"AI 未能找到匹配的元素。\n原因：ScrapeGraphAI 获取不到网页内容（可能是反爬、加载超时或 JS 渲染问题）\n返回结果: {json.dumps(result, ensure_ascii=False)}\n\n💡 建议：使用传统的'获取元素列表'等模块，或使用浏览器开发者工具（F12）手动获取选择器"
                )
            
            # 检查描述中是否提到"内容为空"
            if description and ('内容为空' in description or '无法进行实际分析' in description or '无法进行具体分析' in description):
                await context.send_progress(f"⚠️ 警告：AI 提示网站内容为空，返回的选择器可能不准确", "warning")
            
            # 保存选择器到变量
            context.set_variable(variable_name, selector)
            
            return ModuleResult(
                success=True,
                message=f"AI 成功找到元素选择器: {selector}\n描述: {description}\n置信度: {confidence}%",
                data=selector
            )
        
        except Exception as e:
            error_msg = str(e)
            if "ollama" in error_msg.lower():
                error_msg += "\n提示：请确保 Ollama 已安装并运行，且已下载对应模型"
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                error_msg += "\n提示：请检查 API Key 是否正确"
            
            return ModuleResult(success=False, error=f"AI 智能元素选择失败: {error_msg}")
