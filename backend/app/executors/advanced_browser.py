"""高级模块执行器 - advanced_browser"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor, escape_css_selector
from .type_utils import to_int, to_float, parse_search_region
from pathlib import Path
import base64
import os
import re
import tempfile
import time


@register_executor
class SelectDropdownExecutor(ModuleExecutor):
    """下拉框选择模块执行器"""

    @property
    def module_type(self) -> str:
        return "select_dropdown"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        select_by = context.resolve_value(config.get('selectBy', 'value'))  # 支持变量引用
        value = context.resolve_value(config.get('value', ''))
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            # 先等待页面加载完成
            try:
                await context.page.wait_for_load_state('domcontentloaded', timeout=timeout_ms)
            except:
                pass
            
            await context.page.wait_for_selector(escape_css_selector(selector), state='visible', timeout=timeout_ms)
            element = context.page.locator(escape_css_selector(selector))
            
            if select_by == 'value':
                await element.select_option(value=value)
            elif select_by == 'label':
                await element.select_option(label=value)
            elif select_by == 'index':
                await element.select_option(index=int(value))
            
            return ModuleResult(success=True, message=f"已选择: {value}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"选择下拉框失败: {str(e)}")

@register_executor
class SetCheckboxExecutor(ModuleExecutor):
    """设置复选框模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "set_checkbox"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        checked_raw = config.get('checked', True)
        # 支持变量引用
        if isinstance(checked_raw, str):
            checked_raw = context.resolve_value(checked_raw)
        checked = checked_raw in [True, 'true', 'True', '1', 1]
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            await context.page.wait_for_selector(escape_css_selector(selector), state='visible')
            element = context.page.locator(escape_css_selector(selector))
            
            if checked:
                await element.check()
            else:
                await element.uncheck()
            
            return ModuleResult(success=True, message=f"复选框已{'勾选' if checked else '取消勾选'}")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"设置复选框失败: {str(e)}")

@register_executor
class DragElementExecutor(ModuleExecutor):
    """拖拽元素模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "drag_element"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        source_selector = context.resolve_value(config.get('sourceSelector', ''))
        target_selector = context.resolve_value(config.get('targetSelector', ''))
        target_position = config.get('targetPosition')
        
        if not source_selector:
            return ModuleResult(success=False, error="源元素选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            source = context.page.locator(escape_css_selector(source_selector))
            
            if target_selector:
                target = context.page.locator(escape_css_selector(target_selector))
                await source.drag_to(target)
            elif target_position:
                box = await source.bounding_box()
                if box:
                    start_x = box['x'] + box['width'] / 2
                    start_y = box['y'] + box['height'] / 2
                    end_x = target_position.get('x', start_x)
                    end_y = target_position.get('y', start_y)
                    
                    await context.page.mouse.move(start_x, start_y)
                    await context.page.mouse.down()
                    await context.page.mouse.move(end_x, end_y, steps=10)
                    await context.page.mouse.up()
            
            return ModuleResult(success=True, message="拖拽完成")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"拖拽元素失败: {str(e)}")

@register_executor
class ScrollPageExecutor(ModuleExecutor):
    """滚动页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "scroll_page"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        direction = context.resolve_value(config.get('direction', 'down'))  # 支持变量引用
        distance = to_int(config.get('distance', 500), 500, context)
        selector = context.resolve_value(config.get('selector', ''))
        scroll_mode = context.resolve_value(config.get('scrollMode', 'auto'))  # 支持变量引用
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            delta_x = 0
            delta_y = 0
            
            if direction == 'down':
                delta_y = distance
            elif direction == 'up':
                delta_y = -distance
            elif direction == 'right':
                delta_x = distance
            elif direction == 'left':
                delta_x = -distance
            
            # 使用鼠标滚轮模拟滚动（对抖音等虚拟滚动页面更有效）
            if scroll_mode == 'wheel' or scroll_mode == 'auto':
                try:
                    if selector:
                        # 先定位到元素中心
                        element = context.page.locator(escape_css_selector(selector)).first
                        box = await element.bounding_box()
                        if box:
                            center_x = box['x'] + box['width'] / 2
                            center_y = box['y'] + box['height'] / 2
                            await context.page.mouse.move(center_x, center_y)
                            await context.page.mouse.wheel(delta_x, delta_y)
                        else:
                            raise Exception("无法获取元素位置")
                    else:
                        # 在页面中心滚动
                        viewport = context.page.viewport_size
                        if viewport:
                            await context.page.mouse.move(viewport['width'] / 2, viewport['height'] / 2)
                        await context.page.mouse.wheel(delta_x, delta_y)
                    
                    return ModuleResult(success=True, message=f"已滚动 {direction} {distance}px (鼠标滚轮)")
                except Exception as wheel_error:
                    if scroll_mode == 'wheel':
                        raise wheel_error
                    # auto 模式下，滚轮失败则尝试脚本滚动
            
            # 使用 JavaScript 滚动
            if selector:
                await context.page.locator(escape_css_selector(selector)).evaluate(
                    f"el => el.scrollBy({delta_x}, {delta_y})"
                )
            else:
                await context.page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")
            
            return ModuleResult(success=True, message=f"已滚动 {direction} {distance}px")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"滚动页面失败: {str(e)}")

