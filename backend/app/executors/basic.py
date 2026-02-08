"""基础模块执行器实现 - 异步版本"""
import asyncio
import time
from pathlib import Path

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)
from .type_utils import to_int, to_float


# 读取篡改猴脚本
def load_userscript():
    """加载篡改猴脚本（Alt+X 激活元素选择器）"""
    script_path = Path(__file__).parent.parent.parent / "browser_plugin" / "智能元素定位助手.user.js"
    if script_path.exists():
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 移除 UserScript 头部注释
                lines = content.split('\n')
                script_lines = []
                in_header = False
                for line in lines:
                    if line.strip().startswith('// ==UserScript=='):
                        in_header = True
                        continue
                    if line.strip().startswith('// ==/UserScript=='):
                        in_header = False
                        continue
                    if not in_header:
                        script_lines.append(line)
                return '\n'.join(script_lines)
        except Exception as e:
            print(f"[OpenPage] 加载篡改猴脚本失败: {e}")
            return None
    return None

# 篡改猴脚本（Alt+X 激活元素选择器）
USERSCRIPT = load_userscript()


async def inject_userscript_to_page(page):
    """注入篡改猴脚本到页面"""
    if USERSCRIPT:
        try:
            await page.add_init_script(USERSCRIPT)
            print(f"[OpenPage] 已注入篡改猴脚本（Alt+X 激活元素选择器）")
        except Exception as e:
            print(f"[OpenPage] 注入篡改猴脚本失败: {e}")


async def inject_on_navigation(page):
    """页面导航时重新注入脚本"""
    if USERSCRIPT:
        try:
            await page.evaluate(USERSCRIPT)
            print(f"[OpenPage] 页面导航后重新注入篡改猴脚本")
        except Exception as e:
            print(f"[OpenPage] 页面导航后注入失败: {e}")


