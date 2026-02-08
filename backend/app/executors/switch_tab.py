"""
标签页切换模块
支持多种标签页切换模式
"""
from typing import Any, Dict
from .base import ModuleExecutor, ModuleResult, ExecutionContext, register_executor


@register_executor
class SwitchTabExecutor(ModuleExecutor):
    """标签页切换执行器"""
    
    @property
    def module_type(self) -> str:
        """模块类型"""
        return "switch_tab"
    
    async def execute(self, config: Dict[str, Any], context: ExecutionContext) -> ModuleResult:
        """执行标签页切换
        
        Args:
            config: 配置参数
                - switchMode: 切换模式 (index/title/url/next/prev/first/last)
                - tabIndex: 标签页索引（switchMode=index时使用）
                - tabTitle: 标签页标题（switchMode=title时使用）
                - tabUrl: 标签页URL（switchMode=url时使用）
                - matchMode: 匹配模式 (exact/contains/startswith/endswith/regex)
                - saveIndexVariable: 保存切换后的标签页索引到变量
                - saveTitleVariable: 保存切换后的标签页标题到变量
                - saveUrlVariable: 保存切换后的标签页URL到变量
            context: 执行上下文
        
        Returns:
            ModuleResult: 执行结果
        """
        try:
            # 获取浏览器上下文
            browser_context = context.browser_context
            if browser_context is None:
                return ModuleResult(
                    success=False,
                    error="浏览器未启动，请先使用'打开网页'模块启动浏览器"
                )
            
            # 获取所有标签页
            all_pages = browser_context.pages
            if not all_pages:
                return ModuleResult(
                    success=False,
                    error="没有可用的标签页"
                )
            
            # 获取当前标签页索引
            current_page = await context.get_current_frame()
            current_index = -1
            if current_page:
                try:
                    current_index = all_pages.index(current_page)
                except ValueError:
                    current_index = -1
            
            # 获取配置参数
            switch_mode = context.resolve_value(config.get('switchMode', 'index'))
            match_mode = context.resolve_value(config.get('matchMode', 'exact'))
            save_index_var = config.get('saveIndexVariable', '')
            save_title_var = config.get('saveTitleVariable', '')
            save_url_var = config.get('saveUrlVariable', '')
            
            target_page = None
            target_index = -1
            
            # 根据切换模式选择目标标签页
            if switch_mode == 'index':
                # 按索引切换
                tab_index = context.resolve_value(config.get('tabIndex', 0))
                try:
                    tab_index = int(tab_index)
                except (ValueError, TypeError):
                    return ModuleResult(
                        success=False,
                        error=f"标签页索引必须是数字: {tab_index}"
                    )
                
                if tab_index < 0 or tab_index >= len(all_pages):
                    return ModuleResult(
                        success=False,
                        error=f"标签页索引超出范围: {tab_index}（共有 {len(all_pages)} 个标签页，索引范围: 0-{len(all_pages)-1}）"
                    )
                
                target_page = all_pages[tab_index]
                target_index = tab_index
            
            elif switch_mode == 'title':
                # 按标题切换
                tab_title = context.resolve_value(config.get('tabTitle', ''))
                if not tab_title:
                    return ModuleResult(
                        success=False,
                        error="请输入标签页标题"
                    )
                
                # 查找匹配的标签页
                for idx, page in enumerate(all_pages):
                    page_title = await page.title()
                    if self._match_string(page_title, tab_title, match_mode):
                        target_page = page
                        target_index = idx
                        break
                
                if target_page is None:
                    return ModuleResult(
                        success=False,
                        error=f"未找到标题匹配的标签页: {tab_title}"
                    )
            
            elif switch_mode == 'url':
                # 按URL切换
                tab_url = context.resolve_value(config.get('tabUrl', ''))
                if not tab_url:
                    return ModuleResult(
                        success=False,
                        error="请输入标签页URL"
                    )
                
                # 查找匹配的标签页
                for idx, page in enumerate(all_pages):
                    page_url = page.url
                    if self._match_string(page_url, tab_url, match_mode):
                        target_page = page
                        target_index = idx
                        break
                
                if target_page is None:
                    return ModuleResult(
                        success=False,
                        error=f"未找到URL匹配的标签页: {tab_url}"
                    )
            
            elif switch_mode == 'next':
                # 切换到下一个标签页
                if current_index == -1:
                    target_index = 0
                else:
                    target_index = (current_index + 1) % len(all_pages)
                target_page = all_pages[target_index]
            
            elif switch_mode == 'prev':
                # 切换到上一个标签页
                if current_index == -1:
                    target_index = len(all_pages) - 1
                else:
                    target_index = (current_index - 1) % len(all_pages)
                target_page = all_pages[target_index]
            
            elif switch_mode == 'first':
                # 切换到第一个标签页
                target_page = all_pages[0]
                target_index = 0
            
            elif switch_mode == 'last':
                # 切换到最后一个标签页
                target_page = all_pages[-1]
                target_index = len(all_pages) - 1
            
            else:
                return ModuleResult(
                    success=False,
                    error=f"不支持的切换模式: {switch_mode}"
                )
            
            # 切换到目标标签页
            if target_page:
                context.page = target_page
                await target_page.bring_to_front()
                
                # 获取标签页信息
                page_title = await target_page.title()
                page_url = target_page.url
                
                # 保存到变量
                if save_index_var:
                    context.set_variable(save_index_var, target_index)
                if save_title_var:
                    context.set_variable(save_title_var, page_title)
                if save_url_var:
                    context.set_variable(save_url_var, page_url)
                
                return ModuleResult(
                    success=True,
                    message=f"已切换到标签页 {target_index}: {page_title}",
                    data={
                        'index': target_index,
                        'title': page_title,
                        'url': page_url,
                        'total_tabs': len(all_pages)
                    }
                )
            
            return ModuleResult(
                success=False,
                error="未找到目标标签页"
            )
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[SwitchTab] 切换标签页失败: {e}\n{error_details}")
            return ModuleResult(
                success=False,
                error=f"切换标签页失败: {str(e)}"
            )
    
    def _match_string(self, text: str, pattern: str, mode: str) -> bool:
        """字符串匹配
        
        Args:
            text: 要匹配的文本
            pattern: 匹配模式
            mode: 匹配模式 (exact/contains/startswith/endswith/regex)
        
        Returns:
            bool: 是否匹配
        """
        if mode == 'exact':
            return text == pattern
        elif mode == 'contains':
            return pattern in text
        elif mode == 'startswith':
            return text.startswith(pattern)
        elif mode == 'endswith':
            return text.endswith(pattern)
        elif mode == 'regex':
            import re
            try:
                return bool(re.search(pattern, text))
            except re.error:
                return False
        else:
            return text == pattern