@register_executor
class UploadFileExecutor(ModuleExecutor):
    """上传文件模块执行器"""

    @property
    def module_type(self) -> str:
        return "upload_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get("selector", ""))
        file_path = context.resolve_value(config.get("filePath", ""))
        # 获取超时配置，默认30秒
        timeout_ms = to_int(config.get('timeout', 30000), 30000, context)

        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")

        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")

        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")

        try:
            await context.switch_to_latest_page()

            element = context.page.locator(escape_css_selector(selector))
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            input_type = await element.evaluate("el => el.type || ''")

            if tag_name == "input" and input_type == "file":
                await context.page.set_input_files(selector, file_path)
            else:
                try:
                    async with context.page.expect_file_chooser(timeout=timeout_ms) as fc_info:
                        await element.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(file_path)
                except Exception:
                    file_inputs = context.page.locator('input[type="file"]:not([webkitdirectory])')
                    count = await file_inputs.count()
                    if count > 0:
                        await file_inputs.last.set_input_files(file_path)
                    else:
                        all_inputs = context.page.locator('input[type="file"]')
                        if await all_inputs.count() > 0:
                            await all_inputs.first.set_input_files(file_path)
                        else:
                            raise Exception("未找到文件上传入口")

            return ModuleResult(success=True, message=f"已上传文件: {file_path}")

        except Exception as e:
            return ModuleResult(success=False, error=f"上传文件失败: {str(e)}")

@register_executor
class DownloadFileExecutor(ModuleExecutor):
    """下载文件模块执行器"""

    @property
    def module_type(self) -> str:
        return "download_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import httpx
        import os
        from urllib.parse import urlparse, unquote
        
        download_mode = context.resolve_value(config.get("downloadMode", "click"))  # 支持变量引用
        trigger_selector = context.resolve_value(config.get("triggerSelector", ""))
        download_url = context.resolve_value(config.get("downloadUrl", ""))
        save_path = context.resolve_value(config.get("savePath", ""))
        file_name = context.resolve_value(config.get("fileName", ""))
        variable_name = config.get("variableName", "")

        try:
            if download_mode == "url":
                if not download_url:
                    return ModuleResult(success=False, error="下载URL不能为空")

                if not file_name:
                    parsed = urlparse(download_url)
                    file_name = unquote(os.path.basename(parsed.path)) or "downloaded_file"

                if save_path:
                    Path(save_path).mkdir(parents=True, exist_ok=True)
                    final_path = Path(save_path) / file_name
                else:
                    downloads_dir = Path("downloads")
                    downloads_dir.mkdir(exist_ok=True)
                    final_path = downloads_dir / file_name

                async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                    response = await client.get(download_url)
                    response.raise_for_status()

                    with open(final_path, "wb") as f:
                        f.write(response.content)

                if variable_name:
                    context.set_variable(variable_name, str(final_path))

                return ModuleResult(
                    success=True,
                    message=f"已下载文件: {final_path}",
                    data=str(final_path),
                )

            else:
                if not trigger_selector:
                    return ModuleResult(success=False, error="触发元素选择器不能为空")

                if context.page is None:
                    return ModuleResult(success=False, error="没有打开的页面")

                await context.switch_to_latest_page()

                async with context.page.expect_download() as download_info:
                    await context.page.click(trigger_selector)

                download = await download_info.value

                if save_path:
                    Path(save_path).mkdir(parents=True, exist_ok=True)
                    if file_name:
                        final_path = Path(save_path) / file_name
                    else:
                        final_path = Path(save_path) / download.suggested_filename
                    await download.save_as(str(final_path))
                else:
                    final_path = await download.path()

                if variable_name:
                    context.set_variable(variable_name, str(final_path))

                return ModuleResult(
                    success=True,
                    message=f"已下载文件: {final_path}",
                    data=str(final_path),
                )

        except Exception as e:
            return ModuleResult(success=False, error=f"下载文件失败: {str(e)}")