@register_executor
class GroupExecutor(ModuleExecutor):
    """备注分组模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "group"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        return ModuleResult(success=True, message="备注分组（跳过）")


@register_executor
class OpenPageExecutor(ModuleExecutor):
    """打开网页模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "open_page"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        url = context.resolve_value(config.get('url', ''))
        wait_until = context.resolve_value(config.get('waitUntil', 'load'))  # 支持变量引用
        open_mode = context.resolve_value(config.get('openMode', 'new_tab'))  # 打开模式：new_tab 或 current_tab
        
        if not url:
            return ModuleResult(success=False, error="URL不能为空")
        
        try:
            # 如果没有浏览器实例，创建一个
            if context.browser_context is None:
                p = context._playwright
                if p is None:
                    return ModuleResult(success=False, error="Playwright未初始化")
                
                user_data_dir = context._user_data_dir
                print(f"[OpenPage] user_data_dir={user_data_dir}")
                
                # 获取浏览器配置
                browser_config = context.browser_config or {}
                browser_type = browser_config.get('type', 'msedge')
                executable_path = browser_config.get('executablePath', '')
                fullscreen = browser_config.get('fullscreen', False)
                launch_args_str = browser_config.get('launchArgs', '')
                
                # 解析启动参数（每行一个参数）
                if launch_args_str:
                    # 用户自定义的启动参数
                    launch_args_list = [arg.strip() for arg in launch_args_str.split('\n') if arg.strip()]
                    print(f"[OpenPage] 使用自定义启动参数: {len(launch_args_list)} 个")
                else:
                    # 默认启动参数
                    launch_args_list = [
                        '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                        '--start-maximized',  # 始终最大化启动
                        '--ignore-certificate-errors',  # 忽略证书错误
                        '--ignore-ssl-errors',  # 忽略 SSL 错误
                        '--disable-features=IsolateOrigins,site-per-process',  # 禁用站点隔离
                        '--allow-running-insecure-content',  # 允许运行不安全内容
                        '--disable-infobars',  # 禁用信息栏
                        '--disable-notifications',  # 禁用通知
                    ]
                    print(f"[OpenPage] 使用默认启动参数: {len(launch_args_list)} 个")
                
                # 根据浏览器类型选择 Playwright 浏览器引擎
                if browser_type == 'firefox':
                    browser_engine = p.firefox
                else:
                    browser_engine = p.chromium
                
                # 确定 channel 参数
                # 注意：executable_path 和 channel 是互斥的
                if executable_path:
                    channel = None  # 使用自定义路径时不设置 channel
                elif browser_type in ('msedge', 'chrome'):
                    channel = browser_type
                else:
                    channel = None
                
                print(f"[OpenPage] 浏览器配置: type={browser_type}, channel={channel}, executablePath={executable_path or '默认'}, fullscreen={fullscreen}")
                
                # 当指定了自定义浏览器路径时，使用非持久化模式
                # 因为Playwright的launch_persistent_context不支持executable_path参数
                if executable_path:
                    print(f"[OpenPage] 使用自定义浏览器路径: {executable_path}")
                    print(f"[OpenPage] ⚠️ 注意：自定义浏览器路径不支持持久化，登录状态不会保存")
                    print(f"[OpenPage] 💡 建议：如需持久化登录状态，请使用默认浏览器（不指定路径）")
                    
                    # 使用普通模式启动（非持久化）
                    launch_args = {
                        'headless': context.headless,
                        'executable_path': executable_path,
                        'args': launch_args_list,
                    }
                    
                    context.browser = await browser_engine.launch(**launch_args)
                    context.browser_context = await context.browser.new_context(
                        no_viewport=True,
                        ignore_https_errors=True,
                        permissions=['geolocation', 'notifications', 'camera', 'microphone'],
                    )
                    
                    # 授予所有权限
                    try:
                        await context.browser_context.grant_permissions(
                            ['geolocation', 'notifications', 'camera', 'microphone', 'clipboard-read', 'clipboard-write'],
                            origin='*'
                        )
                    except Exception as e:
                        print(f"[OpenPage] 授予权限时出现警告: {e}")
                    
                    context.page = await context.browser_context.new_page()
                    
                    # 注入篡改猴脚本
                    await inject_userscript_to_page(context.page)
                    
                    # 监听页面导航，重新注入脚本
                    context.page.on("load", lambda: asyncio.create_task(inject_on_navigation(context.page)))
                    
                    # 监听新页面并自动注入
                    def on_page(new_page):
                        asyncio.create_task(inject_userscript_to_page(new_page))
                        new_page.on("load", lambda: asyncio.create_task(inject_on_navigation(new_page)))
                    context.browser_context.on("page", on_page)
                elif user_data_dir:
                    from pathlib import Path
                    import psutil
                    import time
                    
                    # 为不同浏览器类型使用不同的数据目录，避免冲突
                    user_data_path = Path(user_data_dir) / browser_type
                    user_data_path.mkdir(parents=True, exist_ok=True)
                    actual_user_data_dir = str(user_data_path)
                    
                    # 清理所有可能的锁文件
                    lock_files = [
                        "SingletonLock",
                        "lockfile", 
                        ".lock",
                        "Singleton",
                        "SingletonCookie",
                        "SingletonSocket"
                    ]
                    
                    cleaned_locks = []
                    for lock_name in lock_files:
                        lock_file = user_data_path / lock_name
                        if lock_file.exists():
                            try:
                                lock_file.unlink()
                                cleaned_locks.append(lock_name)
                            except Exception as e:
                                print(f"[OpenPage] 清理锁文件 {lock_name} 失败: {e}")
                    
                    if cleaned_locks:
                        print(f"[OpenPage] 已清理 {len(cleaned_locks)} 个锁文件: {', '.join(cleaned_locks)}")
                    
                    # 检查并终止占用该目录的浏览器进程
                    browser_process_names = {
                        'chromium': ['chrome.exe', 'chromium.exe'],
                        'chrome': ['chrome.exe'],
                        'msedge': ['msedge.exe'],
                        'firefox': ['firefox.exe']
                    }
                    
                    process_names = browser_process_names.get(browser_type, [])
                    killed_processes = []
                    
                    try:
                        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                            try:
                                if proc.info['name'] and proc.info['name'].lower() in [p.lower() for p in process_names]:
                                    # 检查进程是否使用了这个user_data_dir
                                    cmdline = proc.info.get('cmdline', [])
                                    if cmdline and any(actual_user_data_dir in str(arg) for arg in cmdline):
                                        print(f"[OpenPage] 发现占用目录的进程: PID={proc.info['pid']}, Name={proc.info['name']}")
                                        proc.terminate()
                                        killed_processes.append(proc.info['pid'])
                            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                                pass
                        
                        # 等待进程终止
                        if killed_processes:
                            print(f"[OpenPage] 已终止 {len(killed_processes)} 个占用进程，等待清理...")
                            time.sleep(1)
                            
                            # 再次清理锁文件
                            for lock_name in lock_files:
                                lock_file = user_data_path / lock_name
                                if lock_file.exists():
                                    try:
                                        lock_file.unlink()
                                    except:
                                        pass
                    except Exception as e:
                        print(f"[OpenPage] 进程检查失败: {e}")
                    
                    # 无头模式下需要特殊处理启动参数
                    if context.headless:
                        print(f"[OpenPage] 无头模式下使用持久化上下文")
                        # 移除可能导致冲突的参数
                        headless_args = [arg for arg in launch_args_list if not any(x in arg for x in ['--start-maximized'])]
                        # 添加新的无头模式参数
                        headless_args.append('--headless=new')
                        launch_args_list = headless_args
                    
                    # 多次尝试启动持久化上下文
                    max_retries = 3
                    last_error = None
                    for attempt in range(max_retries):
                        try:
                            print(f"[OpenPage] 启动持久化浏览器上下文 (尝试 {attempt + 1}/{max_retries})...")
                            
                            # 构建启动参数
                            launch_args = {
                                'user_data_dir': actual_user_data_dir,
                                'headless': context.headless,
                                'args': launch_args_list,
                                'no_viewport': True,  # 使用 no_viewport 让页面自适应窗口大小
                                'ignore_https_errors': True,
                                # 自动授予所有权限，避免弹窗阻塞工作流
                                'permissions': ['geolocation', 'notifications', 'camera', 'microphone'],
                            }
                            if channel:
                                launch_args['channel'] = channel
                            
                            context.browser_context = await browser_engine.launch_persistent_context(**launch_args)
                            
                            # 授予所有权限，避免弹窗阻塞工作流
                            try:
                                await context.browser_context.grant_permissions(
                                    ['geolocation', 'notifications', 'camera', 'microphone', 'clipboard-read', 'clipboard-write'],
                                    origin='*'
                                )
                            except Exception as e:
                                print(f"[OpenPage] 授予权限时出现警告: {e}")
                            
                            # 只在第一次启动时关闭旧页面，后续打开网页时保留已有标签页
                            # 检查是否是第一次启动（通过检查 context.page 是否为 None）
                            is_first_launch = context.page is None
                            
                            if is_first_launch:
                                # 第一次启动：关闭所有历史页面
                                existing_pages = context.browser_context.pages[:]
                                for old_page in existing_pages:
                                    try:
                                        await old_page.close()
                                    except:
                                        pass
                                print(f"[OpenPage] 第一次启动，已清理 {len(existing_pages)} 个历史页面")
                            
                            # 创建新页面（新标签页）
                            context.page = await context.browser_context.new_page()
                            
                            # 注入篡改猴脚本
                            await inject_userscript_to_page(context.page)
                            
                            # 监听页面导航，重新注入脚本
                            context.page.on("load", lambda: asyncio.create_task(inject_on_navigation(context.page)))
                            
                            # 监听新页面并自动注入
                            def on_page(new_page):
                                asyncio.create_task(inject_userscript_to_page(new_page))
                                # 为新页面也监听导航事件
                                new_page.on("load", lambda: asyncio.create_task(inject_on_navigation(new_page)))
                            context.browser_context.on("page", on_page)
                            
                            if is_first_launch:
                                print(f"[OpenPage] 持久化浏览器上下文启动成功")
                            else:
                                print(f"[OpenPage] 在现有浏览器中创建新标签页")
                            break
                        except Exception as e:
                            last_error = e
                            error_msg = str(e)
                            print(f"[OpenPage] 持久化上下文启动失败 (尝试 {attempt + 1}): {e}")
                            
                            # 如果是用户数据目录被占用，尝试关闭 browser_context
                            if context.browser_context:
                                try:
                                    await context.browser_context.close()
                                except:
                                    pass
                                context.browser_context = None
                            
                            if lock_file.exists():
                                try:
                                    lock_file.unlink()
                                except:
                                    pass
                            await asyncio.sleep(0.5)
                    else:
                        return ModuleResult(
                            success=False, 
                            error=f"无法启动持久化浏览器: {last_error}"
                        )
                else:
                    print(f"[OpenPage] 使用普通模式启动浏览器")
                    
                    # 构建启动参数
                    launch_args = {'headless': context.headless}
                    if channel:
                        launch_args['channel'] = channel
                    if executable_path:
                        launch_args['executable_path'] = executable_path
                    
                    context.browser = await browser_engine.launch(**launch_args)
                    context.browser_context = await context.browser.new_context()
                    context.page = await context.browser_context.new_page()
                    
                    # 注入篡改猴脚本
                    await inject_userscript_to_page(context.page)
                    
                    # 监听页面导航，重新注入脚本
                    context.page.on("load", lambda: asyncio.create_task(inject_on_navigation(context.page)))
                    
                    # 监听新页面并自动注入
                    def on_page(new_page):
                        asyncio.create_task(inject_userscript_to_page(new_page))
                        # 为新页面也监听导航事件
                        new_page.on("load", lambda: asyncio.create_task(inject_on_navigation(new_page)))
                    context.browser_context.on("page", on_page)
            
            # 如果浏览器已经启动，根据打开模式决定是新建标签页还是复用当前标签页
            else:
                if open_mode == 'current_tab' and context.page is not None:
                    # 覆盖当前标签页模式：复用现有页面
                    print(f"[OpenPage] 在当前标签页中打开网页")
                else:
                    # 新建标签页模式：创建新标签页
                    context.page = await context.browser_context.new_page()
                    # 注入篡改猴脚本
                    await inject_userscript_to_page(context.page)
                    # 监听页面导航
                    context.page.on("load", lambda: asyncio.create_task(inject_on_navigation(context.page)))
                    print(f"[OpenPage] 在现有浏览器中创建新标签页")
            
            # 强制最大化窗口（使用 CDP）
            try:
                cdp = await context.page.context.new_cdp_session(context.page)
                
                # 先获取所有窗口
                windows = await cdp.send('Browser.getWindowForTarget')
                window_id = windows.get('windowId')
                
                if window_id:
                    # 使用获取到的窗口 ID
                    await cdp.send('Browser.setWindowBounds', {
                        'windowId': window_id,
                        'bounds': {'windowState': 'maximized'}
                    })
                    print(f"[OpenPage] 窗口已强制最大化 (windowId={window_id})")
                else:
                    print(f"[OpenPage] 无法获取窗口ID，尝试使用默认ID")
                    # 降级方案：尝试使用 windowId 1
                    await cdp.send('Browser.setWindowBounds', {
                        'windowId': 1,
                        'bounds': {'windowState': 'maximized'}
                    })
                    print(f"[OpenPage] 窗口已强制最大化 (使用默认ID)")
                    
            except Exception as e:
                print(f"[OpenPage] 窗口最大化失败: {e}")
            
            # 导航到目标URL
            await context.page.goto(url, wait_until=wait_until)
            
            # 确保页面获得焦点
            await context.page.bring_to_front()
            
            return ModuleResult(success=True, message=f"已打开网页: {url}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"打开网页失败: {str(e)}")


@register_executor
class ClickElementExecutor(ModuleExecutor):
    """点击元素模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "click_element"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        click_type = context.resolve_value(config.get('clickType', 'single'))  # 支持变量引用
        wait_for_selector_raw = config.get('waitForSelector', True)
        # 支持变量引用
        if isinstance(wait_for_selector_raw, str):
            wait_for_selector_raw = context.resolve_value(wait_for_selector_raw)
        wait_for_selector = wait_for_selector_raw in [True, 'true', 'True', '1', 1]
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            print(f"[ClickElement] 开始点击，selector: {selector}")
            print(f"[ClickElement] 当前在iframe中: {context._in_iframe}")
            
            await context.switch_to_latest_page()
            
            # 如果在iframe中，获取当前的frame
            current_page = await context.get_current_frame()
            if current_page is None:
                return ModuleResult(success=False, error="无法获取当前页面或frame")
            
            print(f"[ClickElement] 使用的page/frame: {current_page}")
            print(f"[ClickElement] page URL: {current_page.url if hasattr(current_page, 'url') else 'N/A'}")
            
            element = current_page.locator(selector).first
            
            if wait_for_selector:
                try:
                    print(f"[ClickElement] 等待元素attached...")
                    await element.wait_for(state='attached', timeout=timeout_ms)
                except Exception as e:
                    print(f"[ClickElement] wait_for失败: {e}，尝试wait_for_selector...")
                    await current_page.wait_for_selector(selector, state='visible', timeout=timeout_ms)
            
            print(f"[ClickElement] 执行点击...")
            if click_type == 'double':
                await element.dblclick()
            elif click_type == 'right':
                await element.click(button='right')
            else:
                await element.click()
            
            print(f"[ClickElement] 点击成功")
            return ModuleResult(success=True, message=f"已点击元素: {selector}")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"点击元素失败: {str(e)}")


@register_executor
class HoverElementExecutor(ModuleExecutor):
    """悬停元素模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "hover_element"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        hover_duration = to_int(config.get('hoverDuration', 500), 500, context)
        force_raw = config.get('force', False)
        # 支持变量引用
        if isinstance(force_raw, str):
            force_raw = context.resolve_value(force_raw)
        force = force_raw in [True, 'true', 'True', '1', 1]
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            # 如果在iframe中，获取当前的frame
            current_page = await context.get_current_frame()
            if current_page is None:
                return ModuleResult(success=False, error="无法获取当前页面或frame")
            
            element = current_page.locator(selector).first
            
            try:
                await element.wait_for(state='attached', timeout=timeout_ms)
            except:
                await current_page.wait_for_selector(selector, state='visible', timeout=timeout_ms)
            
            # 使用 force 参数来绕过遮挡检测
            await element.hover(force=force, timeout=timeout_ms)
            
            if hover_duration > 0:
                await asyncio.sleep(hover_duration / 1000)
            
            return ModuleResult(success=True, message=f"已悬停到元素: {selector}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"悬停元素失败: {str(e)}")


@register_executor
class InputTextExecutor(ModuleExecutor):
    """输入文本模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "input_text"
    
    async def _find_input_element(self, page, selector: str):
        """查找可输入的元素"""
        element = page.locator(selector).first
        
        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        is_contenteditable = await element.evaluate("el => el.isContentEditable")
        
        if tag_name in ['input', 'textarea', 'select'] or is_contenteditable:
            return element, 'direct'
        
        inner_input = element.locator('input, textarea').first
        if await inner_input.count() > 0:
            return inner_input, 'inner'
        
        inner_editable = element.locator('[contenteditable="true"]').first
        if await inner_editable.count() > 0:
            return inner_editable, 'contenteditable'
        
        return element, 'keyboard'
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        text = context.resolve_value(config.get('text', ''))
        clear_before_raw = config.get('clearBefore', True)
        # 支持变量引用
        if isinstance(clear_before_raw, str):
            clear_before_raw = context.resolve_value(clear_before_raw)
        clear_before = clear_before_raw in [True, 'true', 'True', '1', 1]
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            try:
                await context.page.wait_for_selector(selector, state='visible', timeout=timeout_ms)
            except:
                pass
            
            element, input_type = await self._find_input_element(context.page, selector)
            
            if input_type == 'keyboard':
                await element.click()
                if clear_before:
                    await context.page.keyboard.press('Control+a')
                    await context.page.keyboard.press('Backspace')
                await context.page.keyboard.type(text)
                return ModuleResult(success=True, message=f"已通过键盘输入文本到: {selector}")
            else:
                if clear_before:
                    await element.clear()
                await element.fill(text)
                suffix = f" (在内部{input_type}元素)" if input_type == 'inner' else ""
                return ModuleResult(success=True, message=f"已输入文本到: {selector}{suffix}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"输入文本失败: {str(e)}")


@register_executor
class GetElementInfoExecutor(ModuleExecutor):
    """获取元素信息模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "get_element_info"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        attribute = context.resolve_value(config.get('attribute', 'text'))  # 支持变量引用
        variable_name = config.get('variableName', '')
        column_name = config.get('columnName', '')
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            element = context.page.locator(selector).first
            
            try:
                await element.wait_for(state='attached', timeout=timeout_ms)
            except:
                try:
                    await context.page.wait_for_selector(selector, state='visible', timeout=timeout_ms)
                    element = context.page.locator(selector).first
                except:
                    pass
            
            if await element.count() == 0:
                return ModuleResult(success=False, error=f"未找到元素: {selector}")
            
            value = None
            for retry in range(3):
                if attribute == 'text':
                    value = await element.text_content()
                elif attribute == 'innerHTML':
                    value = await element.inner_html()
                elif attribute == 'value':
                    value = await element.input_value()
                elif attribute == 'href':
                    value = await element.get_attribute('href')
                elif attribute == 'src':
                    value = await element.get_attribute('src')
                else:
                    value = await element.get_attribute(attribute)
                
                if value is not None and value != '':
                    break
                
                if retry < 2:
                    await asyncio.sleep(0.1)
            
            if variable_name:
                context.set_variable(variable_name, value)
            
            if column_name:
                context.add_data_value(column_name, value)
            
            return ModuleResult(success=True, message=f"已获取元素信息: {value}", data=value)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"获取元素信息失败: {str(e)}")


@register_executor
class WaitExecutor(ModuleExecutor):
    """等待模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "wait"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        wait_type = context.resolve_value(config.get('waitType', 'time'))  # 支持变量引用
        
        try:
            if wait_type == 'time':
                duration = to_int(config.get('duration', 1000), 1000, context)
                await asyncio.sleep(duration / 1000)
                return ModuleResult(success=True, message=f"已等待 {duration}ms")
            
            elif wait_type == 'selector':
                selector = context.resolve_value(config.get('selector', ''))
                state = context.resolve_value(config.get('state', 'visible'))  # 支持变量引用
                
                if not selector:
                    return ModuleResult(success=False, error="选择器不能为空")
                
                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")
                
                await context.switch_to_latest_page()
                await context.page.wait_for_selector(selector, state=state)
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
        wait_condition = context.resolve_value(config.get('waitCondition', 'visible'))  # 支持变量引用
        wait_timeout = to_int(config.get('waitTimeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            state_map = {
                'visible': 'visible',
                'hidden': 'hidden',
                'attached': 'attached',
                'detached': 'detached',
            }
            state = state_map.get(wait_condition, 'visible')
            
            await context.page.wait_for_selector(selector, state=state, timeout=wait_timeout)
            
            condition_labels = {
                'visible': '可见',
                'hidden': '隐藏/消失',
                'attached': '存在于DOM',
                'detached': '从DOM移除',
            }
            label = condition_labels.get(wait_condition, wait_condition)
            
            return ModuleResult(
                success=True, 
                message=f"元素已{label}: {selector}",
                data={'selector': selector, 'condition': wait_condition}
            )
        
        except Exception as e:
            error_msg = str(e)
            if 'Timeout' in error_msg:
                return ModuleResult(success=False, error=f"等待超时 ({wait_timeout}ms): 元素 {selector} 未满足条件 '{wait_condition}'")
            return ModuleResult(success=False, error=f"等待元素失败: {error_msg}")


@register_executor
class WaitImageExecutor(ModuleExecutor):
    """等待图像模块执行器 - 等待屏幕上出现指定图像"""
    
    @property
    def module_type(self) -> str:
        return "wait_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import ctypes
        
        image_path = context.resolve_value(config.get('imagePath', ''))
        confidence = to_float(config.get('confidence', 0.8), 0.8, context)
        wait_timeout = to_int(config.get('waitTimeout', 30), 30, context)  # 秒
        check_interval = to_float(config.get('checkInterval', 0.5), 0.5, context)  # 秒
        variable_name_x = config.get('variableNameX', '')
        variable_name_y = config.get('variableNameY', '')
        search_region = config.get('searchRegion', None)
        
        if not image_path:
            return ModuleResult(success=False, error="图像路径不能为空")
        
        if not Path(image_path).exists():
            return ModuleResult(success=False, error=f"图像文件不存在: {image_path}")
        
        try:
            import cv2
            import numpy as np
            from .type_utils import parse_search_region
            
            # 设置 DPI 感知
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except:
                    pass
            
            # 读取模板图像
            template = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if template is None:
                return ModuleResult(success=False, error="无法读取图像文件，请检查图像格式")
            
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            h, w = template_gray.shape
            
            # 解析搜索区域
            region_x, region_y, region_w, region_h = parse_search_region(search_region)
            use_region = region_w > 0 and region_h > 0
            
            # 获取虚拟屏幕尺寸
            SM_XVIRTUALSCREEN = 76
            SM_YVIRTUALSCREEN = 77
            SM_CXVIRTUALSCREEN = 78
            SM_CYVIRTUALSCREEN = 79
            
            virtual_left = ctypes.windll.user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
            virtual_top = ctypes.windll.user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
            virtual_width = ctypes.windll.user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
            virtual_height = ctypes.windll.user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            
            start_time = time.time()
            found = False
            center_x, center_y = 0, 0
            best_confidence = 0
            
            while time.time() - start_time < wait_timeout:
                # 截取屏幕
                if use_region:
                    from PIL import ImageGrab
                    screenshot_pil = ImageGrab.grab(bbox=(region_x, region_y, region_x + region_w, region_y + region_h))
                    screen = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
                    offset_x, offset_y = region_x, region_y
                else:
                    try:
                        import win32gui
                        import win32ui
                        import win32con
                        
                        hdesktop = win32gui.GetDesktopWindow()
                        desktop_dc = win32gui.GetWindowDC(hdesktop)
                        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
                        mem_dc = img_dc.CreateCompatibleDC()
                        
                        screenshot = win32ui.CreateBitmap()
                        screenshot.CreateCompatibleBitmap(img_dc, virtual_width, virtual_height)
                        mem_dc.SelectObject(screenshot)
                        mem_dc.BitBlt((0, 0), (virtual_width, virtual_height), img_dc, 
                                      (virtual_left, virtual_top), win32con.SRCCOPY)
                        
                        bmpinfo = screenshot.GetInfo()
                        bmpstr = screenshot.GetBitmapBits(True)
                        screen = np.frombuffer(bmpstr, dtype=np.uint8).reshape(
                            (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
                        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)
                        
                        mem_dc.DeleteDC()
                        win32gui.DeleteObject(screenshot.GetHandle())
                        win32gui.ReleaseDC(hdesktop, desktop_dc)
                        offset_x, offset_y = virtual_left, virtual_top
                        
                    except ImportError:
                        from PIL import ImageGrab
                        screenshot_pil = ImageGrab.grab(all_screens=True)
                        screen = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
                        offset_x, offset_y = 0, 0
                
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                
                # 模板匹配
                result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    # 找到匹配
                    img_left = offset_x + max_loc[0]
                    img_top = offset_y + max_loc[1]
                    center_x = img_left + w // 2
                    center_y = img_top + h // 2
                    best_confidence = max_val
                    found = True
                    break
                
                # 更新最高匹配度
                if max_val > best_confidence:
                    best_confidence = max_val
                
                await asyncio.sleep(check_interval)
            
            if not found:
                return ModuleResult(
                    success=False, 
                    error=f"等待超时 ({wait_timeout}秒): 未找到匹配的图像（最高匹配度: {best_confidence:.2%}）"
                )
            
            # 保存坐标到变量
            if variable_name_x:
                context.set_variable(variable_name_x, center_x)
            if variable_name_y:
                context.set_variable(variable_name_y, center_y)
            
            return ModuleResult(
                success=True, 
                message=f"图像已出现在 ({center_x}, {center_y})，匹配度: {best_confidence:.2%}",
                data={'x': center_x, 'y': center_y, 'confidence': best_confidence}
            )
        
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else "opencv-python/Pillow"
            return ModuleResult(
                success=False, 
                error=f"等待图像功能初始化失败: {missing}"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"等待图像失败: {str(e)}")


@register_executor
class ClosePageExecutor(ModuleExecutor):
    """关闭网页模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "close_page"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            if context.page is not None:
                await context.page.close()
                context.page = None
                return ModuleResult(success=True, message="已关闭页面")
            return ModuleResult(success=True, message="没有需要关闭的页面")
        except Exception as e:
            return ModuleResult(success=False, error=f"关闭页面失败: {str(e)}")


@register_executor
class SetVariableExecutor(ModuleExecutor):
    """设置变量模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "set_variable"
    
    def _evaluate_expression(self, expr: str, context: ExecutionContext):
        """安全地计算表达式"""
        import re
        
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
        variable_value = context.resolve_value(config.get('variableValue', ''))  # 支持变量引用
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            resolved_value = self._evaluate_expression(variable_value, context)
            context.set_variable(variable_name, resolved_value)
            
            return ModuleResult(
                success=True, 
                message=f"已设置变量 {variable_name} = {resolved_value}",
                data=resolved_value
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"设置变量失败: {str(e)}")


@register_executor
class PrintLogExecutor(ModuleExecutor):
    """打印日志模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "print_log"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        log_message = context.resolve_value(config.get('logMessage', '')) or '(空日志)'  # 支持变量引用
        log_level = context.resolve_value(config.get('logLevel', 'info'))  # 支持变量引用
        
        try:
            return ModuleResult(
                success=True, 
                message=log_message,
                data={'level': log_level, 'message': log_message},
                log_level=log_level
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"打印日志失败: {str(e)}")


@register_executor
class PlaySoundExecutor(ModuleExecutor):
    """播放提示音模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "play_sound"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import winsound
        
        beep_count = to_int(config.get('beepCount', 1), 1, context)
        beep_interval = to_int(config.get('beepInterval', 300), 300, context)
        
        try:
            for i in range(beep_count):
                winsound.Beep(1000, 200)
                if i < beep_count - 1:
                    await asyncio.sleep(beep_interval / 1000)
            
            return ModuleResult(
                success=True, 
                message=f"已播放 {beep_count} 次提示音",
                data={'count': beep_count}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"播放提示音失败: {str(e)}")


@register_executor
class SystemNotificationExecutor(ModuleExecutor):
    """系统消息弹窗模块执行器 - Windows 系统右下角通知"""
    
    @property
    def module_type(self) -> str:
        return "system_notification"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        title = context.resolve_value(config.get('notifyTitle', 'WebRPA通知')) or 'WebRPA通知'
        message = context.resolve_value(config.get('notifyMessage', ''))
        duration = to_int(config.get('duration', 5), 5, context)  # 显示时长（秒）
        
        if not message:
            return ModuleResult(success=False, error="通知消息不能为空")
        
        try:
            loop = asyncio.get_running_loop()
            
            def show_notification():
                try:
                    # 使用 plyer 库显示通知
                    from plyer import notification
                    notification.notify(
                        title=title,
                        message=message,
                        timeout=duration,
                        app_name='WebRPA'
                    )
                    return True, None
                except Exception as e:
                    return False, str(e)
            
            success, error = await loop.run_in_executor(None, show_notification)
            
            if not success:
                return ModuleResult(success=False, error=f"显示通知失败: {error}")
            
            return ModuleResult(
                success=True,
                message=f"已显示系统通知: {title}",
                data={'title': title, 'message': message}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"系统通知失败: {str(e)}")


@register_executor
class PlayMusicExecutor(ModuleExecutor):
    """播放音乐模块执行器 - 通过前端浏览器播放，支持播放器UI控制"""

    @property
    def module_type(self) -> str:
        return "play_music"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_play_music_sync

        audio_url = context.resolve_value(config.get("audioUrl", ""))
        wait_for_end_raw = config.get("waitForEnd", True)
        # 支持变量引用
        if isinstance(wait_for_end_raw, str):
            wait_for_end_raw = context.resolve_value(wait_for_end_raw)
        wait_for_end = wait_for_end_raw in [True, 'true', 'True', '1', 1]

        if not audio_url:
            return ModuleResult(success=False, error="音频URL不能为空")

        try:
            url = audio_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # 通过前端播放音乐
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_play_music_sync(
                    audio_url=url,
                    wait_for_end=wait_for_end,
                    timeout=600  # 10分钟超时
                )
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"播放音乐失败: {error_msg}")

            source_display = audio_url
            if len(source_display) > 50:
                source_display = source_display[:50] + "..."

            return ModuleResult(success=True, message=f"播放完成: {source_display}")

        except Exception as e:
            return ModuleResult(success=False, error=f"播放音乐失败: {str(e)}")


@register_executor
class PlayVideoExecutor(ModuleExecutor):
    """播放视频模块执行器 - 通过前端浏览器播放，支持播放器UI控制"""

    @property
    def module_type(self) -> str:
        return "play_video"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_play_video_sync

        video_url = context.resolve_value(config.get("videoUrl", ""))
        wait_for_end_raw = config.get("waitForEnd", True)
        # 支持变量引用
        if isinstance(wait_for_end_raw, str):
            wait_for_end_raw = context.resolve_value(wait_for_end_raw)
        wait_for_end = wait_for_end_raw in [True, 'true', 'True', '1', 1]

        if not video_url:
            return ModuleResult(success=False, error="视频URL不能为空")

        try:
            url = video_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # 通过前端播放视频
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_play_video_sync(
                    video_url=url,
                    wait_for_end=wait_for_end,
                    timeout=3600  # 1小时超时
                )
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"播放视频失败: {error_msg}")

            source_display = video_url
            if len(source_display) > 50:
                source_display = source_display[:50] + "..."

            return ModuleResult(success=True, message=f"播放完成: {source_display}")

        except Exception as e:
            return ModuleResult(success=False, error=f"播放视频失败: {str(e)}")


@register_executor
class ViewImageExecutor(ModuleExecutor):
    """查看图片模块执行器 - 通过前端浏览器显示图片查看器"""

    @property
    def module_type(self) -> str:
        return "view_image"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_view_image_sync

        image_url = context.resolve_value(config.get("imageUrl", ""))
        auto_close_raw = config.get("autoClose", False)
        # 支持变量引用
        if isinstance(auto_close_raw, str):
            auto_close_raw = context.resolve_value(auto_close_raw)
        auto_close = auto_close_raw in [True, 'true', 'True', '1', 1]
        display_time = to_int(config.get("displayTime", 5000), 5000, context)  # 支持变量引用

        if not image_url:
            return ModuleResult(success=False, error="图片URL不能为空")

        try:
            url = image_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # 通过前端显示图片
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_view_image_sync(
                    image_url=url,
                    auto_close=auto_close,
                    display_time=display_time,
                    timeout=300  # 5分钟超时
                )
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"查看图片失败: {error_msg}")

            source_display = image_url
            if len(source_display) > 50:
                source_display = source_display[:50] + "..."

            return ModuleResult(success=True, message=f"图片查看完成: {source_display}")

        except Exception as e:
            return ModuleResult(success=False, error=f"查看图片失败: {str(e)}")


@register_executor
class InputPromptExecutor(ModuleExecutor):
    """变量输入框模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "input_prompt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_input_prompt_sync
        
        variable_name = config.get('variableName', '')
        prompt_title = context.resolve_value(config.get('promptTitle', '输入'))
        prompt_message = context.resolve_value(config.get('promptMessage', '请输入值:'))
        default_value = context.resolve_value(config.get('defaultValue', ''))
        input_mode = context.resolve_value(config.get('inputMode', 'single'))  # 支持变量引用
        min_value = config.get('minValue')
        max_value = config.get('maxValue')
        max_length = config.get('maxLength')
        required_raw = config.get('required', True)
        # 支持变量引用
        if isinstance(required_raw, str):
            required_raw = context.resolve_value(required_raw)
        required = required_raw in [True, 'true', 'True', '1', 1]
        
        # 列表选择模式：解析选项列表
        select_options = None
        if input_mode in ('select_single', 'select_multiple'):
            select_options_var = config.get('selectOptions', '')
            if select_options_var:
                resolved_options = context.resolve_value(select_options_var)
                if isinstance(resolved_options, list):
                    # 将列表中的每个元素转换为字符串
                    select_options = []
                    for item in resolved_options:
                        if isinstance(item, dict):
                            # 如果是字典，尝试转换为 JSON 字符串
                            import json
                            select_options.append(json.dumps(item, ensure_ascii=False))
                        elif isinstance(item, (list, tuple)):
                            # 如果是列表或元组，转换为字符串
                            select_options.append(str(item))
                        else:
                            # 其他类型直接转换为字符串
                            select_options.append(str(item))
                elif isinstance(resolved_options, str):
                    # 尝试从变量获取
                    var_name = select_options_var.strip('{}')
                    raw_list = context.variables.get(var_name, [])
                    if isinstance(raw_list, list):
                        # 同样处理列表中的元素
                        select_options = []
                        for item in raw_list:
                            if isinstance(item, dict):
                                import json
                                select_options.append(json.dumps(item, ensure_ascii=False))
                            elif isinstance(item, (list, tuple)):
                                select_options.append(str(item))
                            else:
                                select_options.append(str(item))
                    else:
                        select_options = []
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        try:
            # 使用线程池执行同步等待，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            user_input = await loop.run_in_executor(
                None,
                lambda: request_input_prompt_sync(
                    variable_name=variable_name,
                    title=prompt_title,
                    message=prompt_message,
                    default_value=default_value,
                    input_mode=input_mode,
                    min_value=min_value,
                    max_value=max_value,
                    max_length=max_length,
                    required=required,
                    select_options=select_options,
                    timeout=300
                )
            )
            
            if user_input is None:
                return ModuleResult(
                    success=True, 
                    message=f"用户取消输入，变量 {variable_name} 保持不变",
                    data={'cancelled': True}
                )
            
            # 根据输入模式处理结果
            if input_mode == 'checkbox':
                # 复选框模式：将字符串 'true'/'false' 转换为布尔值
                bool_value = user_input.lower() in ('true', '1', 'yes', 'on')
                context.set_variable(variable_name, bool_value)
                return ModuleResult(
                    success=True, 
                    message=f"已设置变量 {variable_name} = {bool_value}",
                    data={'value': bool_value, 'type': 'boolean'}
                )
            elif input_mode == 'slider_int':
                # 滑动条（整数）模式
                try:
                    int_value = int(float(user_input))
                    context.set_variable(variable_name, int_value)
                    return ModuleResult(
                        success=True, 
                        message=f"已设置变量 {variable_name} = {int_value}",
                        data={'value': int_value, 'type': 'integer'}
                    )
                except ValueError:
                    return ModuleResult(success=False, error=f"滑动条返回的值不是有效的整数")
            elif input_mode == 'slider_float':
                # 滑动条（浮点数）模式
                try:
                    float_value = float(user_input)
                    context.set_variable(variable_name, float_value)
                    return ModuleResult(
                        success=True, 
                        message=f"已设置变量 {variable_name} = {float_value}",
                        data={'value': float_value, 'type': 'float'}
                    )
                except ValueError:
                    return ModuleResult(success=False, error=f"滑动条返回的值不是有效的数字")
            elif input_mode == 'select_single':
                # 列表单选模式：返回选中的单个项（字符串）
                context.set_variable(variable_name, user_input)
                return ModuleResult(
                    success=True, 
                    message=f"已设置变量 {variable_name} = {user_input}",
                    data={'value': user_input, 'type': 'string'}
                )
            elif input_mode == 'select_multiple':
                # 列表多选模式：返回选中的多个项（列表）
                import json
                try:
                    # 前端发送的是 JSON 字符串
                    selected_list = json.loads(user_input) if isinstance(user_input, str) else user_input
                    if not isinstance(selected_list, list):
                        selected_list = [selected_list]
                    context.set_variable(variable_name, selected_list)
                    return ModuleResult(
                        success=True, 
                        message=f"已设置变量 {variable_name} = 列表({len(selected_list)}项)",
                        data={'value': selected_list, 'count': len(selected_list), 'type': 'list'}
                    )
                except (json.JSONDecodeError, ValueError):
                    # 如果解析失败，当作单个字符串处理
                    context.set_variable(variable_name, [user_input])
                    return ModuleResult(
                        success=True, 
                        message=f"已设置变量 {variable_name} = 列表(1项)",
                        data={'value': [user_input], 'count': 1, 'type': 'list'}
                    )
            elif input_mode == 'list':
                result_list = [line.strip() for line in user_input.split('\n') if line.strip()]
                context.set_variable(variable_name, result_list)
                return ModuleResult(
                    success=True, 
                    message=f"已设置变量 {variable_name} = 列表({len(result_list)}项)",
                    data={'value': result_list, 'count': len(result_list)}
                )
            elif input_mode in ('number', 'integer'):
                try:
                    if input_mode == 'integer':
                        num_value = int(user_input)
                    else:
                        num_value = float(user_input)
                    context.set_variable(variable_name, num_value)
                    return ModuleResult(
                        success=True, 
                        message=f"已设置变量 {variable_name} = {num_value}",
                        data={'value': num_value}
                    )
                except ValueError:
                    return ModuleResult(success=False, error=f"输入的值不是有效的{'整数' if input_mode == 'integer' else '数字'}")
            elif input_mode in ('file', 'folder'):
                # 文件/文件夹路径模式
                context.set_variable(variable_name, user_input)
                mode_name = '文件' if input_mode == 'file' else '文件夹'
                return ModuleResult(
                    success=True, 
                    message=f"已设置{mode_name}路径 {variable_name} = {user_input}",
                    data={'value': user_input, 'type': input_mode}
                )
            else:
                # single, multiline, password 都保存为字符串
                context.set_variable(variable_name, user_input)
                display_value = '******' if input_mode == 'password' else user_input
                return ModuleResult(
                    success=True, 
                    message=f"已设置变量 {variable_name} = {display_value}",
                    data={'value': user_input}
                )
        except Exception as e:
            return ModuleResult(success=False, error=f"输入框失败: {str(e)}")


