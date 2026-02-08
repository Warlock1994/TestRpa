"""Firecrawl AI 爬虫模块执行器 - 纯 Python 实现，无需外部服务"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import html2text
import re
from urllib.parse import urljoin, urlparse
from typing import List, Set, Dict
import asyncio


@register_executor
class FirecrawlScrapeExecutor(ModuleExecutor):
    """Firecrawl AI 单页数据抓取
    
    使用 Playwright + BeautifulSoup 智能提取单个网页的结构化数据。
    支持 Markdown、HTML、纯文本等多种格式。
    """
    
    @property
    def module_type(self) -> str:
        return "firecrawl_scrape"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            # 获取配置
            url = context.resolve_value(config.get('url', ''))
            variable_name = config.get('variableName', 'scrape_result')
            
            # 抓取选项
            formats = config.get('formats', ['markdown'])
            only_main_content = config.get('onlyMainContent', True)
            include_tags = context.resolve_value(config.get('includeTags', ''))
            exclude_tags = context.resolve_value(config.get('excludeTags', ''))
            wait_for = context.resolve_value(config.get('waitFor', ''))
            timeout = config.get('timeout', 30000)
            
            # 参数验证
            if not url:
                return ModuleResult(success=False, error="URL 不能为空")
            
            # 发送进度日志
            await context.send_progress(f"🔥 正在抓取页面: {url}", "info")
            await context.send_progress(f"格式: {', '.join(formats)}", "info")
            
            # 使用 Playwright 获取页面内容
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # 访问页面
                    await page.goto(url, timeout=timeout, wait_until='networkidle')
                    
                    # 如果指定了等待选择器
                    if wait_for:
                        try:
                            await page.wait_for_selector(wait_for, timeout=5000)
                        except:
                            pass
                    
                    # 获取 HTML 内容
                    html_content = await page.content()
                    
                    # 使用 BeautifulSoup 解析
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(['script', 'style', 'noscript']):
                        script.decompose()
                    
                    # 如果指定了排除标签
                    if exclude_tags:
                        exclude_list = [tag.strip() for tag in exclude_tags.split(',') if tag.strip()]
                        for tag in exclude_list:
                            for element in soup.find_all(tag):
                                element.decompose()
                    
                    # 如果只提取主内容
                    if only_main_content:
                        # 尝试找到主内容区域
                        main_content = (
                            soup.find('main') or 
                            soup.find('article') or 
                            soup.find('div', {'id': re.compile(r'content|main', re.I)}) or
                            soup.find('div', {'class': re.compile(r'content|main', re.I)}) or
                            soup.body
                        )
                        if main_content:
                            soup = BeautifulSoup(str(main_content), 'html.parser')
                    
                    # 如果指定了包含标签
                    if include_tags:
                        include_list = [tag.strip() for tag in include_tags.split(',') if tag.strip()]
                        filtered_soup = BeautifulSoup('', 'html.parser')
                        for tag in include_list:
                            for element in soup.find_all(tag):
                                filtered_soup.append(element)
                        soup = filtered_soup
                    
                    # 构建结果
                    result = {
                        'url': url,
                        'title': soup.title.string if soup.title else '',
                    }
                    
                    # 根据格式生成内容
                    if 'markdown' in formats:
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        h.ignore_images = False
                        h.body_width = 0
                        result['markdown'] = h.handle(str(soup))
                    
                    if 'html' in formats:
                        result['html'] = str(soup)
                    
                    if 'text' in formats:
                        result['text'] = soup.get_text(separator='\n', strip=True)
                    
                    # 提取元数据
                    result['metadata'] = {
                        'title': soup.title.string if soup.title else '',
                        'description': '',
                        'language': soup.html.get('lang', '') if soup.html else '',
                    }
                    
                    # 提取 meta 标签
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc:
                        result['metadata']['description'] = meta_desc.get('content', '')
                    
                finally:
                    await browser.close()
            
            # 保存结果到变量
            context.set_variable(variable_name, result)
            
            # 格式化结果用于显示
            result_preview = ""
            if 'markdown' in result:
                markdown_content = result['markdown']
                if len(markdown_content) > 300:
                    result_preview = markdown_content[:300] + "..."
                else:
                    result_preview = markdown_content
            elif 'html' in result:
                html_content = result['html']
                if len(html_content) > 300:
                    result_preview = html_content[:300] + "..."
                else:
                    result_preview = html_content
            else:
                result_preview = json.dumps(result, ensure_ascii=False, indent=2)[:300] + "..."
            
            return ModuleResult(
                success=True,
                message=f"✅ 成功抓取页面数据，已保存到变量 {variable_name}\n\n预览:\n{result_preview}",
                data=result
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"抓取失败: {str(e)}")


@register_executor
class FirecrawlMapExecutor(ModuleExecutor):
    """Firecrawl AI 网站链接抓取
    
    使用 Playwright 智能发现网站的所有链接。
    可以用于构建网站地图或批量抓取。
    """
    
    @property
    def module_type(self) -> str:
        return "firecrawl_map"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            # 获取配置
            url = context.resolve_value(config.get('url', ''))
            variable_name = config.get('variableName', 'map_result')
            
            # Map 选项
            search = context.resolve_value(config.get('search', ''))
            include_subdomains = config.get('includeSubdomains', False)
            limit = config.get('limit', 5000)
            
            # 参数验证
            if not url:
                return ModuleResult(success=False, error="URL 不能为空")
            
            # 发送进度日志
            await context.send_progress(f"🗺️ 正在抓取网站链接: {url}", "info")
            if search:
                await context.send_progress(f"搜索关键词: {search}", "info")
            
            # 解析基础 URL
            base_domain = urlparse(url).netloc
            
            # 使用 Playwright 获取页面并提取链接
            links_found: Set[str] = set()
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    await page.goto(url, timeout=30000, wait_until='networkidle')
                    
                    # 获取所有链接
                    all_links = await page.eval_on_selector_all(
                        'a[href]',
                        '(elements) => elements.map(e => e.href)'
                    )
                    
                    # 过滤链接
                    for link in all_links:
                        # 转换为绝对 URL
                        absolute_url = urljoin(url, link)
                        parsed = urlparse(absolute_url)
                        
                        # 检查是否是 HTTP/HTTPS
                        if parsed.scheme not in ['http', 'https']:
                            continue
                        
                        # 检查域名
                        if not include_subdomains:
                            if parsed.netloc != base_domain:
                                continue
                        else:
                            if not parsed.netloc.endswith(base_domain):
                                continue
                        
                        # 如果有搜索关键词，过滤
                        if search and search.lower() not in absolute_url.lower():
                            continue
                        
                        links_found.add(absolute_url)
                        
                        # 达到限制
                        if len(links_found) >= limit:
                            break
                    
                finally:
                    await browser.close()
            
            # 转换为列表
            links = sorted(list(links_found))
            
            # 保存结果到变量
            context.set_variable(variable_name, links)
            
            # 格式化结果用于显示
            links_preview = "\n".join(links[:10])
            if len(links) > 10:
                links_preview += f"\n... 还有 {len(links) - 10} 个链接"
            
            return ModuleResult(
                success=True,
                message=f"✅ 成功抓取 {len(links)} 个链接，已保存到变量 {variable_name}\n\n链接预览:\n{links_preview}",
                data=links
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"链接抓取失败: {str(e)}")


@register_executor
class FirecrawlCrawlExecutor(ModuleExecutor):
    """Firecrawl AI 全站数据抓取
    
    使用 Playwright 智能爬取整个网站的数据。
    支持深度爬取、智能过滤、并发控制等高级功能。
    """
    
    @property
    def module_type(self) -> str:
        return "firecrawl_crawl"
    
    async def _scrape_page(self, url: str, formats: List[str], only_main_content: bool, browser) -> Dict:
        """抓取单个页面"""
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until='networkidle')
            html_content = await page.content()
            
            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(['script', 'style', 'noscript']):
                script.decompose()
            
            # 如果只提取主内容
            if only_main_content:
                main_content = (
                    soup.find('main') or 
                    soup.find('article') or 
                    soup.find('div', {'id': re.compile(r'content|main', re.I)}) or
                    soup.find('div', {'class': re.compile(r'content|main', re.I)}) or
                    soup.body
                )
                if main_content:
                    soup = BeautifulSoup(str(main_content), 'html.parser')
            
            # 构建结果
            result = {
                'url': url,
                'title': soup.title.string if soup.title else '',
            }
            
            # 根据格式生成内容
            if 'markdown' in formats:
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                result['markdown'] = h.handle(str(soup))
            
            if 'html' in formats:
                result['html'] = str(soup)
            
            if 'text' in formats:
                result['text'] = soup.get_text(separator='\n', strip=True)
            
            return result
        finally:
            await page.close()
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            # 获取配置
            url = context.resolve_value(config.get('url', ''))
            variable_name = config.get('variableName', 'crawl_result')
            
            # Crawl 选项
            max_depth = config.get('maxDepth', 2)
            limit = config.get('limit', 100)
            include_paths = context.resolve_value(config.get('includePaths', ''))
            exclude_paths = context.resolve_value(config.get('excludePaths', ''))
            allow_external_links = config.get('allowExternalLinks', False)
            
            # 抓取格式
            formats = config.get('formats', ['markdown'])
            only_main_content = config.get('onlyMainContent', True)
            
            # 参数验证
            if not url:
                return ModuleResult(success=False, error="URL 不能为空")
            
            # 发送进度日志
            await context.send_progress(f"🕷️ 正在爬取整个网站: {url}", "info")
            await context.send_progress(f"最大深度: {max_depth}, 页面限制: {limit}", "info")
            
            # 解析基础 URL
            base_domain = urlparse(url).netloc
            base_url = f"{urlparse(url).scheme}://{base_domain}"
            
            # 准备过滤规则
            include_patterns = []
            if include_paths:
                include_patterns = [p.strip() for p in include_paths.split(',') if p.strip()]
            
            exclude_patterns = []
            if exclude_paths:
                exclude_patterns = [p.strip() for p in exclude_paths.split(',') if p.strip()]
            
            # 爬取状态
            visited: Set[str] = set()
            to_visit: List[tuple] = [(url, 0)]  # (url, depth)
            results: List[Dict] = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                try:
                    while to_visit and len(results) < limit:
                        current_url, depth = to_visit.pop(0)
                        
                        # 跳过已访问的
                        if current_url in visited:
                            continue
                        
                        visited.add(current_url)
                        
                        # 检查深度
                        if depth > max_depth:
                            continue
                        
                        # 检查包含/排除规则
                        if include_patterns:
                            if not any(pattern in current_url for pattern in include_patterns):
                                continue
                        
                        if exclude_patterns:
                            if any(pattern in current_url for pattern in exclude_patterns):
                                continue
                        
                        await context.send_progress(f"⏳ 正在爬取 ({len(results)+1}/{limit}): {current_url}", "info")
                        
                        try:
                            # 抓取页面
                            page_data = await self._scrape_page(current_url, formats, only_main_content, browser)
                            results.append(page_data)
                            
                            # 如果还没达到最大深度，提取链接
                            if depth < max_depth and len(results) < limit:
                                page = await browser.new_page()
                                try:
                                    await page.goto(current_url, timeout=30000)
                                    links = await page.eval_on_selector_all(
                                        'a[href]',
                                        '(elements) => elements.map(e => e.href)'
                                    )
                                    
                                    for link in links:
                                        absolute_url = urljoin(current_url, link)
                                        parsed = urlparse(absolute_url)
                                        
                                        # 检查是否是 HTTP/HTTPS
                                        if parsed.scheme not in ['http', 'https']:
                                            continue
                                        
                                        # 检查域名
                                        if not allow_external_links:
                                            if parsed.netloc != base_domain:
                                                continue
                                        
                                        # 添加到待访问列表
                                        if absolute_url not in visited:
                                            to_visit.append((absolute_url, depth + 1))
                                
                                finally:
                                    await page.close()
                        
                        except Exception as e:
                            await context.send_progress(f"⚠️ 跳过页面 {current_url}: {str(e)}", "warning")
                            continue
                
                finally:
                    await browser.close()
            
            # 保存结果到变量
            context.set_variable(variable_name, results)
            
            # 格式化结果用于显示
            result_summary = f"成功爬取 {len(results)} 个页面"
            
            if len(results) > 0:
                first_page = results[0]
                if 'markdown' in first_page:
                    preview = first_page['markdown'][:200] + "..."
                    result_summary += f"\n\n第一个页面预览:\n{preview}"
            
            return ModuleResult(
                success=True,
                message=f"✅ {result_summary}，已保存到变量 {variable_name}",
                data=results
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"全站爬取失败: {str(e)}")