@register_executor
class SaveImageExecutor(ModuleExecutor):
    """保存图片模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "save_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        selector = context.resolve_value(config.get('selector', ''))
        save_path = context.resolve_value(config.get('savePath', ''))
        variable_name = config.get('variableName', '')
        
        if not selector:
            return ModuleResult(success=False, error="选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            element = context.page.locator(escape_css_selector(selector))
            src = await element.get_attribute('src')
            
            if src and src.startswith('data:'):
                header, data = src.split(',', 1)
                image_data = base64.b64decode(data)
            else:
                image_data = await element.screenshot()
            
            if save_path:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(image_data)
                final_path = save_path
            else:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    f.write(image_data)
                    final_path = f.name
            
            if variable_name:
                context.set_variable(variable_name, final_path)
            
            return ModuleResult(success=True, message=f"已保存图片: {final_path}", data=final_path)
        
        except Exception as e:
            return ModuleResult(success=False, error=f"保存图片失败: {str(e)}")

@register_executor
class GetChildElementsExecutor(ModuleExecutor):
    """获取子元素列表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "get_child_elements"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        parent_selector = context.resolve_value(config.get('parentSelector', ''))
        variable_name = config.get('variableName', '')
        child_selector = context.resolve_value(config.get('childSelector', '*'))  # 默认获取所有子元素
        # 如果child_selector为空字符串，使用默认值'*'
        if not child_selector:
            child_selector = '*'
        
        if not parent_selector:
            return ModuleResult(success=False, error="父元素选择器不能为空")
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            # 等待父元素出现
            await context.page.wait_for_selector(escape_css_selector(parent_selector), state='attached')
            
            # 使用JavaScript获取子元素的选择器
            child_selectors = await context.page.evaluate("""
                (args) => {
                    const { parentSelector, childSelector } = args;
                    const parent = document.querySelector(parentSelector);
                    if (!parent) return [];
                    
                    // 获取直接子元素
                    const children = childSelector === '*' 
                        ? Array.from(parent.children)
                        : Array.from(parent.querySelectorAll(':scope > ' + childSelector));
                    
                    // 获取父元素的所有子元素（用于计算正确的nth-child）
                    const allChildren = Array.from(parent.children);
                    
                    // 为每个子元素生成唯一的选择器
                    return children.map((child) => {
                        // 尝试使用ID
                        if (child.id) {
                            return '#' + child.id;
                        }
                        
                        // 尝试使用class（检查在父元素下是否唯一）
                        if (child.className && typeof child.className === 'string') {
                            const classes = child.className.trim().split(/\\s+/).filter(c => c);
                            if (classes.length > 0) {
                                const classSelector = '.' + classes.join('.');
                                // 检查在父元素的直接子元素中是否唯一
                                const matches = parent.querySelectorAll(':scope > ' + classSelector);
                                if (matches.length === 1) {
                                    return parentSelector + ' > ' + classSelector;
                                }
                            }
                        }
                        
                        // 使用nth-child（基于在所有子元素中的实际位置）
                        const actualIndex = allChildren.indexOf(child);
                        const tagName = child.tagName.toLowerCase();
                        return parentSelector + ' > ' + tagName + ':nth-child(' + (actualIndex + 1) + ')';
                    });
                }
            """, {
                'parentSelector': parent_selector,
                'childSelector': child_selector
            })
            
            # 保存到变量
            context.set_variable(variable_name, child_selectors)
            
            return ModuleResult(
                success=True, 
                message=f"已获取 {len(child_selectors)} 个子元素，保存到变量 {variable_name}",
                data=child_selectors
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"获取子元素列表失败: {str(e)}")