@register_executor
class RandomNumberExecutor(ModuleExecutor):
    """生成随机数模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "random_number"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import random
        
        random_type = context.resolve_value(config.get('randomType', 'integer'))  # 支持变量引用
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
            
            return ModuleResult(
                success=True,
                message=f"已生成随机数: {result}",
                data={'value': result}
            )
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
        
        time_format = context.resolve_value(config.get('timeFormat', 'datetime'))  # 支持变量引用
        custom_format = context.resolve_value(config.get('customFormat', ''))  # 支持变量引用
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
            
            return ModuleResult(
                success=True,
                message=f"已获取时间: {result}",
                data={'value': result}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"获取时间失败: {str(e)}")


@register_executor
class ScreenshotExecutor(ModuleExecutor):
    """网页截图模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "screenshot"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import os
        from datetime import datetime
        
        screenshot_type = context.resolve_value(config.get('screenshotType', 'fullpage'))  # 支持变量引用
        selector = context.resolve_value(config.get('selector', ''))
        save_path = context.resolve_value(config.get('savePath', ''))
        file_name_pattern = context.resolve_value(config.get('fileNamePattern', ''))
        variable_name = config.get('variableName', '')
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if file_name_pattern:
                file_name = file_name_pattern.replace('{时间戳}', timestamp)
                if not file_name.endswith('.png'):
                    file_name += '.png'
            else:
                file_name = f"screenshot_{timestamp}.png"
            
            if save_path:
                if save_path.endswith('.png'):
                    final_path = save_path
                else:
                    os.makedirs(save_path, exist_ok=True)
                    final_path = os.path.join(save_path, file_name)
            else:
                screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'screenshots')
                os.makedirs(screenshots_dir, exist_ok=True)
                final_path = os.path.join(screenshots_dir, file_name)
            
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            if screenshot_type == 'element' and selector:
                await context.page.wait_for_selector(selector, state='visible')
                element = context.page.locator(selector).first
                await element.screenshot(path=final_path)
            elif screenshot_type == 'viewport':
                await context.page.screenshot(path=final_path, full_page=False)
            else:
                await context.page.screenshot(path=final_path, full_page=True)
            
            if variable_name:
                context.set_variable(variable_name, final_path)
            
            return ModuleResult(
                success=True,
                message=f"已保存截图: {final_path}",
                data={'path': final_path}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"截图失败: {str(e)}")


@register_executor
class TextToSpeechExecutor(ModuleExecutor):
    """文本朗读模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "text_to_speech"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_tts_sync
        
        text = context.resolve_value(config.get('text', ''))
        lang = context.resolve_value(config.get('lang', 'zh-CN'))  # 支持变量引用
        rate = to_float(config.get('rate', 1), 1.0, context)  # 支持变量引用
        pitch = to_float(config.get('pitch', 1), 1.0, context)  # 支持变量引用
        volume = to_float(config.get('volume', 1), 1.0, context)  # 支持变量引用
        
        if not text:
            return ModuleResult(success=False, error="朗读文本不能为空")
        
        try:
            # 使用线程池执行同步等待，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None,
                lambda: request_tts_sync(
                    text=text,
                    lang=lang,
                    rate=rate,
                    pitch=pitch,
                    volume=volume,
                    timeout=60
                )
            )
            
            if success:
                return ModuleResult(
                    success=True,
                    message=f"已朗读文本: {text[:50]}{'...' if len(text) > 50 else ''}",
                    data={'text': text, 'lang': lang}
                )
            else:
                return ModuleResult(success=False, error="语音合成超时或失败")
        except Exception as e:
            return ModuleResult(success=False, error=f"文本朗读失败: {str(e)}")


@register_executor
class JsScriptExecutor(ModuleExecutor):
    """JS脚本模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "js_script"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_js_script_sync
        
        code = context.resolve_value(config.get('code', ''))  # 支持变量引用
        result_variable = config.get('resultVariable', '')
        
        if not code:
            return ModuleResult(success=False, error="JavaScript代码不能为空")
        
        try:
            variables = dict(context.variables)
            
            # 使用线程池执行同步等待，避免阻塞事件循环
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_js_script_sync(
                    code=code,
                    variables=variables,
                    timeout=30
                )
            )
            
            if result.get('success'):
                script_result = result.get('result')
                
                if result_variable:
                    context.set_variable(result_variable, script_result)
                
                result_str = str(script_result)
                if len(result_str) > 100:
                    result_str = result_str[:100] + '...'
                
                return ModuleResult(
                    success=True,
                    message=f"JS脚本执行成功，返回值: {result_str}",
                    data={'result': script_result}
                )
            else:
                error = result.get('error', '未知错误')
                return ModuleResult(success=False, error=f"JS脚本执行失败: {error}")
        except Exception as e:
            return ModuleResult(success=False, error=f"JS脚本执行异常: {str(e)}")