@register_executor
class GetSiblingElementsExecutor(ModuleExecutor):
    """获取兄弟元素列表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "get_sibling_elements"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        element_selector = context.resolve_value(config.get('elementSelector', ''))
        variable_name = config.get('variableName', '')
        include_self = config.get('includeSelf', False)  # 是否包含自身
        sibling_type = context.resolve_value(config.get('siblingType', 'all'))  # all, previous, next
        # 如果sibling_type为空字符串，使用默认值'all'
        if not sibling_type:
            sibling_type = 'all'
        
        if not element_selector:
            return ModuleResult(success=False, error="元素选择器不能为空")
        
        if not variable_name:
            return ModuleResult(success=False, error="变量名不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            await context.switch_to_latest_page()
            
            # 等待元素出现
            await context.page.wait_for_selector(escape_css_selector(element_selector), state='attached')
            
            # 使用JavaScript获取兄弟元素的选择器
            sibling_selectors = await context.page.evaluate("""
                (args) => {
                    const { elementSelector, includeSelf, siblingType } = args;
                    const element = document.querySelector(elementSelector);
                    if (!element || !element.parentElement) return [];
                    
                    const parent = element.parentElement;
                    const allSiblings = Array.from(parent.children);
                    const elementIndex = allSiblings.indexOf(element);
                    
                    let siblings = [];
                    if (siblingType === 'previous') {
                        // 只获取前面的兄弟元素
                        siblings = allSiblings.slice(0, elementIndex);
                    } else if (siblingType === 'next') {
                        // 只获取后面的兄弟元素
                        siblings = allSiblings.slice(elementIndex + 1);
                    } else {
                        // 获取所有兄弟元素
                        siblings = allSiblings.filter((sibling, index) => 
                            includeSelf ? true : index !== elementIndex
                        );
                    }
                    
                    // 为每个兄弟元素生成唯一的选择器
                    return siblings.map((sibling) => {
                        // 尝试使用ID
                        if (sibling.id) {
                            return '#' + sibling.id;
                        }
                        
                        // 尝试使用class（检查在整个文档中是否唯一）
                        if (sibling.className && typeof sibling.className === 'string') {
                            const classes = sibling.className.trim().split(/\\s+/).filter(c => c);
                            if (classes.length > 0) {
                                const classSelector = '.' + classes.join('.');
                                // 检查在整个文档中是否唯一
                                const matches = document.querySelectorAll(classSelector);
                                if (matches.length === 1) {
                                    return classSelector;
                                }
                                // 如果不唯一，尝试在父元素下是否唯一
                                const parentMatches = parent.querySelectorAll(':scope > ' + classSelector);
                                if (parentMatches.length === 1) {
                                    // 生成父元素选择器
                                    let parentSelector = '';
                                    if (parent.id) {
                                        parentSelector = '#' + parent.id;
                                    } else if (parent.className && typeof parent.className === 'string') {
                                        const parentClasses = parent.className.trim().split(/\\s+/).filter(c => c);
                                        if (parentClasses.length > 0) {
                                            parentSelector = '.' + parentClasses.join('.');
                                        }
                                    }
                                    if (parentSelector) {
                                        return parentSelector + ' > ' + classSelector;
                                    }
                                }
                            }
                        }
                        
                        // 使用nth-child（基于在所有子元素中的实际位置）
                        const actualIndex = allSiblings.indexOf(sibling);
                        const tagName = sibling.tagName.toLowerCase();
                        
                        // 生成父元素的选择器
                        let parentSelector = '';
                        if (parent.id) {
                            parentSelector = '#' + parent.id;
                        } else if (parent.className && typeof parent.className === 'string') {
                            const classes = parent.className.trim().split(/\\s+/).filter(c => c);
                            if (classes.length > 0) {
                                parentSelector = '.' + classes.join('.');
                            }
                        }
                        
                        if (parentSelector) {
                            return parentSelector + ' > ' + tagName + ':nth-child(' + (actualIndex + 1) + ')';
                        } else {
                            // 如果父元素没有ID或class，尝试生成更完整的路径
                            const parentTagName = parent.tagName.toLowerCase();
                            return parentTagName + ' > ' + tagName + ':nth-child(' + (actualIndex + 1) + ')';
                        }
                    });
                }
            """, {
                'elementSelector': element_selector,
                'includeSelf': include_self,
                'siblingType': sibling_type
            })
            
            # 保存到变量
            context.set_variable(variable_name, sibling_selectors)
            
            type_desc = {
                'all': '所有',
                'previous': '前面的',
                'next': '后面的'
            }.get(sibling_type, '所有')
            
            return ModuleResult(
                success=True, 
                message=f"已获取 {len(sibling_selectors)} 个{type_desc}兄弟元素，保存到变量 {variable_name}",
                data=sibling_selectors
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"获取兄弟元素列表失败: {str(e)}")