@register_executor
class RefreshPageExecutor(ModuleExecutor):
    """刷新页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "refresh_page"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        wait_until = context.resolve_value(config.get('waitUntil', 'load'))  # 支持变量引用
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            await context.page.reload(wait_until=wait_until)
            return ModuleResult(success=True, message="已刷新页面")
        except Exception as e:
            return ModuleResult(success=False, error=f"刷新页面失败: {str(e)}")


@register_executor
class GoBackExecutor(ModuleExecutor):
    """返回上一页模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "go_back"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        wait_until = context.resolve_value(config.get('waitUntil', 'load'))  # 支持变量引用
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            response = await context.page.go_back(wait_until=wait_until)
            
            if response is None:
                return ModuleResult(success=True, message="已返回上一页（无历史记录）")
            
            return ModuleResult(success=True, message=f"已返回上一页: {context.page.url}")
        except Exception as e:
            return ModuleResult(success=False, error=f"返回上一页失败: {str(e)}")


@register_executor
class GoForwardExecutor(ModuleExecutor):
    """前进下一页模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "go_forward"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        wait_until = context.resolve_value(config.get('waitUntil', 'load'))  # 支持变量引用
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            response = await context.page.go_forward(wait_until=wait_until)
            
            if response is None:
                return ModuleResult(success=True, message="已前进下一页（无前进记录）")
            
            return ModuleResult(success=True, message=f"已前进下一页: {context.page.url}")
        except Exception as e:
            return ModuleResult(success=False, error=f"前进下一页失败: {str(e)}")


@register_executor
class HandleDialogExecutor(ModuleExecutor):
    """处理弹窗模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "handle_dialog"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        dialog_action = context.resolve_value(config.get('dialogAction', 'accept'))  # 支持变量引用
        prompt_text = context.resolve_value(config.get('promptText', ''))
        save_message = config.get('saveMessage', '')
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            dialog_info = {'handled': False, 'message': '', 'type': ''}
            
            async def handle_dialog(dialog):
                dialog_info['message'] = dialog.message
                dialog_info['type'] = dialog.type
                dialog_info['handled'] = True
                
                if dialog_action == 'accept':
                    if dialog.type == 'prompt' and prompt_text:
                        await dialog.accept(prompt_text)
                    else:
                        await dialog.accept()
                else:
                    await dialog.dismiss()
            
            context.page.on('dialog', handle_dialog)
            await asyncio.sleep(0.5)
            context.page.remove_listener('dialog', handle_dialog)
            
            if save_message and dialog_info['message']:
                context.set_variable(save_message, dialog_info['message'])
            
            if dialog_info['handled']:
                action_text = '确认' if dialog_action == 'accept' else '取消'
                return ModuleResult(
                    success=True,
                    message=f"已{action_text}{dialog_info['type']}弹窗: {dialog_info['message'][:50]}",
                    data=dialog_info
                )
            else:
                return ModuleResult(
                    success=True,
                    message="弹窗处理器已设置，等待弹窗出现",
                    data={'waiting': True}
                )
        except Exception as e:
            return ModuleResult(success=False, error=f"处理弹窗失败: {str(e)}")


@register_executor
class InjectJavaScriptExecutor(ModuleExecutor):
    """JS脚本注入模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "inject_javascript"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        javascript_code = context.resolve_value(config.get('javascriptCode', ''))
        save_result = config.get('saveResult', '')
        inject_mode = context.resolve_value(config.get('injectMode', 'current'))  # current, all, url_match, index
        target_url = context.resolve_value(config.get('targetUrl', ''))
        target_index_str = context.resolve_value(config.get('targetIndex', '0'))
        
        # 转换索引为整数
        try:
            target_index = int(target_index_str) if target_index_str else 0
        except ValueError:
            target_index = 0
        
        if not javascript_code:
            return ModuleResult(success=False, error="JavaScript代码不能为空")
        
        if context.browser_context is None:
            return ModuleResult(success=False, error="没有打开的浏览器")
        
        try:
            # 获取所有页面
            all_pages = context.browser_context.pages
            if not all_pages:
                return ModuleResult(success=False, error="没有打开的页面")
            
            # 根据注入模式选择目标页面
            target_pages = []
            
            if inject_mode == 'current':
                # 当前页面模式
                await context.switch_to_latest_page()
                if context.page:
                    target_pages = [context.page]
                else:
                    return ModuleResult(success=False, error="没有当前活动页面")
            
            elif inject_mode == 'all':
                # 所有标签页模式
                target_pages = all_pages
            
            elif inject_mode == 'url_match':
                # URL匹配模式
                if not target_url:
                    return ModuleResult(success=False, error="URL匹配模式需要指定目标URL")
                
                import re
                # 支持通配符和正则表达式
                url_pattern = target_url.replace('*', '.*')
                try:
                    regex = re.compile(url_pattern)
                    for page in all_pages:
                        if regex.search(page.url):
                            target_pages.append(page)
                except re.error:
                    return ModuleResult(success=False, error=f"无效的URL匹配模式: {target_url}")
                
                if not target_pages:
                    return ModuleResult(success=False, error=f"没有找到匹配URL的页面: {target_url}")
            
            elif inject_mode == 'index':
                # 索引模式
                if target_index < 0 or target_index >= len(all_pages):
                    return ModuleResult(
                        success=False, 
                        error=f"标签页索引超出范围: {target_index}（共有 {len(all_pages)} 个标签页）"
                    )
                target_pages = [all_pages[target_index]]
            
            else:
                return ModuleResult(success=False, error=f"不支持的注入模式: {inject_mode}")
            
            # 执行JavaScript代码
            results = []
            errors = []
            
            # 包装用户代码以支持return语句
            # 如果代码已经是函数形式，直接使用；否则包装成IIFE
            wrapped_code = javascript_code.strip()
            if not (wrapped_code.startswith('(') or wrapped_code.startswith('async') or wrapped_code.startswith('function')):
                # 包装成立即执行的异步函数，支持return和await
                wrapped_code = f"(async () => {{ {javascript_code} }})()"
            
            for i, page in enumerate(target_pages):
                try:
                    result = await page.evaluate(wrapped_code)
                    results.append({
                        'index': all_pages.index(page),
                        'url': page.url,
                        'title': await page.title(),
                        'result': result,
                        'success': True
                    })
                except Exception as e:
                    errors.append({
                        'index': all_pages.index(page),
                        'url': page.url,
                        'error': str(e)
                    })
            
            # 保存结果
            if save_result:
                if inject_mode == 'current' or inject_mode == 'index':
                    # 单页面模式，保存单个结果
                    if results:
                        context.set_variable(save_result, results[0]['result'])
                else:
                    # 多页面模式，保存结果数组
                    context.set_variable(save_result, results)
            
            # 生成执行报告
            success_count = len(results)
            error_count = len(errors)
            total_count = success_count + error_count
            
            if error_count == 0:
                # 全部成功
                if inject_mode == 'current' or inject_mode == 'index':
                    result_str = str(results[0]['result']) if results[0]['result'] is not None else 'undefined'
                    if len(result_str) > 100:
                        result_str = result_str[:100] + '...'
                    message = f"JavaScript执行成功，返回值: {result_str}"
                else:
                    message = f"JavaScript执行成功，已注入到 {success_count} 个标签页"
                
                return ModuleResult(
                    success=True,
                    message=message,
                    data={
                        'mode': inject_mode,
                        'total': total_count,
                        'success': success_count,
                        'results': results
                    }
                )
            elif success_count == 0:
                # 全部失败
                error_details = '\n'.join([f"标签页 {e['index']} ({e['url']}): {e['error']}" for e in errors])
                return ModuleResult(
                    success=False,
                    error=f"JavaScript执行失败（{error_count}/{total_count}）:\n{error_details}"
                )
            else:
                # 部分成功
                error_details = '\n'.join([f"标签页 {e['index']}: {e['error']}" for e in errors])
                return ModuleResult(
                    success=True,
                    message=f"JavaScript部分执行成功（{success_count}/{total_count}），{error_count} 个失败",
                    data={
                        'mode': inject_mode,
                        'total': total_count,
                        'success': success_count,
                        'error': error_count,
                        'results': results,
                        'errors': errors
                    }
                )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"JavaScript执行失败: {str(e)}")



@register_executor
class SwitchIframeExecutor(ModuleExecutor):
    """切换到iframe模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "switch_iframe"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        切换到iframe内部
        配置项：
        - locateBy: 定位方式（index/name/selector）
        - iframeIndex: iframe索引（从0开始）
        - iframeName: iframe的name或id属性
        - iframeSelector: iframe的CSS选择器
        """
        locate_by = context.resolve_value(config.get('locateBy', 'index'))
        iframe_index = to_int(config.get('iframeIndex', 0), 0, context)
        iframe_name = context.resolve_value(config.get('iframeName', ''))
        iframe_selector = context.resolve_value(config.get('iframeSelector', ''))
        
        if context.page is None:
            return ModuleResult(success=False, error="页面未初始化，请先打开网页")
        
        try:
            page = context.page
            frame = None
            
            # 调试：列出所有frame
            print(f"[SwitchIframe] 页面URL: {page.url}")
            print(f"[SwitchIframe] 所有frames:")
            for i, f in enumerate(page.frames):
                is_main = " (主frame)" if f == page.main_frame else ""
                print(f"  Frame {i}: name='{f.name}', url={f.url}{is_main}")
            
            if locate_by == 'index':
                # 通过索引定位iframe
                frames = page.frames
                # 过滤掉主框架
                child_frames = [f for f in frames if f != page.main_frame]
                
                print(f"[SwitchIframe] 子frames数量: {len(child_frames)}")
                
                if iframe_index < 0 or iframe_index >= len(child_frames):
                    return ModuleResult(
                        success=False,
                        error=f"iframe索引超出范围: {iframe_index}（共有 {len(child_frames)} 个iframe）"
                    )
                
                frame = child_frames[iframe_index]
                print(f"[SwitchIframe] 选择的frame: {frame.name}, URL: {frame.url}")
                
            elif locate_by == 'name':
                # 通过name或id定位iframe
                if not iframe_name:
                    return ModuleResult(success=False, error="请指定iframe的name或id")
                
                print(f"[SwitchIframe] 查找name={iframe_name}的iframe...")
                
                # 先尝试通过name属性查找
                frame = page.frame(name=iframe_name)
                print(f"[SwitchIframe] page.frame(name={iframe_name}) 结果: {frame}")
                
                # 如果没找到，尝试通过id查找
                if frame is None:
                    try:
                        print(f"[SwitchIframe] 尝试通过id查找...")
                        iframe_element = await page.wait_for_selector(
                            f'iframe[id="{iframe_name}"]',
                            timeout=5000
                        )
                        if iframe_element:
                            frame = await iframe_element.content_frame()
                            print(f"[SwitchIframe] 通过id找到frame: {frame}")
                    except Exception as e:
                        print(f"[SwitchIframe] 通过id查找失败: {e}")
                
                if frame is None:
                    return ModuleResult(
                        success=False,
                        error=f"未找到name或id为 '{iframe_name}' 的iframe"
                    )
                
            elif locate_by == 'selector':
                # 通过CSS选择器定位iframe
                if not iframe_selector:
                    return ModuleResult(success=False, error="请指定iframe的CSS选择器")
                
                try:
                    iframe_element = await page.wait_for_selector(
                        iframe_selector,
                        timeout=10000
                    )
                    if iframe_element:
                        frame = await iframe_element.content_frame()
                    
                    if frame is None:
                        return ModuleResult(
                            success=False,
                            error=f"选择器 '{iframe_selector}' 找到的元素不是iframe"
                        )
                except Exception as e:
                    return ModuleResult(
                        success=False,
                        error=f"未找到iframe: {iframe_selector}，错误: {str(e)}"
                    )
            
            else:
                return ModuleResult(
                    success=False,
                    error=f"不支持的定位方式: {locate_by}"
                )
            
            # 等待iframe加载
            print(f"[SwitchIframe] 等待iframe加载...")
            print(f"[SwitchIframe] iframe当前URL: {frame.url}")
            try:
                # 等待iframe内容加载
                await frame.wait_for_load_state('domcontentloaded', timeout=10000)
                print(f"[SwitchIframe] iframe已加载，最终URL: {frame.url}")
                
                # 如果iframe是about:blank，等待一下看是否会变化
                if frame.url == 'about:blank' or not frame.url:
                    print(f"[SwitchIframe] iframe URL是about:blank，等待2秒...")
                    await asyncio.sleep(2)
                    print(f"[SwitchIframe] 等待后URL: {frame.url}")
                    
                    # 尝试等待iframe内有内容
                    try:
                        await frame.wait_for_selector('body', timeout=3000)
                        body_html = await frame.evaluate('document.body.innerHTML')
                        print(f"[SwitchIframe] iframe body内容长度: {len(body_html)}")
                        print(f"[SwitchIframe] iframe body前200字符: {body_html[:200]}")
                        
                        # 检查是否有嵌套iframe
                        nested_iframes = await frame.query_selector_all('iframe')
                        if nested_iframes:
                            print(f"[SwitchIframe] 检测到 {len(nested_iframes)} 个嵌套iframe")
                            # 如果只有一个嵌套iframe，自动切换到它
                            if len(nested_iframes) == 1:
                                print(f"[SwitchIframe] 自动切换到嵌套iframe...")
                                nested_frame = await nested_iframes[0].content_frame()
                                if nested_frame:
                                    # 等待嵌套iframe加载
                                    try:
                                        await nested_frame.wait_for_load_state('domcontentloaded', timeout=5000)
                                    except:
                                        pass
                                    
                                    print(f"[SwitchIframe] 嵌套iframe URL: {nested_frame.url}")
                                    frame = nested_frame  # 使用嵌套iframe
                                    print(f"[SwitchIframe] 已自动切换到嵌套iframe")
                    except Exception as e:
                        print(f"[SwitchIframe] 获取iframe内容失败: {e}")
                
            except Exception as e:
                print(f"[SwitchIframe] 等待iframe加载超时: {e}")
            
            # 切换到iframe
            # 保存主页面引用和iframe定位信息
            if not context._in_iframe:
                context._main_page = context.page
            
            # 保存iframe定位信息，用于后续动态获取frame
            if locate_by == 'name':
                context._iframe_locator = {'type': 'name', 'value': iframe_name}
            elif locate_by == 'index':
                context._iframe_locator = {'type': 'index', 'value': iframe_index}
            elif locate_by == 'selector':
                context._iframe_locator = {'type': 'selector', 'value': iframe_selector}
            
            # 设置iframe状态
            context._in_iframe = True
            context.page = frame
            context._current_frame = frame  # 保存frame的直接引用（重要！用于嵌套iframe）
            
            frame_url = frame.url if frame.url else '(about:blank)'
            
            print(f"[SwitchIframe] 切换完成，当前frame URL: {frame_url}")
            
            return ModuleResult(
                success=True,
                message=f"已切换到iframe（{locate_by}），URL: {frame_url}"
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"切换iframe失败: {str(e)}")


@register_executor
class SwitchToMainExecutor(ModuleExecutor):
    """切换回主页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "switch_to_main"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        切换回主页面（退出iframe）
        """
        if context.browser_context is None:
            return ModuleResult(success=False, error="浏览器未初始化")
        
        try:
            # 如果不在iframe中，无需切换
            if not context._in_iframe:
                if context.page:
                    return ModuleResult(
                        success=True,
                        message=f"当前已在主页面，URL: {context.page.url}"
                    )
                else:
                    return ModuleResult(success=False, error="没有活动页面")
            
            # 恢复主页面
            if context._main_page:
                context.page = context._main_page
                context._in_iframe = False
                context._main_page = None
                context._iframe_locator = None
                context._current_frame = None  # 清除frame引用
                
                return ModuleResult(
                    success=True,
                    message=f"已切换回主页面，URL: {context.page.url}"
                )
            else:
                # 如果没有保存的主页面引用，尝试获取最新页面
                await context.switch_to_latest_page()
                context._in_iframe = False
                context._main_page = None
                context._iframe_locator = None
                context._current_frame = None  # 清除frame引用
                
                if context.page:
                    return ModuleResult(
                        success=True,
                        message=f"已切换回主页面，URL: {context.page.url}"
                    )
                else:
                    return ModuleResult(success=False, error="无法找到主页面")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ModuleResult(success=False, error=f"切换回主页面失败: {str(e)}")
