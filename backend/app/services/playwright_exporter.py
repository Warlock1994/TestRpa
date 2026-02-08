"""Playwright 代码导出服务 - 将工作流导出为可运行的 Playwright Python 代码

支持的功能：
- 基本的浏览器操作（打开页面、点击、输入等）
- 流程控制（条件判断、循环、子工作流）
- 并行分支执行（使用 asyncio.gather）
- 多线段汇聚
- 变量操作
- 数据处理

注意事项：
- 导出的代码是独立的 Python 脚本，不依赖 WebRPA
- 某些模块（如系统操作、QQ/微信自动化）需要额外的依赖或无法在纯 Playwright 中实现
- 子工作流会被展开为内联函数
"""
from typing import Any, Optional
from datetime import datetime


class PlaywrightExporter:
    """将工作流导出为 Playwright Python 代码"""
    
    def __init__(self):
        self.indent_level = 0
        self.indent_str = "    "
        self.lines: list[str] = []
        self.variables: dict[str, Any] = {}
        self.has_async_operations = True
        self.subflow_definitions: dict[str, list] = {}  # 子工作流定义
        self.node_map: dict = {}
        self.edge_map: dict = {}
        self.all_edges: list = []
    
    def _indent(self) -> str:
        """获取当前缩进"""
        return self.indent_str * self.indent_level
    
    def _add_line(self, line: str = ""):
        """添加一行代码"""
        if line:
            self.lines.append(f"{self._indent()}{line}")
        else:
            self.lines.append("")
    
    def _add_comment(self, comment: str):
        """添加注释"""
        self._add_line(f"# {comment}")
    
    def _escape_string(self, s: str) -> str:
        """转义字符串"""
        if s is None:
            return '""'
        return repr(str(s))
    
    def _resolve_variable_reference(self, value: Any) -> str:
        """解析变量引用，返回 Python 表达式"""
        if value is None:
            return '""'
        if not isinstance(value, str):
            return repr(value)
        
        # 检查是否包含变量引用 {变量名}
        import re
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, value)
        
        if not matches:
            return self._escape_string(value)
        
        # 如果整个字符串就是一个变量引用
        if value == f'{{{matches[0]}}}' and len(matches) == 1:
            var_name = self._sanitize_var_name(matches[0])
            return f'variables.get("{var_name}", "")'
        
        # 包含变量引用的字符串，使用 f-string
        result = value
        for match in matches:
            var_name = self._sanitize_var_name(match)
            result = result.replace(f'{{{match}}}', f'{{variables.get("{var_name}", "")}}')
        return f'f{self._escape_string(result)}'

    def _sanitize_var_name(self, name: str) -> str:
        """清理变量名，确保是有效的 Python 标识符"""
        import re
        # 替换非法字符为下划线
        sanitized = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', name)
        # 如果以数字开头，添加前缀
        if sanitized and sanitized[0].isdigit():
            sanitized = f'var_{sanitized}'
        return sanitized or 'unnamed_var'
    
    def _sanitize_func_name(self, name: str) -> str:
        """清理函数名"""
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if sanitized and sanitized[0].isdigit():
            sanitized = f'subflow_{sanitized}'
        return sanitized or 'unnamed_subflow'
    
    def export(self, workflow_data: dict) -> str:
        """导出工作流为 Playwright Python 代码"""
        self.lines = []
        self.indent_level = 0
        self.subflow_definitions = {}
        
        workflow_name = workflow_data.get('name', '未命名工作流')
        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])
        variables = workflow_data.get('variables', [])
        
        # 构建节点映射
        self.node_map = {node['id']: node for node in nodes}
        self.all_edges = edges
        
        # 构建边的映射
        self.edge_map = {}
        for edge in edges:
            source = edge['source']
            handle = edge.get('sourceHandle', 'default')
            target = edge['target']
            if source not in self.edge_map:
                self.edge_map[source] = {}
            if handle not in self.edge_map[source]:
                self.edge_map[source][handle] = []
            self.edge_map[source][handle].append(target)
        
        # 识别子工作流定义（groupNode with isSubflow=True）
        self._identify_subflows(nodes)
        
        # 构建执行顺序
        execution_order = self._build_execution_order(nodes, edges)
        
        # 生成文件头
        self._generate_header(workflow_name)
        
        # 生成变量初始化
        self._generate_variables(variables)
        
        # 生成子工作流函数
        self._generate_subflow_functions()
        
        # 生成主函数
        self._generate_main_function(execution_order)
        
        # 生成入口点
        self._generate_entry_point()
        
        return '\n'.join(self.lines)
    
    def _identify_subflows(self, nodes: list):
        """识别子工作流定义"""
        for node in nodes:
            if node.get('type') == 'groupNode':
                data = node.get('data', {})
                if data.get('isSubflow') and data.get('subflowName'):
                    subflow_name = data['subflowName']
                    # 找到该分组内的所有节点
                    group_id = node['id']
                    child_nodes = [n for n in nodes if n.get('parentId') == group_id or n.get('parentNode') == group_id]
                    self.subflow_definitions[subflow_name] = {
                        'group_id': group_id,
                        'nodes': child_nodes,
                        'data': data
                    }
    
    def _build_execution_order(self, nodes: list, edges: list) -> list:
        """构建节点执行顺序（拓扑排序）"""
        # 排除子工作流内部的节点（它们会在子工作流调用时执行）
        subflow_node_ids = set()
        for sf_data in self.subflow_definitions.values():
            for n in sf_data['nodes']:
                subflow_node_ids.add(n['id'])
            subflow_node_ids.add(sf_data['group_id'])
        
        # 过滤出主流程的节点
        main_nodes = [n for n in nodes if n['id'] not in subflow_node_ids]
        
        # 构建邻接表和入度表
        adj = {node['id']: [] for node in main_nodes}
        in_degree = {node['id']: 0 for node in main_nodes}
        
        for edge in edges:
            source = edge['source']
            target = edge['target']
            # 只处理主流程的边
            if source in adj and target in in_degree:
                adj[source].append((target, edge.get('sourceHandle')))
                in_degree[target] += 1
        
        # 找到所有入度为0的节点（起始节点）
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            for next_id, handle in adj[node_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)
        
        return result

    def _generate_header(self, workflow_name: str):
        """生成文件头部"""
        self._add_line('"""')
        self._add_line(f'Playwright 自动化脚本 - {workflow_name}')
        self._add_line(f'由 WebRPA 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self._add_line('')
        self._add_line('使用方法:')
        self._add_line('1. 安装依赖: pip install playwright pyperclip')
        self._add_line('2. 安装浏览器: playwright install chromium')
        self._add_line('3. 运行脚本: python this_script.py')
        self._add_line('')
        self._add_line('注意事项:')
        self._add_line('- 某些模块可能需要额外的依赖（如 pandas, openpyxl 等）')
        self._add_line('- 系统操作、QQ/微信自动化等模块需要手动实现')
        self._add_line('- 并行分支会使用 asyncio.gather 执行')
        self._add_line('"""')
        self._add_line('')
        self._add_line('import asyncio')
        self._add_line('import time')
        self._add_line('import json')
        self._add_line('import re')
        self._add_line('import os')
        self._add_line('from pathlib import Path')
        self._add_line('from typing import Any, Optional')
        self._add_line('from playwright.async_api import async_playwright, Page, BrowserContext, Browser')
        self._add_line('')
        self._add_line('')
        self._add_comment('全局变量存储')
        self._add_line('variables: dict = {}')
        self._add_line('page: Optional[Page] = None')
        self._add_line('context: Optional[BrowserContext] = None')
        self._add_line('browser: Optional[Browser] = None')
        self._add_line('')
    
    def _generate_variables(self, variables: list):
        """生成变量初始化代码"""
        self._add_line('def init_variables():')
        self.indent_level += 1
        self._add_line('"""初始化工作流变量"""')
        self._add_line('global variables')
        if variables:
            for var in variables:
                name = var.get('name', '')
                value = var.get('value', '')
                var_type = var.get('type', 'string')
                if name:
                    if var_type == 'number':
                        try:
                            value = float(value) if '.' in str(value) else int(value)
                        except:
                            value = 0
                    elif var_type == 'boolean':
                        value = str(value).lower() in ('true', '1', 'yes')
                    elif var_type == 'array':
                        if isinstance(value, str):
                            try:
                                value = json.loads(value)
                            except:
                                value = []
                    elif var_type == 'object':
                        if isinstance(value, str):
                            try:
                                value = json.loads(value)
                            except:
                                value = {}
                    self._add_line(f'variables["{name}"] = {repr(value)}')
        else:
            self._add_line('pass  # 无预定义变量')
        self.indent_level -= 1
        self._add_line('')
    
    def _generate_subflow_functions(self):
        """生成子工作流函数"""
        for subflow_name, sf_data in self.subflow_definitions.items():
            func_name = self._sanitize_func_name(subflow_name)
            self._add_line(f'async def subflow_{func_name}():')
            self.indent_level += 1
            self._add_line(f'"""子工作流: {subflow_name}"""')
            self._add_line('global variables, page, context, browser')
            self._add_line('')
            
            # 获取子工作流内的节点执行顺序
            nodes = sf_data['nodes']
            if nodes:
                # 构建子工作流内部的执行顺序
                node_ids = {n['id'] for n in nodes}
                internal_edges = [e for e in self.all_edges if e['source'] in node_ids and e['target'] in node_ids]
                
                # 简单的拓扑排序
                adj = {n['id']: [] for n in nodes}
                in_degree = {n['id']: 0 for n in nodes}
                for edge in internal_edges:
                    adj[edge['source']].append(edge['target'])
                    in_degree[edge['target']] += 1
                
                queue = [nid for nid, deg in in_degree.items() if deg == 0]
                order = []
                while queue:
                    nid = queue.pop(0)
                    order.append(nid)
                    for next_id in adj[nid]:
                        in_degree[next_id] -= 1
                        if in_degree[next_id] == 0:
                            queue.append(next_id)
                
                # 生成节点代码
                processed = set()
                for node_id in order:
                    node = self.node_map.get(node_id)
                    if node and node_id not in processed:
                        self._generate_node_code(node, processed)
            else:
                self._add_line('pass  # 空子工作流')
            
            self.indent_level -= 1
            self._add_line('')

    def _generate_main_function(self, execution_order: list):
        """生成主执行函数"""
        self._add_line('async def run_workflow():')
        self.indent_level += 1
        self._add_line('"""执行工作流主逻辑"""')
        self._add_line('global variables, page, context, browser')
        self._add_line('')
        self._add_line('async with async_playwright() as p:')
        self.indent_level += 1
        self._add_comment('启动浏览器（可修改 headless=True 启用无头模式）')
        self._add_line('browser = await p.chromium.launch(headless=False)')
        self._add_line('context = await browser.new_context()')
        self._add_line('page = await context.new_page()')
        self._add_line('')
        self._add_line('try:')
        self.indent_level += 1
        
        # 生成节点代码
        processed = set()
        for node_id in execution_order:
            if node_id in processed:
                continue
            node = self.node_map.get(node_id)
            if node:
                self._generate_node_code(node, processed)
        
        self._add_line('')
        self._add_line('print("✅ 工作流执行完成")')
        
        self.indent_level -= 1
        self._add_line('except Exception as e:')
        self.indent_level += 1
        self._add_line('print(f"❌ 执行出错: {e}")')
        self._add_line('import traceback')
        self._add_line('traceback.print_exc()')
        self._add_line('raise')
        self.indent_level -= 1
        self._add_line('finally:')
        self.indent_level += 1
        self._add_comment('关闭浏览器')
        self._add_line('await context.close()')
        self._add_line('await browser.close()')
        self.indent_level -= 1
        
        self.indent_level -= 1  # async with
        self.indent_level -= 1  # function
        self._add_line('')

    def _generate_node_code(self, node: dict, processed: set):
        """生成单个节点的代码"""
        node_id = node['id']
        if node_id in processed:
            return
        processed.add(node_id)
        
        node_type = node.get('type', '')
        data = node.get('data', {})
        module_type = data.get('moduleType', node_type)
        label = data.get('label', module_type)
        
        # 跳过分组节点（除非是子工作流定义）
        if node_type == 'groupNode':
            if data.get('isSubflow'):
                self._add_comment(f'子工作流定义: {label} (已生成为独立函数)')
            else:
                self._add_comment(f'分组: {label}')
            return
        
        # 添加节点注释
        self._add_line('')
        self._add_comment(f'节点: {label}')
        
        # 根据模块类型生成代码
        generator = getattr(self, f'_gen_{module_type}', None)
        if generator:
            generator(data, node_id, processed)
        else:
            self._add_comment(f'TODO: 不支持的模块类型 "{module_type}"，请手动实现')
            self._add_line('pass')
    
    def _generate_entry_point(self):
        """生成入口点"""
        self._add_line('')
        self._add_line('if __name__ == "__main__":')
        self.indent_level += 1
        self._add_line('init_variables()')
        self._add_line('asyncio.run(run_workflow())')
        self.indent_level -= 1



    # ==================== 浏览器操作模块 ====================
    
    def _gen_open_page(self, data: dict, node_id: str, processed: set):
        """打开网页"""
        url = self._resolve_variable_reference(data.get('url', ''))
        wait_until = data.get('waitUntil', 'load')
        self._add_line(f'await page.goto({url}, wait_until="{wait_until}")')
        self._add_line('print(f"已打开网页: {page.url}")')
    
    def _gen_click_element(self, data: dict, node_id: str, processed: set):
        """点击元素"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        click_type = data.get('clickType', 'single')
        timeout = data.get('timeout', 30000)
        
        self._add_line(f'await page.wait_for_selector({selector}, timeout={timeout})')
        if click_type == 'double':
            self._add_line(f'await page.dblclick({selector})')
        elif click_type == 'right':
            self._add_line(f'await page.click({selector}, button="right")')
        else:
            self._add_line(f'await page.click({selector})')
    
    def _gen_hover_element(self, data: dict, node_id: str, processed: set):
        """悬停元素"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        duration = data.get('hoverDuration', 500)
        self._add_line(f'await page.hover({selector})')
        if duration > 0:
            self._add_line(f'await asyncio.sleep({duration / 1000})')
    
    def _gen_input_text(self, data: dict, node_id: str, processed: set):
        """输入文本"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        text = self._resolve_variable_reference(data.get('text', ''))
        clear_before = data.get('clearBefore', True)
        
        if clear_before:
            self._add_line(f'await page.fill({selector}, "")')
        self._add_line(f'await page.fill({selector}, str({text}))')

    def _gen_get_element_info(self, data: dict, node_id: str, processed: set):
        """获取元素信息"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        attribute = data.get('attribute', 'text')
        variable_name = data.get('variableName', '')
        
        var_name = self._sanitize_var_name(variable_name) if variable_name else 'element_info'
        
        if attribute == 'text':
            self._add_line(f'{var_name} = await page.inner_text({selector})')
        elif attribute == 'innerHTML':
            self._add_line(f'{var_name} = await page.inner_html({selector})')
        elif attribute == 'value':
            self._add_line(f'{var_name} = await page.input_value({selector})')
        elif attribute == 'href':
            self._add_line(f'{var_name} = await page.get_attribute({selector}, "href")')
        elif attribute == 'src':
            self._add_line(f'{var_name} = await page.get_attribute({selector}, "src")')
        else:
            self._add_line(f'{var_name} = await page.get_attribute({selector}, "{attribute}")')
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = {var_name}')
        self._add_line(f'print(f"获取到: {{{var_name}}}")')
    
    def _gen_wait(self, data: dict, node_id: str, processed: set):
        """等待"""
        duration = data.get('duration', 1000)
        if isinstance(duration, str) and '{' in duration:
            duration_expr = self._resolve_variable_reference(duration)
            self._add_line(f'await asyncio.sleep(float({duration_expr}) / 1000)')
        else:
            self._add_line(f'await asyncio.sleep({float(duration) / 1000})')
    
    def _gen_wait_element(self, data: dict, node_id: str, processed: set):
        """等待元素"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        state = data.get('state', 'visible')
        timeout = data.get('timeout', 30000)
        self._add_line(f'await page.wait_for_selector({selector}, state="{state}", timeout={timeout})')
    
    def _gen_close_page(self, data: dict, node_id: str, processed: set):
        """关闭页面"""
        self._add_line('await page.close()')
        self._add_line('page = await context.new_page()')
    
    def _gen_refresh_page(self, data: dict, node_id: str, processed: set):
        """刷新页面"""
        self._add_line('await page.reload()')
    
    def _gen_go_back(self, data: dict, node_id: str, processed: set):
        """后退"""
        self._add_line('await page.go_back()')
    
    def _gen_go_forward(self, data: dict, node_id: str, processed: set):
        """前进"""
        self._add_line('await page.go_forward()')
    
    def _gen_screenshot(self, data: dict, node_id: str, processed: set):
        """截图"""
        save_path = self._resolve_variable_reference(data.get('savePath', 'screenshot.png'))
        full_page = data.get('fullPage', False)
        variable_name = data.get('variableName', '')
        
        self._add_line(f'_screenshot_path = {save_path}')
        self._add_line(f'await page.screenshot(path=_screenshot_path, full_page={full_page})')
        self._add_line('print(f"截图已保存: {_screenshot_path}")')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _screenshot_path')
    
    def _gen_scroll_page(self, data: dict, node_id: str, processed: set):
        """滚动页面"""
        direction = data.get('direction', 'down')
        distance = data.get('distance', 500)
        
        if direction == 'down':
            self._add_line(f'await page.evaluate("window.scrollBy(0, {distance})")')
        elif direction == 'up':
            self._add_line(f'await page.evaluate("window.scrollBy(0, -{distance})")')
        elif direction == 'right':
            self._add_line(f'await page.evaluate("window.scrollBy({distance}, 0)")')
        elif direction == 'left':
            self._add_line(f'await page.evaluate("window.scrollBy(-{distance}, 0)")')

    def _gen_select_dropdown(self, data: dict, node_id: str, processed: set):
        """下拉框选择"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        select_by = data.get('selectBy', 'value')
        value = self._resolve_variable_reference(data.get('value', ''))
        
        if select_by == 'value':
            self._add_line(f'await page.select_option({selector}, value={value})')
        elif select_by == 'label':
            self._add_line(f'await page.select_option({selector}, label={value})')
        elif select_by == 'index':
            self._add_line(f'await page.select_option({selector}, index=int({value}))')
    
    def _gen_set_checkbox(self, data: dict, node_id: str, processed: set):
        """设置复选框"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        checked = data.get('checked', True)
        
        if checked:
            self._add_line(f'await page.check({selector})')
        else:
            self._add_line(f'await page.uncheck({selector})')
    
    def _gen_upload_file(self, data: dict, node_id: str, processed: set):
        """上传文件"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        self._add_line(f'await page.set_input_files({selector}, {file_path})')
    
    def _gen_download_file(self, data: dict, node_id: str, processed: set):
        """下载文件"""
        download_mode = data.get('downloadMode', 'click')
        trigger_selector = self._resolve_variable_reference(data.get('triggerSelector', ''))
        download_url = self._resolve_variable_reference(data.get('downloadUrl', ''))
        save_path = self._resolve_variable_reference(data.get('savePath', ''))
        file_name = self._resolve_variable_reference(data.get('fileName', ''))
        variable_name = data.get('variableName', '')
        
        if download_mode == 'click':
            self._add_line('async with page.expect_download() as download_info:')
            self.indent_level += 1
            self._add_line(f'await page.click({trigger_selector})')
            self.indent_level -= 1
            self._add_line('_download = await download_info.value')
            if save_path or file_name:
                if save_path and file_name:
                    self._add_line(f'_save_path = os.path.join({save_path}, {file_name})')
                elif save_path:
                    self._add_line(f'_save_path = os.path.join({save_path}, _download.suggested_filename)')
                else:
                    self._add_line(f'_save_path = {file_name}')
                self._add_line('await _download.save_as(_save_path)')
                if variable_name:
                    self._add_line(f'variables["{variable_name}"] = _save_path')
            else:
                self._add_line('print(f"文件已下载: {_download.suggested_filename}")')
                if variable_name:
                    self._add_line(f'variables["{variable_name}"] = _download.suggested_filename')
        else:
            self._add_comment('URL 直接下载')
            self._add_line('import httpx')
            self._add_line(f'async with httpx.AsyncClient() as _client:')
            self.indent_level += 1
            self._add_line(f'_response = await _client.get({download_url})')
            if file_name:
                self._add_line(f'_file_name = {file_name}')
            else:
                self._add_line(f'_file_name = str({download_url}).split("/")[-1].split("?")[0] or "downloaded_file"')
            if save_path:
                self._add_line(f'_save_path = os.path.join({save_path}, _file_name)')
            else:
                self._add_line('_save_path = _file_name')
            self._add_line('with open(_save_path, "wb") as _f:')
            self.indent_level += 1
            self._add_line('_f.write(_response.content)')
            self.indent_level -= 1
            if variable_name:
                self._add_line(f'variables["{variable_name}"] = _save_path')
            self._add_line('print(f"文件已下载: {_save_path}")')
            self.indent_level -= 1
    
    def _gen_drag_element(self, data: dict, node_id: str, processed: set):
        """拖拽元素"""
        source = self._resolve_variable_reference(data.get('sourceSelector', ''))
        target = self._resolve_variable_reference(data.get('targetSelector', ''))
        self._add_line(f'await page.drag_and_drop({source}, {target})')

    def _gen_js_script(self, data: dict, node_id: str, processed: set):
        """执行 JavaScript"""
        script = data.get('script', '')
        variable_name = data.get('variableName', '')
        
        escaped_script = script.replace('\\', '\\\\').replace('`', '\\`')
        
        if variable_name:
            var_name = self._sanitize_var_name(variable_name)
            self._add_line(f'{var_name} = await page.evaluate("""{escaped_script}""")')
            self._add_line(f'variables["{variable_name}"] = {var_name}')
        else:
            self._add_line(f'await page.evaluate("""{escaped_script}""")')
    
    def _gen_handle_dialog(self, data: dict, node_id: str, processed: set):
        """处理对话框"""
        action = data.get('action', 'accept')
        prompt_text = self._resolve_variable_reference(data.get('promptText', ''))
        
        self._add_line('def _handle_dialog(dialog):')
        self.indent_level += 1
        if action == 'accept':
            if prompt_text:
                self._add_line(f'asyncio.create_task(dialog.accept({prompt_text}))')
            else:
                self._add_line('asyncio.create_task(dialog.accept())')
        else:
            self._add_line('asyncio.create_task(dialog.dismiss())')
        self.indent_level -= 1
        self._add_line('page.on("dialog", _handle_dialog)')
    
    def _gen_keyboard_action(self, data: dict, node_id: str, processed: set):
        """键盘操作"""
        key_sequence = self._resolve_variable_reference(data.get('keySequence', ''))
        self._add_line(f'await page.keyboard.press({key_sequence})')


    # ==================== 流程控制模块 ====================
    
    def _gen_condition(self, data: dict, node_id: str, processed: set):
        """条件判断"""
        condition_mode = data.get('conditionMode', 'variable')
        
        if condition_mode == 'expression':
            # 表达式模式
            expression = data.get('expression', 'True')
            # 替换变量引用
            import re
            def replace_var(match):
                var_name = match.group(1)
                return f'variables.get("{var_name}", "")'
            condition = re.sub(r'\{([^}]+)\}', replace_var, expression)
        else:
            # 变量比较模式
            variable_name = data.get('variableName', '')
            operator = data.get('operator', 'equals')
            compare_value = self._resolve_variable_reference(data.get('compareValue', ''))
            
            var_expr = f'variables.get("{variable_name}", "")'
            
            op_map = {
                'equals': '==',
                'not_equals': '!=',
                'contains': 'in',
                'not_contains': 'not in',
                'greater': '>',
                'less': '<',
                'greater_equal': '>=',
                'less_equal': '<=',
                'is_empty': '== ""',
                'is_not_empty': '!= ""',
                'is_true': '== True',
                'is_false': '== False',
                'starts_with': '.startswith',
                'ends_with': '.endswith',
            }
            
            op = op_map.get(operator, '==')
            
            if operator in ['is_empty', 'is_not_empty']:
                condition = f'str({var_expr}) {op}'
            elif operator in ['is_true']:
                condition = f'bool({var_expr})'
            elif operator in ['is_false']:
                condition = f'not bool({var_expr})'
            elif operator in ['contains', 'not_contains']:
                condition = f'str({compare_value}) {op} str({var_expr})'
            elif operator in ['starts_with']:
                condition = f'str({var_expr}).startswith(str({compare_value}))'
            elif operator in ['ends_with']:
                condition = f'str({var_expr}).endswith(str({compare_value}))'
            elif operator in ['greater', 'less', 'greater_equal', 'less_equal']:
                condition = f'float({var_expr} or 0) {op} float({compare_value} or 0)'
            else:
                condition = f'str({var_expr}) {op} str({compare_value})'
        
        self._add_line(f'if {condition}:')
        self.indent_level += 1
        
        # 获取 true 和 false 分支的目标节点
        true_targets = self.edge_map.get(node_id, {}).get('true', []) or self.edge_map.get(node_id, {}).get('condition-true', [])
        false_targets = self.edge_map.get(node_id, {}).get('false', []) or self.edge_map.get(node_id, {}).get('condition-false', [])
        
        # 收集 true 分支的所有节点
        if true_targets:
            true_branch_nodes = self._collect_branch_nodes(true_targets, false_targets)
            true_processed = set()
            true_order = self._topological_sort_nodes(true_branch_nodes)
            for target_id in true_order:
                if target_id in self.node_map and target_id not in true_processed:
                    self._generate_node_code(self.node_map[target_id], true_processed)
            # 标记为已处理
            for nid in true_branch_nodes:
                processed.add(nid)
        else:
            self._add_line('pass  # True 分支')
        
        self.indent_level -= 1
        
        # 处理 false 分支
        if false_targets:
            self._add_line('else:')
            self.indent_level += 1
            false_branch_nodes = self._collect_branch_nodes(false_targets, true_targets)
            false_processed = set()
            false_order = self._topological_sort_nodes(false_branch_nodes)
            for target_id in false_order:
                if target_id in self.node_map and target_id not in false_processed:
                    self._generate_node_code(self.node_map[target_id], false_processed)
            # 标记为已处理
            for nid in false_branch_nodes:
                processed.add(nid)
            self.indent_level -= 1

    def _collect_branch_nodes(self, start_nodes: list, other_branch_nodes: list) -> set:
        """收集分支内的所有节点ID（不跨越到另一个分支）"""
        collected = set()
        other_set = set(other_branch_nodes) if other_branch_nodes else set()
        to_visit = list(start_nodes)
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in collected or node_id in other_set:
                continue
            collected.add(node_id)
            
            # 获取该节点的所有后继节点
            node_edges = self.edge_map.get(node_id, {})
            for handle, targets in node_edges.items():
                for target_id in targets:
                    if target_id not in collected and target_id not in other_set:
                        to_visit.append(target_id)
        
        return collected
    
    def _gen_loop(self, data: dict, node_id: str, processed: set):
        """循环"""
        loop_mode = data.get('loopMode', 'count')
        index_variable = data.get('indexVariable', 'loop_index')
        
        if loop_mode == 'count':
            # 次数循环
            loop_count = data.get('loopCount', 1)
            loop_count_expr = self._resolve_variable_reference(loop_count)
            self._add_line(f'for {index_variable} in range(int({loop_count_expr})):')
        elif loop_mode == 'range':
            # 范围循环
            start_value = data.get('startValue', 0)
            end_value = data.get('endValue', 10)
            step_value = data.get('stepValue', 1)
            start_expr = self._resolve_variable_reference(start_value)
            end_expr = self._resolve_variable_reference(end_value)
            step_expr = self._resolve_variable_reference(step_value)
            self._add_line(f'for {index_variable} in range(int({start_expr}), int({end_expr}) + 1, int({step_expr})):')
        elif loop_mode == 'while':
            # 条件循环
            condition_variable = data.get('conditionVariable', '')
            self._add_line(f'while variables.get("{condition_variable}", False):')
        else:
            # 默认次数循环
            loop_count = data.get('loopCount', 1)
            loop_count_expr = self._resolve_variable_reference(loop_count)
            self._add_line(f'for {index_variable} in range(int({loop_count_expr})):')
        
        self.indent_level += 1
        if loop_mode != 'while':
            self._add_line(f'variables["{index_variable}"] = {index_variable}')
        
        # 收集循环体内的所有节点
        loop_targets = self.edge_map.get(node_id, {}).get('loop', []) or self.edge_map.get(node_id, {}).get('loop-body', [])
        done_targets = self.edge_map.get(node_id, {}).get('done', []) or self.edge_map.get(node_id, {}).get('loop-done', [])
        
        if loop_targets:
            # 收集循环体内的所有节点（包括后继节点）
            loop_body_nodes = self._collect_loop_body_node_ids(loop_targets, done_targets)
            
            # 按拓扑顺序生成循环体内的节点
            loop_processed = set()
            loop_order = self._topological_sort_nodes(loop_body_nodes)
            for target_id in loop_order:
                if target_id in self.node_map and target_id not in loop_processed:
                    self._generate_node_code(self.node_map[target_id], loop_processed)
            
            # 标记循环体内的节点为已处理（防止在循环外再次生成）
            for nid in loop_body_nodes:
                processed.add(nid)
        else:
            self._add_line('pass  # 循环体')
        
        self.indent_level -= 1
        
        # 处理循环完成后的节点
        if done_targets:
            for target_id in done_targets:
                if target_id in self.node_map and target_id not in processed:
                    self._generate_node_code(self.node_map[target_id], processed)

    def _gen_foreach(self, data: dict, node_id: str, processed: set):
        """遍历循环"""
        source_variable = data.get('sourceVariable', '')
        item_variable = data.get('itemVariable', 'item')
        index_variable = data.get('indexVariable', 'index')
        
        self._add_line(f'_foreach_list = variables.get("{source_variable}", [])')
        self._add_line('if not isinstance(_foreach_list, list):')
        self.indent_level += 1
        self._add_line('_foreach_list = [_foreach_list]')
        self.indent_level -= 1
        self._add_line(f'for {index_variable}, {item_variable} in enumerate(_foreach_list):')
        self.indent_level += 1
        self._add_line(f'variables["{item_variable}"] = {item_variable}')
        self._add_line(f'variables["{index_variable}"] = {index_variable}')
        
        # 收集循环体内的所有节点
        loop_targets = self.edge_map.get(node_id, {}).get('loop', []) or self.edge_map.get(node_id, {}).get('loop-body', [])
        done_targets = self.edge_map.get(node_id, {}).get('done', []) or self.edge_map.get(node_id, {}).get('loop-done', [])
        
        if loop_targets:
            # 收集循环体内的所有节点
            loop_body_nodes = self._collect_loop_body_node_ids(loop_targets, done_targets)
            
            # 按拓扑顺序生成循环体内的节点
            loop_processed = set()
            loop_order = self._topological_sort_nodes(loop_body_nodes)
            for target_id in loop_order:
                if target_id in self.node_map and target_id not in loop_processed:
                    self._generate_node_code(self.node_map[target_id], loop_processed)
            
            # 标记循环体内的节点为已处理
            for nid in loop_body_nodes:
                processed.add(nid)
        else:
            self._add_line('pass  # 循环体')
        
        self.indent_level -= 1
        
        # 处理循环完成后的节点
        if done_targets:
            for target_id in done_targets:
                if target_id in self.node_map and target_id not in processed:
                    self._generate_node_code(self.node_map[target_id], processed)

    def _collect_loop_body_node_ids(self, start_nodes: list, exclude_nodes: list) -> set:
        """收集循环体内的所有节点ID"""
        collected = set()
        exclude_set = set(exclude_nodes) if exclude_nodes else set()
        to_visit = list(start_nodes)
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in collected or node_id in exclude_set:
                continue
            collected.add(node_id)
            
            # 获取该节点的所有后继节点
            node_edges = self.edge_map.get(node_id, {})
            for handle, targets in node_edges.items():
                # 跳过 done/loop-done 分支（这些是循环外的）
                if handle in ('done', 'loop-done'):
                    continue
                for target_id in targets:
                    if target_id not in collected and target_id not in exclude_set:
                        to_visit.append(target_id)
        
        return collected

    def _topological_sort_nodes(self, node_ids: set) -> list:
        """对节点进行拓扑排序"""
        # 构建邻接表和入度表
        adj = {nid: [] for nid in node_ids}
        in_degree = {nid: 0 for nid in node_ids}
        
        for edge in self.all_edges:
            source = edge['source']
            target = edge['target']
            handle = edge.get('sourceHandle', 'default')
            # 只处理循环体内的边，跳过 done 分支
            if source in node_ids and target in node_ids and handle not in ('done', 'loop-done'):
                adj[source].append(target)
                in_degree[target] += 1
        
        # 拓扑排序
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            for next_id in adj[node_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)
        
        # 如果有环或未处理的节点，添加到结果末尾
        for nid in node_ids:
            if nid not in result:
                result.append(nid)
        
        return result
    
    def _gen_break_loop(self, data: dict, node_id: str, processed: set):
        """跳出循环"""
        self._add_line('break')
    
    def _gen_continue_loop(self, data: dict, node_id: str, processed: set):
        """跳过当前循环"""
        self._add_line('continue')
    
    def _gen_subflow(self, data: dict, node_id: str, processed: set):
        """调用子工作流"""
        subflow_name = data.get('subflowName', '')
        
        if subflow_name and subflow_name in self.subflow_definitions:
            func_name = self._sanitize_func_name(subflow_name)
            self._add_line(f'await subflow_{func_name}()')
        else:
            self._add_comment(f'警告: 找不到子工作流 "{subflow_name}"')
            self._add_line('pass')
    
    def _gen_group(self, data: dict, node_id: str, processed: set):
        """分组节点 - 仅作为注释"""
        label = data.get('label', '分组')
        is_subflow = data.get('isSubflow', False)
        if is_subflow:
            self._add_comment(f'=== 子工作流定义: {label} ===')
        else:
            self._add_comment(f'=== {label} ===')


    # ==================== 变量与数据操作模块 ====================
    
    def _gen_set_variable(self, data: dict, node_id: str, processed: set):
        """设置变量"""
        variable_name = data.get('variableName', '')
        value = self._resolve_variable_reference(data.get('variableValue', ''))
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = {value}')
    
    def _gen_print_log(self, data: dict, node_id: str, processed: set):
        """打印日志"""
        message = self._resolve_variable_reference(data.get('logMessage', ''))
        log_level = data.get('logLevel', 'info')
        prefix = {'info': 'ℹ️', 'success': '✅', 'warning': '⚠️', 'error': '❌'}.get(log_level, '')
        self._add_line(f'print(f"{prefix} " + str({message}))')
    
    def _gen_input_prompt(self, data: dict, node_id: str, processed: set):
        """用户输入提示 - 支持所有输入模式"""
        input_mode = data.get('inputMode', 'single')
        variable_name = data.get('variableName', '')
        prompt_title = data.get('promptTitle', '请输入')
        prompt_message = data.get('promptMessage', '')
        default_value = self._resolve_variable_reference(data.get('defaultValue', ''))
        
        # 构建提示文本
        prompt_parts = []
        if prompt_title:
            prompt_parts.append(str(prompt_title))
        if prompt_message:
            prompt_parts.append(str(prompt_message))
        prompt_text = ' - '.join(prompt_parts) if prompt_parts else '请输入'
        
        if not variable_name:
            self._add_line(f'input("{prompt_text}")')
            return
        
        var_name = self._sanitize_var_name(variable_name)
        
        if input_mode == 'single':
            self._add_line(f'_{var_name}_input = input("{prompt_text} (默认: " + str({default_value}) + "): ")')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input if _{var_name}_input else {default_value}')
        
        elif input_mode == 'multiline':
            self._add_line(f'print("{prompt_text} (输入空行结束):")')
            self._add_line(f'_{var_name}_lines = []')
            self._add_line('while True:')
            self.indent_level += 1
            self._add_line('_line = input()')
            self._add_line('if not _line:')
            self.indent_level += 1
            self._add_line('break')
            self.indent_level -= 1
            self._add_line(f'_{var_name}_lines.append(_line)')
            self.indent_level -= 1
            self._add_line(f'variables["{variable_name}"] = "\\n".join(_{var_name}_lines) if _{var_name}_lines else {default_value}')
        
        elif input_mode == 'number':
            self._add_line(f'_{var_name}_input = input("{prompt_text} (数字, 默认: " + str({default_value}) + "): ")')
            self._add_line('try:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = float(_{var_name}_input) if _{var_name}_input else float({default_value} or 0)')
            self.indent_level -= 1
            self._add_line('except ValueError:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = float({default_value} or 0)')
            self.indent_level -= 1
        
        elif input_mode == 'integer':
            self._add_line(f'_{var_name}_input = input("{prompt_text} (整数, 默认: " + str({default_value}) + "): ")')
            self._add_line('try:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = int(_{var_name}_input) if _{var_name}_input else int({default_value} or 0)')
            self.indent_level -= 1
            self._add_line('except ValueError:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = int({default_value} or 0)')
            self.indent_level -= 1
        
        elif input_mode == 'password':
            self._add_line('import getpass')
            self._add_line(f'_{var_name}_input = getpass.getpass("{prompt_text}: ")')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input if _{var_name}_input else {default_value}')
        
        elif input_mode == 'list':
            self._add_line(f'print("{prompt_text} (每行一个元素，输入空行结束):")')
            self._add_line(f'_{var_name}_lines = []')
            self._add_line('while True:')
            self.indent_level += 1
            self._add_line('_line = input()')
            self._add_line('if not _line:')
            self.indent_level += 1
            self._add_line('break')
            self.indent_level -= 1
            self._add_line(f'_{var_name}_lines.append(_line)')
            self.indent_level -= 1
            self._add_line(f'variables["{variable_name}"] = _{var_name}_lines if _{var_name}_lines else []')
        
        elif input_mode == 'file':
            self._add_line(f'print("{prompt_text}")')
            self._add_line('try:')
            self.indent_level += 1
            self._add_line('import tkinter as tk')
            self._add_line('from tkinter import filedialog')
            self._add_line('_root = tk.Tk()')
            self._add_line('_root.withdraw()')
            self._add_line(f'_{var_name}_path = filedialog.askopenfilename(title="{prompt_title}")')
            self._add_line('_root.destroy()')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_path if _{var_name}_path else {default_value}')
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line(f'_{var_name}_input = input("请输入文件路径 (默认: " + str({default_value}) + "): ")')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input if _{var_name}_input else {default_value}')
            self.indent_level -= 1
        
        elif input_mode == 'folder':
            self._add_line(f'print("{prompt_text}")')
            self._add_line('try:')
            self.indent_level += 1
            self._add_line('import tkinter as tk')
            self._add_line('from tkinter import filedialog')
            self._add_line('_root = tk.Tk()')
            self._add_line('_root.withdraw()')
            self._add_line(f'_{var_name}_path = filedialog.askdirectory(title="{prompt_title}")')
            self._add_line('_root.destroy()')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_path if _{var_name}_path else {default_value}')
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line(f'_{var_name}_input = input("请输入文件夹路径 (默认: " + str({default_value}) + "): ")')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input if _{var_name}_input else {default_value}')
            self.indent_level -= 1
        
        elif input_mode == 'checkbox':
            self._add_line(f'_{var_name}_input = input("{prompt_text} (y/n, 默认: " + str({default_value}) + "): ").lower()')
            self._add_line(f'if _{var_name}_input:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input in ("y", "yes", "true", "1")')
            self.indent_level -= 1
            self._add_line('else:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = str({default_value}).lower() in ("true", "1", "yes")')
            self.indent_level -= 1
        
        elif input_mode in ('slider_int', 'slider_float'):
            min_val = data.get('minValue', 0)
            max_val = data.get('maxValue', 100)
            self._add_line(f'_{var_name}_input = input("{prompt_text} ({min_val}-{max_val}, 默认: " + str({default_value}) + "): ")')
            self._add_line('try:')
            self.indent_level += 1
            if input_mode == 'slider_int':
                self._add_line(f'_{var_name}_val = int(_{var_name}_input) if _{var_name}_input else int({default_value} or {min_val})')
            else:
                self._add_line(f'_{var_name}_val = float(_{var_name}_input) if _{var_name}_input else float({default_value} or {min_val})')
            self._add_line(f'variables["{variable_name}"] = max({min_val}, min({max_val}, _{var_name}_val))')
            self.indent_level -= 1
            self._add_line('except ValueError:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = {default_value} or {min_val}')
            self.indent_level -= 1
        
        elif input_mode == 'select_single':
            options = data.get('options', [])
            options_str = ', '.join([f'"{opt}"' for opt in options]) if options else '"选项1", "选项2"'
            self._add_line(f'_options = [{options_str}]')
            self._add_line(f'print("{prompt_text}")')
            self._add_line('for _i, _opt in enumerate(_options):')
            self.indent_level += 1
            self._add_line('print(f"  {_i + 1}. {_opt}")')
            self.indent_level -= 1
            self._add_line(f'_{var_name}_input = input("请输入选项编号 (默认: 1): ")')
            self._add_line('try:')
            self.indent_level += 1
            self._add_line(f'_{var_name}_idx = int(_{var_name}_input) - 1 if _{var_name}_input else 0')
            self._add_line(f'variables["{variable_name}"] = _options[_{var_name}_idx] if 0 <= _{var_name}_idx < len(_options) else _options[0]')
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = _options[0] if _options else ""')
            self.indent_level -= 1
        
        elif input_mode == 'select_multiple':
            options = data.get('options', [])
            options_str = ', '.join([f'"{opt}"' for opt in options]) if options else '"选项1", "选项2"'
            self._add_line(f'_options = [{options_str}]')
            self._add_line(f'print("{prompt_text} (输入编号，用逗号分隔)")')
            self._add_line('for _i, _opt in enumerate(_options):')
            self.indent_level += 1
            self._add_line('print(f"  {_i + 1}. {_opt}")')
            self.indent_level -= 1
            self._add_line(f'_{var_name}_input = input("请输入选项编号: ")')
            self._add_line(f'_{var_name}_selected = []')
            self._add_line(f'for _idx_str in _{var_name}_input.split(","):')
            self.indent_level += 1
            self._add_line('try:')
            self.indent_level += 1
            self._add_line('_idx = int(_idx_str.strip()) - 1')
            self._add_line('if 0 <= _idx < len(_options):')
            self.indent_level += 1
            self._add_line(f'_{var_name}_selected.append(_options[_idx])')
            self.indent_level -= 1
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line('pass')
            self.indent_level -= 1
            self.indent_level -= 1
            self._add_line(f'variables["{variable_name}"] = _{var_name}_selected')
        
        else:
            # 默认单行输入
            self._add_line(f'_{var_name}_input = input("{prompt_text}: ")')
            self._add_line(f'variables["{variable_name}"] = _{var_name}_input if _{var_name}_input else {default_value}')
    
    def _gen_play_sound(self, data: dict, node_id: str, processed: set):
        """播放提示音"""
        sound_type = data.get('soundType', 'success')
        self._add_comment(f'播放提示音: {sound_type}')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('import winsound')
        if sound_type == 'success':
            self._add_line('winsound.MessageBeep(winsound.MB_OK)')
        elif sound_type == 'error':
            self._add_line('winsound.MessageBeep(winsound.MB_ICONHAND)')
        elif sound_type == 'warning':
            self._add_line('winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)')
        else:
            self._add_line('winsound.MessageBeep()')
        self.indent_level -= 1
        self._add_line('except:')
        self.indent_level += 1
        self._add_line(f'print("🔔 提示音: {sound_type}")')
        self.indent_level -= 1
    
    def _gen_system_notification(self, data: dict, node_id: str, processed: set):
        """系统通知"""
        title = self._resolve_variable_reference(data.get('title', '通知'))
        message = self._resolve_variable_reference(data.get('message', ''))
        self._add_comment('系统通知')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('from plyer import notification')
        self._add_line(f'notification.notify(title=str({title}), message=str({message}), timeout=5)')
        self.indent_level -= 1
        self._add_line('except ImportError:')
        self.indent_level += 1
        self._add_line(f'print(f"📢 通知: {{{title}}} - {{{message}}}")')
        self.indent_level -= 1
    
    def _gen_set_clipboard(self, data: dict, node_id: str, processed: set):
        """设置剪贴板"""
        content = self._resolve_variable_reference(data.get('content', ''))
        self._add_line('import pyperclip')
        self._add_line(f'pyperclip.copy(str({content}))')
    
    def _gen_get_clipboard(self, data: dict, node_id: str, processed: set):
        """获取剪贴板"""
        variable_name = data.get('variableName', '')
        self._add_line('import pyperclip')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = pyperclip.paste()')


    # ==================== 字符串操作模块 ====================
    
    def _gen_string_replace(self, data: dict, node_id: str, processed: set):
        """字符串替换"""
        input_text = self._resolve_variable_reference(data.get('inputText', ''))
        search_value = self._resolve_variable_reference(data.get('searchValue', ''))
        replace_value = self._resolve_variable_reference(data.get('replaceValue', ''))
        variable_name = data.get('variableName', '')
        replace_mode = data.get('replaceMode', 'text')
        replace_all = data.get('replaceAll', True)
        
        if variable_name:
            if replace_mode == 'regex':
                self._add_line('import re as _re')
                if replace_all:
                    self._add_line(f'variables["{variable_name}"] = _re.sub(str({search_value}), str({replace_value}), str({input_text}))')
                else:
                    self._add_line(f'variables["{variable_name}"] = _re.sub(str({search_value}), str({replace_value}), str({input_text}), count=1)')
            else:
                if replace_all:
                    self._add_line(f'variables["{variable_name}"] = str({input_text}).replace(str({search_value}), str({replace_value}))')
                else:
                    self._add_line(f'variables["{variable_name}"] = str({input_text}).replace(str({search_value}), str({replace_value}), 1)')
    
    def _gen_string_split(self, data: dict, node_id: str, processed: set):
        """字符串分割"""
        input_text = self._resolve_variable_reference(data.get('inputText', ''))
        separator = self._resolve_variable_reference(data.get('separator', ','))
        max_split = data.get('maxSplit', '')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            if max_split and str(max_split).strip():
                max_split_expr = self._resolve_variable_reference(max_split)
                self._add_line(f'variables["{variable_name}"] = str({input_text}).split(str({separator}), int({max_split_expr}))')
            else:
                self._add_line(f'variables["{variable_name}"] = str({input_text}).split(str({separator}))')
    
    def _gen_string_concat(self, data: dict, node_id: str, processed: set):
        """字符串拼接"""
        string1 = self._resolve_variable_reference(data.get('string1', ''))
        string2 = self._resolve_variable_reference(data.get('string2', ''))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = str({string1}) + str({string2})')
    
    def _gen_string_join(self, data: dict, node_id: str, processed: set):
        """字符串连接（列表转字符串）"""
        list_variable = data.get('listVariable', '')
        separator = self._resolve_variable_reference(data.get('separator', ''))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'_list = variables.get("{list_variable}", [])')
            self._add_line(f'variables["{variable_name}"] = str({separator}).join(str(x) for x in _list)')
    
    def _gen_string_trim(self, data: dict, node_id: str, processed: set):
        """字符串去空白"""
        input_text = self._resolve_variable_reference(data.get('inputText', ''))
        trim_mode = data.get('trimMode', 'both')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            if trim_mode == 'both':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).strip()')
            elif trim_mode == 'start':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).lstrip()')
            elif trim_mode == 'end':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).rstrip()')
            elif trim_mode == 'all':
                self._add_line(f'variables["{variable_name}"] = "".join(str({input_text}).split())')
    
    def _gen_string_case(self, data: dict, node_id: str, processed: set):
        """字符串大小写转换"""
        input_text = self._resolve_variable_reference(data.get('inputText', ''))
        case_mode = data.get('caseMode', 'upper')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            if case_mode == 'upper':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).upper()')
            elif case_mode == 'lower':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).lower()')
            elif case_mode == 'capitalize':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).capitalize()')
            elif case_mode == 'title':
                self._add_line(f'variables["{variable_name}"] = str({input_text}).title()')
    
    def _gen_string_substring(self, data: dict, node_id: str, processed: set):
        """字符串截取"""
        input_text = self._resolve_variable_reference(data.get('inputText', ''))
        start_index = self._resolve_variable_reference(data.get('startIndex', 0))
        end_index = data.get('endIndex', '')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            if end_index and str(end_index).strip():
                end_index_expr = self._resolve_variable_reference(end_index)
                self._add_line(f'variables["{variable_name}"] = str({input_text})[int({start_index}):int({end_index_expr})]')
            else:
                self._add_line(f'variables["{variable_name}"] = str({input_text})[int({start_index}):]')
    
    def _gen_regex_extract(self, data: dict, node_id: str, processed: set):
        """正则提取"""
        source_text = self._resolve_variable_reference(data.get('sourceText', '') or data.get('inputText', ''))
        pattern = self._resolve_variable_reference(data.get('pattern', ''))
        variable_name = data.get('variableName', '')
        
        self._add_line(f'_match = re.search(str({pattern}), str({source_text}))')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _match.group(1) if _match and _match.groups() else (_match.group(0) if _match else "")')
    
    def _gen_json_parse(self, data: dict, node_id: str, processed: set):
        """JSON 解析"""
        source_variable = data.get('sourceVariable', '')
        json_path = data.get('jsonPath', '')
        variable_name = data.get('variableName', '')
        
        self._add_line(f'_json_data = variables.get("{source_variable}", {{}})')
        self._add_line('if isinstance(_json_data, str):')
        self.indent_level += 1
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('_json_data = json.loads(_json_data)')
        self.indent_level -= 1
        self._add_line('except:')
        self.indent_level += 1
        self._add_line('pass')
        self.indent_level -= 1
        self.indent_level -= 1
        
        if json_path and variable_name:
            # 简单的 JSON Path 解析
            self._add_comment(f'JSON Path: {json_path}')
            self._add_line(f'_result = _json_data')
            # 解析简单的路径如 $.data.items[0].name
            path_parts = json_path.replace('$', '').strip('.').split('.')
            for part in path_parts:
                if not part:
                    continue
                # 处理数组索引
                if '[' in part:
                    key = part[:part.index('[')]
                    idx = part[part.index('[')+1:part.index(']')]
                    if key:
                        self._add_line(f'_result = _result.get("{key}", []) if isinstance(_result, dict) else _result')
                    self._add_line(f'_result = _result[{idx}] if isinstance(_result, list) and len(_result) > {idx} else None')
                else:
                    self._add_line(f'_result = _result.get("{part}", None) if isinstance(_result, dict) else None')
            self._add_line(f'variables["{variable_name}"] = _result')
        elif variable_name:
            self._add_line(f'variables["{variable_name}"] = _json_data')
    
    def _gen_base64(self, data: dict, node_id: str, processed: set):
        """Base64编码/解码"""
        operation = data.get('operation', 'encode')
        variable_name = data.get('variableName', '')
        
        self._add_line('import base64')
        
        if operation == 'encode':
            input_text = self._resolve_variable_reference(data.get('inputText', ''))
            if variable_name:
                self._add_line(f'variables["{variable_name}"] = base64.b64encode(str({input_text}).encode()).decode()')
        elif operation == 'decode':
            input_base64 = self._resolve_variable_reference(data.get('inputBase64', ''))
            if variable_name:
                self._add_line(f'variables["{variable_name}"] = base64.b64decode(str({input_base64})).decode()')
        elif operation == 'file_to_base64':
            file_path = self._resolve_variable_reference(data.get('filePath', ''))
            if variable_name:
                self._add_line(f'with open({file_path}, "rb") as _f:')
                self.indent_level += 1
                self._add_line(f'variables["{variable_name}"] = base64.b64encode(_f.read()).decode()')
                self.indent_level -= 1
        elif operation == 'base64_to_file':
            input_base64 = self._resolve_variable_reference(data.get('inputBase64', ''))
            output_path = self._resolve_variable_reference(data.get('outputPath', ''))
            file_name = self._resolve_variable_reference(data.get('fileName', ''))
            if output_path:
                self._add_line(f'_output_path = os.path.join({output_path}, {file_name})')
            else:
                self._add_line(f'_output_path = {file_name}')
            self._add_line('with open(_output_path, "wb") as _f:')
            self.indent_level += 1
            self._add_line(f'_f.write(base64.b64decode(str({input_base64})))')
            self.indent_level -= 1
            if variable_name:
                self._add_line(f'variables["{variable_name}"] = _output_path')
    
    def _gen_random_number(self, data: dict, node_id: str, processed: set):
        """随机数"""
        min_val = data.get('minValue', 0)
        max_val = data.get('maxValue', 100)
        variable_name = data.get('variableName', '')
        
        self._add_line('import random')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = random.randint({min_val}, {max_val})')
    
    def _gen_get_time(self, data: dict, node_id: str, processed: set):
        """获取时间"""
        time_format = data.get('format', '%Y-%m-%d %H:%M:%S')
        variable_name = data.get('variableName', '')
        
        self._add_line('from datetime import datetime as _dt')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _dt.now().strftime("{time_format}")')


    # ==================== 列表与字典操作模块 ====================
    
    def _gen_list_operation(self, data: dict, node_id: str, processed: set):
        """列表操作"""
        operation = data.get('operation', 'append')
        list_variable = data.get('listVariable', '')
        value = self._resolve_variable_reference(data.get('value', ''))
        
        self._add_line(f'if "{list_variable}" not in variables:')
        self.indent_level += 1
        self._add_line(f'variables["{list_variable}"] = []')
        self.indent_level -= 1
        
        if operation == 'append':
            self._add_line(f'variables["{list_variable}"].append({value})')
        elif operation == 'remove':
            self._add_line(f'if {value} in variables["{list_variable}"]:')
            self.indent_level += 1
            self._add_line(f'variables["{list_variable}"].remove({value})')
            self.indent_level -= 1
        elif operation == 'clear':
            self._add_line(f'variables["{list_variable}"] = []')
    
    def _gen_list_get(self, data: dict, node_id: str, processed: set):
        """获取列表元素"""
        list_variable = data.get('listVariable', '')
        index = self._resolve_variable_reference(data.get('index', 0))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'_list = variables.get("{list_variable}", [])')
            self._add_line(f'_idx = int({index})')
            self._add_line(f'variables["{variable_name}"] = _list[_idx] if -len(_list) <= _idx < len(_list) else None')
    
    def _gen_list_length(self, data: dict, node_id: str, processed: set):
        """获取列表长度"""
        list_variable = data.get('listVariable', '')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = len(variables.get("{list_variable}", []))')
    
    def _gen_list_export(self, data: dict, node_id: str, processed: set):
        """列表导出为文本文件"""
        list_variable = data.get('listVariable', '')
        output_path = self._resolve_variable_reference(data.get('outputPath', ''))
        separator = data.get('separator', '\n')
        encoding = data.get('encoding', 'utf-8')
        append_mode = data.get('appendMode', False)
        
        mode = '"a"' if append_mode else '"w"'
        sep_repr = repr(separator)
        
        self._add_line(f'_list = variables.get("{list_variable}", [])')
        self._add_line(f'with open({output_path}, {mode}, encoding="{encoding}") as _f:')
        self.indent_level += 1
        self._add_line(f'_f.write({sep_repr}.join(str(x) for x in _list))')
        self.indent_level -= 1
        self._add_line(f'print(f"列表已导出到: {{{output_path}}}")')
    
    def _gen_dict_operation(self, data: dict, node_id: str, processed: set):
        """字典操作"""
        dict_action = data.get('dictAction', 'set')
        dict_variable = data.get('dictVariable', '')
        key = self._resolve_variable_reference(data.get('dictKey', ''))
        value = self._resolve_variable_reference(data.get('dictValue', ''))
        
        self._add_line(f'if "{dict_variable}" not in variables:')
        self.indent_level += 1
        self._add_line(f'variables["{dict_variable}"] = {{}}')
        self.indent_level -= 1
        
        if dict_action == 'set':
            self._add_line(f'variables["{dict_variable}"][{key}] = {value}')
        elif dict_action == 'delete':
            self._add_line(f'variables["{dict_variable}"].pop({key}, None)')
        elif dict_action == 'clear':
            self._add_line(f'variables["{dict_variable}"] = {{}}')
    
    def _gen_dict_get(self, data: dict, node_id: str, processed: set):
        """获取字典值"""
        dict_variable = data.get('dictVariable', '')
        key = self._resolve_variable_reference(data.get('dictKey', ''))
        variable_name = data.get('variableName', '')
        default_value = self._resolve_variable_reference(data.get('defaultValue', ''))
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = variables.get("{dict_variable}", {{}}).get({key}, {default_value})')
    
    def _gen_dict_keys(self, data: dict, node_id: str, processed: set):
        """获取字典键/值/键值对"""
        dict_variable = data.get('dictVariable', '')
        key_type = data.get('keyType', 'keys')
        variable_name = data.get('variableName', '')
        
        if variable_name:
            if key_type == 'keys':
                self._add_line(f'variables["{variable_name}"] = list(variables.get("{dict_variable}", {{}}).keys())')
            elif key_type == 'values':
                self._add_line(f'variables["{variable_name}"] = list(variables.get("{dict_variable}", {{}}).values())')
            elif key_type == 'items':
                self._add_line(f'variables["{variable_name}"] = list(variables.get("{dict_variable}", {{}}).items())')

    # ==================== 数据表格操作模块 ====================
    
    def _gen_table_add_row(self, data: dict, node_id: str, processed: set):
        """表格添加行"""
        row_data = data.get('rowData', '')
        
        self._add_line('if "_table_data" not in variables:')
        self.indent_level += 1
        self._add_line('variables["_table_data"] = []')
        self.indent_level -= 1
        
        if row_data:
            row_data_expr = self._resolve_variable_reference(row_data)
            self._add_line(f'_row_data = {row_data_expr}')
            self._add_line('if isinstance(_row_data, str):')
            self.indent_level += 1
            self._add_line('try:')
            self.indent_level += 1
            self._add_line('_row_data = json.loads(_row_data)')
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line('_row_data = {}')
            self.indent_level -= 1
            self.indent_level -= 1
            self._add_line('variables["_table_data"].append(_row_data if isinstance(_row_data, dict) else {})')
        else:
            self._add_line('variables["_table_data"].append({})')
    
    def _gen_table_set_cell(self, data: dict, node_id: str, processed: set):
        """表格设置单元格"""
        row_index = self._resolve_variable_reference(data.get('rowIndex', -1))
        column_name = self._resolve_variable_reference(data.get('columnName', ''))
        value = self._resolve_variable_reference(data.get('cellValue', ''))
        
        self._add_line('if variables.get("_table_data"):')
        self.indent_level += 1
        self._add_line(f'_row_idx = int({row_index})')
        self._add_line('if _row_idx < 0:')
        self.indent_level += 1
        self._add_line('_row_idx = len(variables["_table_data"]) + _row_idx')
        self.indent_level -= 1
        self._add_line('if 0 <= _row_idx < len(variables["_table_data"]):')
        self.indent_level += 1
        self._add_line(f'variables["_table_data"][_row_idx][{column_name}] = {value}')
        self.indent_level -= 1
        self.indent_level -= 1
    
    def _gen_table_get_cell(self, data: dict, node_id: str, processed: set):
        """表格获取单元格"""
        row_index = self._resolve_variable_reference(data.get('rowIndex', 0))
        column_name = self._resolve_variable_reference(data.get('columnName', ''))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line('_table = variables.get("_table_data", [])')
            self._add_line(f'_row_idx = int({row_index})')
            self._add_line('if _row_idx < 0:')
            self.indent_level += 1
            self._add_line('_row_idx = len(_table) + _row_idx')
            self.indent_level -= 1
            self._add_line('if 0 <= _row_idx < len(_table):')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = _table[_row_idx].get({column_name}, "")')
            self.indent_level -= 1
            self._add_line('else:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = ""')
            self.indent_level -= 1
    
    def _gen_table_delete_row(self, data: dict, node_id: str, processed: set):
        """表格删除行"""
        row_index = self._resolve_variable_reference(data.get('rowIndex', -1))
        
        self._add_line('if variables.get("_table_data"):')
        self.indent_level += 1
        self._add_line(f'_row_idx = int({row_index})')
        self._add_line('if _row_idx < 0:')
        self.indent_level += 1
        self._add_line('_row_idx = len(variables["_table_data"]) + _row_idx')
        self.indent_level -= 1
        self._add_line('if 0 <= _row_idx < len(variables["_table_data"]):')
        self.indent_level += 1
        self._add_line('variables["_table_data"].pop(_row_idx)')
        self.indent_level -= 1
        self.indent_level -= 1
    
    def _gen_table_clear(self, data: dict, node_id: str, processed: set):
        """表格清空"""
        self._add_line('variables["_table_data"] = []')
    
    def _gen_table_export(self, data: dict, node_id: str, processed: set):
        """表格导出"""
        export_format = data.get('exportFormat', 'excel')
        save_path = self._resolve_variable_reference(data.get('savePath', ''))
        file_name_pattern = self._resolve_variable_reference(data.get('fileNamePattern', ''))
        variable_name = data.get('variableName', '')
        
        self._add_comment('导出表格数据')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('import pandas as pd')
        self._add_line('from datetime import datetime as _dt')
        self._add_line('_df = pd.DataFrame(variables.get("_table_data", []))')
        
        if file_name_pattern:
            self._add_line(f'_file_name = str({file_name_pattern})')
        else:
            self._add_line('_file_name = f"data_{_dt.now().strftime(\'%Y%m%d_%H%M%S\')}"')
        
        if export_format == 'csv':
            self._add_line('if not _file_name.endswith(".csv"):')
            self.indent_level += 1
            self._add_line('_file_name += ".csv"')
            self.indent_level -= 1
        else:
            self._add_line('if not _file_name.endswith(".xlsx"):')
            self.indent_level += 1
            self._add_line('_file_name += ".xlsx"')
            self.indent_level -= 1
        
        if save_path:
            self._add_line(f'_save_dir = {save_path}')
            self._add_line('os.makedirs(_save_dir, exist_ok=True)')
            self._add_line('_full_path = os.path.join(_save_dir, _file_name)')
        else:
            self._add_line('_full_path = _file_name')
        
        if export_format == 'csv':
            self._add_line('_df.to_csv(_full_path, index=False, encoding="utf-8-sig")')
        else:
            self._add_line('_df.to_excel(_full_path, index=False)')
        
        self._add_line('print(f"数据已导出到: {_full_path}")')
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _full_path')
        
        self.indent_level -= 1
        self._add_line('except ImportError:')
        self.indent_level += 1
        self._add_line('print("导出需要安装 pandas 和 openpyxl: pip install pandas openpyxl")')
        self.indent_level -= 1
    
    def _gen_read_excel(self, data: dict, node_id: str, processed: set):
        """读取 Excel"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        variable_name = data.get('variableName', '')
        sheet_name = data.get('sheetName', '')
        
        self._add_comment('读取 Excel 文件')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('import pandas as pd')
        if sheet_name:
            self._add_line(f'_df = pd.read_excel({file_path}, sheet_name="{sheet_name}")')
        else:
            self._add_line(f'_df = pd.read_excel({file_path})')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _df.to_dict("records")')
        self.indent_level -= 1
        self._add_line('except ImportError:')
        self.indent_level += 1
        self._add_line('print("读取 Excel 需要安装 pandas 和 openpyxl: pip install pandas openpyxl")')
        self.indent_level -= 1


    # ==================== 文件操作模块 ====================
    
    def _gen_read_text_file(self, data: dict, node_id: str, processed: set):
        """读取文本文件"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        variable_name = data.get('variableName', '')
        encoding = data.get('encoding', 'utf-8')
        
        self._add_line(f'with open({file_path}, "r", encoding="{encoding}") as _f:')
        self.indent_level += 1
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _f.read()')
        else:
            self._add_line('_f.read()')
        self.indent_level -= 1
    
    def _gen_write_text_file(self, data: dict, node_id: str, processed: set):
        """写入文本文件"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        content = self._resolve_variable_reference(data.get('content', ''))
        encoding = data.get('encoding', 'utf-8')
        append = data.get('append', False)
        
        mode = '"a"' if append else '"w"'
        self._add_line(f'with open({file_path}, {mode}, encoding="{encoding}") as _f:')
        self.indent_level += 1
        self._add_line(f'_f.write(str({content}))')
        self.indent_level -= 1
    
    def _gen_file_exists(self, data: dict, node_id: str, processed: set):
        """文件是否存在"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = Path({file_path}).exists()')
    
    def _gen_create_folder(self, data: dict, node_id: str, processed: set):
        """创建文件夹"""
        folder_path = self._resolve_variable_reference(data.get('folderPath', ''))
        self._add_line(f'Path({folder_path}).mkdir(parents=True, exist_ok=True)')
    
    def _gen_delete_file(self, data: dict, node_id: str, processed: set):
        """删除文件"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        self._add_line(f'Path({file_path}).unlink(missing_ok=True)')
    
    def _gen_copy_file(self, data: dict, node_id: str, processed: set):
        """复制文件"""
        source = self._resolve_variable_reference(data.get('sourcePath', ''))
        dest = self._resolve_variable_reference(data.get('destPath', ''))
        self._add_line('import shutil')
        self._add_line(f'shutil.copy2({source}, {dest})')
    
    def _gen_move_file(self, data: dict, node_id: str, processed: set):
        """移动文件"""
        source = self._resolve_variable_reference(data.get('sourcePath', ''))
        dest = self._resolve_variable_reference(data.get('destPath', ''))
        self._add_line('import shutil')
        self._add_line(f'shutil.move({source}, {dest})')
    
    def _gen_list_files(self, data: dict, node_id: str, processed: set):
        """列出文件"""
        folder_path = self._resolve_variable_reference(data.get('folderPath', ''))
        pattern = self._resolve_variable_reference(data.get('pattern', '*'))
        variable_name = data.get('variableName', '')
        recursive = data.get('recursive', False)
        
        if variable_name:
            if recursive:
                self._add_line(f'variables["{variable_name}"] = [str(p) for p in Path({folder_path}).rglob({pattern})]')
            else:
                self._add_line(f'variables["{variable_name}"] = [str(p) for p in Path({folder_path}).glob({pattern})]')
    
    def _gen_get_file_info(self, data: dict, node_id: str, processed: set):
        """获取文件信息"""
        file_path = self._resolve_variable_reference(data.get('filePath', ''))
        variable_name = data.get('variableName', '')
        
        if variable_name:
            self._add_line(f'_path = Path({file_path})')
            self._add_line('if _path.exists():')
            self.indent_level += 1
            self._add_line('_stat = _path.stat()')
            self._add_line(f'variables["{variable_name}"] = {{')
            self.indent_level += 1
            self._add_line('"name": _path.name,')
            self._add_line('"path": str(_path.absolute()),')
            self._add_line('"size": _stat.st_size,')
            self._add_line('"is_file": _path.is_file(),')
            self._add_line('"is_dir": _path.is_dir(),')
            self._add_line('"extension": _path.suffix,')
            self.indent_level -= 1
            self._add_line('}')
            self.indent_level -= 1
            self._add_line('else:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = None')
            self.indent_level -= 1
    
    def _gen_run_command(self, data: dict, node_id: str, processed: set):
        """执行命令"""
        command = self._resolve_variable_reference(data.get('command', ''))
        variable_name = data.get('variableName', '')
        
        self._add_line('import subprocess')
        self._add_line(f'_result = subprocess.run(str({command}), shell=True, capture_output=True, text=True)')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _result.stdout')

    # ==================== API 请求模块 ====================
    
    def _gen_api_request(self, data: dict, node_id: str, processed: set):
        """API 请求"""
        url = self._resolve_variable_reference(data.get('requestUrl', ''))
        method = data.get('requestMethod', 'GET')
        headers = data.get('headers', {})
        body = data.get('body', '')
        variable_name = data.get('variableName', '')
        
        self._add_line('import httpx')
        self._add_line('async with httpx.AsyncClient() as _client:')
        self.indent_level += 1
        
        # 构建请求参数
        if headers:
            headers_str = json.dumps(headers) if isinstance(headers, dict) else str(headers)
            self._add_line(f'_headers = {headers_str}')
        else:
            self._add_line('_headers = {}')
        
        if body and method.upper() in ('POST', 'PUT', 'PATCH'):
            body_expr = self._resolve_variable_reference(body)
            self._add_line(f'_body = {body_expr}')
            self._add_line(f'_response = await _client.request("{method}", {url}, headers=_headers, json=_body if isinstance(_body, dict) else None, content=_body if isinstance(_body, str) else None)')
        else:
            self._add_line(f'_response = await _client.request("{method}", {url}, headers=_headers)')
        
        if variable_name:
            self._add_line('try:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = _response.json()')
            self.indent_level -= 1
            self._add_line('except:')
            self.indent_level += 1
            self._add_line(f'variables["{variable_name}"] = _response.text')
            self.indent_level -= 1
        
        self.indent_level -= 1

    # ==================== 不支持或需要手动实现的模块 ====================
    
    def _gen_qq_send_message(self, data: dict, node_id: str, processed: set):
        """QQ发送消息 - 需要手动实现"""
        self._add_comment('QQ发送消息 - 需要配合 NapCat 或其他 QQ 机器人框架实现')
        self._add_comment(f'目标: {data.get("targetId", "")}')
        self._add_comment(f'消息: {data.get("message", "")}')
        self._add_line('pass  # TODO: 实现 QQ 消息发送')
    
    def _gen_wechat_send_message(self, data: dict, node_id: str, processed: set):
        """微信发送消息 - 需要手动实现"""
        self._add_comment('微信发送消息 - 需要配合微信自动化工具实现')
        self._add_line('pass  # TODO: 实现微信消息发送')
    
    def _gen_ai_chat(self, data: dict, node_id: str, processed: set):
        """AI对话 - 需要手动实现"""
        self._add_comment('AI对话 - 需要配置 API Key')
        self._add_line('pass  # TODO: 实现 AI 对话')
    
    def _gen_ocr_captcha(self, data: dict, node_id: str, processed: set):
        """OCR验证码 - 需要手动实现"""
        self._add_comment('OCR验证码识别 - 需要配置 OCR 服务')
        self._add_line('pass  # TODO: 实现 OCR 验证码识别')
    
    def _gen_slider_captcha(self, data: dict, node_id: str, processed: set):
        """滑块验证码 - 需要手动实现"""
        self._add_comment('滑块验证码 - 需要实现滑块识别逻辑')
        self._add_line('pass  # TODO: 实现滑块验证码')
    
    def _gen_scheduled_task(self, data: dict, node_id: str, processed: set):
        """定时任务 - 转换为等待"""
        delay = data.get('delay', 0)
        self._add_comment('定时任务 - 转换为等待')
        if delay:
            self._add_line(f'await asyncio.sleep({delay / 1000})')
    
    def _gen_save_image(self, data: dict, node_id: str, processed: set):
        """保存图片"""
        selector = self._resolve_variable_reference(data.get('selector', ''))
        save_path = self._resolve_variable_reference(data.get('savePath', ''))
        variable_name = data.get('variableName', '')
        
        self._add_line(f'_img_src = await page.get_attribute({selector}, "src")')
        self._add_line('if _img_src:')
        self.indent_level += 1
        self._add_line('import httpx')
        self._add_line('async with httpx.AsyncClient() as _client:')
        self.indent_level += 1
        self._add_line('if _img_src.startswith("data:"):')
        self.indent_level += 1
        self._add_comment('Base64 图片')
        self._add_line('import base64')
        self._add_line('_data = _img_src.split(",", 1)[1]')
        self._add_line(f'with open({save_path}, "wb") as _f:')
        self.indent_level += 1
        self._add_line('_f.write(base64.b64decode(_data))')
        self.indent_level -= 1
        self.indent_level -= 1
        self._add_line('else:')
        self.indent_level += 1
        self._add_line('_response = await _client.get(_img_src)')
        self._add_line(f'with open({save_path}, "wb") as _f:')
        self.indent_level += 1
        self._add_line('_f.write(_response.content)')
        self.indent_level -= 1
        self.indent_level -= 1
        self.indent_level -= 1
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = {save_path}')
        self.indent_level -= 1


    # ==================== 便签/备注模块 ====================
    
    def _gen_note(self, data: dict, node_id: str, processed: set):
        """便签节点 - 仅作为注释"""
        content = data.get('content', '')
        if content:
            for line in content.split('\n'):
                self._add_comment(line)
        else:
            self._add_comment('便签')

    # ==================== 数据库操作模块 ====================
    
    def _gen_db_connect(self, data: dict, node_id: str, processed: set):
        """数据库连接"""
        db_type = data.get('dbType', 'mysql')
        host = self._resolve_variable_reference(data.get('host', 'localhost'))
        port = data.get('port', 3306)
        database = self._resolve_variable_reference(data.get('database', ''))
        username = self._resolve_variable_reference(data.get('username', ''))
        password = self._resolve_variable_reference(data.get('password', ''))
        
        self._add_comment(f'数据库连接 ({db_type})')
        if db_type == 'mysql':
            self._add_line('import pymysql')
            self._add_line(f'_db_conn = pymysql.connect(')
            self.indent_level += 1
            self._add_line(f'host={host},')
            self._add_line(f'port={port},')
            self._add_line(f'database={database},')
            self._add_line(f'user={username},')
            self._add_line(f'password={password},')
            self._add_line('charset="utf8mb4"')
            self.indent_level -= 1
            self._add_line(')')
        elif db_type == 'sqlite':
            self._add_line('import sqlite3')
            self._add_line(f'_db_conn = sqlite3.connect({database})')
        else:
            self._add_comment(f'不支持的数据库类型: {db_type}')
            self._add_line('_db_conn = None')
        self._add_line('variables["_db_connection"] = _db_conn')
    
    def _gen_db_query(self, data: dict, node_id: str, processed: set):
        """数据库查询"""
        sql = self._resolve_variable_reference(data.get('sql', ''))
        variable_name = data.get('variableName', '')
        
        self._add_line('_db_conn = variables.get("_db_connection")')
        self._add_line('if _db_conn:')
        self.indent_level += 1
        self._add_line('_cursor = _db_conn.cursor()')
        self._add_line(f'_cursor.execute({sql})')
        self._add_line('_rows = _cursor.fetchall()')
        self._add_line('_columns = [desc[0] for desc in _cursor.description] if _cursor.description else []')
        self._add_line('_result = [dict(zip(_columns, row)) for row in _rows]')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _result')
        self._add_line('_cursor.close()')
        self.indent_level -= 1
    
    def _gen_db_execute(self, data: dict, node_id: str, processed: set):
        """数据库执行"""
        sql = self._resolve_variable_reference(data.get('sql', ''))
        
        self._add_line('_db_conn = variables.get("_db_connection")')
        self._add_line('if _db_conn:')
        self.indent_level += 1
        self._add_line('_cursor = _db_conn.cursor()')
        self._add_line(f'_cursor.execute({sql})')
        self._add_line('_db_conn.commit()')
        self._add_line('_cursor.close()')
        self.indent_level -= 1
    
    def _gen_db_insert(self, data: dict, node_id: str, processed: set):
        """数据库插入"""
        self._gen_db_execute(data, node_id, processed)
    
    def _gen_db_update(self, data: dict, node_id: str, processed: set):
        """数据库更新"""
        self._gen_db_execute(data, node_id, processed)
    
    def _gen_db_delete(self, data: dict, node_id: str, processed: set):
        """数据库删除"""
        self._gen_db_execute(data, node_id, processed)
    
    def _gen_db_close(self, data: dict, node_id: str, processed: set):
        """关闭数据库连接"""
        self._add_line('_db_conn = variables.get("_db_connection")')
        self._add_line('if _db_conn:')
        self.indent_level += 1
        self._add_line('_db_conn.close()')
        self._add_line('variables["_db_connection"] = None')
        self.indent_level -= 1

    # ==================== 邮件模块 ====================
    
    def _gen_send_email(self, data: dict, node_id: str, processed: set):
        """发送邮件"""
        smtp_server = self._resolve_variable_reference(data.get('smtpServer', ''))
        smtp_port = data.get('smtpPort', 465)
        sender = self._resolve_variable_reference(data.get('sender', ''))
        password = self._resolve_variable_reference(data.get('password', ''))
        recipient = self._resolve_variable_reference(data.get('recipient', ''))
        subject = self._resolve_variable_reference(data.get('subject', ''))
        body = self._resolve_variable_reference(data.get('body', ''))
        
        self._add_comment('发送邮件')
        self._add_line('import smtplib')
        self._add_line('from email.mime.text import MIMEText')
        self._add_line('from email.mime.multipart import MIMEMultipart')
        self._add_line('')
        self._add_line('_msg = MIMEMultipart()')
        self._add_line(f'_msg["From"] = {sender}')
        self._add_line(f'_msg["To"] = {recipient}')
        self._add_line(f'_msg["Subject"] = {subject}')
        self._add_line(f'_msg.attach(MIMEText({body}, "plain", "utf-8"))')
        self._add_line('')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line(f'with smtplib.SMTP_SSL({smtp_server}, {smtp_port}) as _server:')
        self.indent_level += 1
        self._add_line(f'_server.login({sender}, {password})')
        self._add_line(f'_server.send_message(_msg)')
        self.indent_level -= 1
        self._add_line('print("邮件发送成功")')
        self.indent_level -= 1
        self._add_line('except Exception as _e:')
        self.indent_level += 1
        self._add_line('print(f"邮件发送失败: {_e}")')
        self.indent_level -= 1

    # ==================== 系统操作模块 ====================
    
    def _gen_real_mouse_click(self, data: dict, node_id: str, processed: set):
        """真实鼠标点击"""
        x = data.get('x', 0)
        y = data.get('y', 0)
        button = data.get('button', 'left')
        click_type = data.get('clickType', 'single')
        
        self._add_comment('真实鼠标点击 - 需要 pyautogui')
        self._add_line('import pyautogui')
        if click_type == 'double':
            self._add_line(f'pyautogui.doubleClick({x}, {y}, button="{button}")')
        else:
            self._add_line(f'pyautogui.click({x}, {y}, button="{button}")')
    
    def _gen_real_mouse_move(self, data: dict, node_id: str, processed: set):
        """真实鼠标移动"""
        x = data.get('x', 0)
        y = data.get('y', 0)
        duration = data.get('duration', 0.5)
        
        self._add_comment('真实鼠标移动 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'pyautogui.moveTo({x}, {y}, duration={duration})')
    
    def _gen_real_mouse_drag(self, data: dict, node_id: str, processed: set):
        """真实鼠标拖拽"""
        start_x = data.get('startX', 0)
        start_y = data.get('startY', 0)
        end_x = data.get('endX', 0)
        end_y = data.get('endY', 0)
        duration = data.get('duration', 0.5)
        
        self._add_comment('真实鼠标拖拽 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'pyautogui.moveTo({start_x}, {start_y})')
        self._add_line(f'pyautogui.drag({end_x - start_x}, {end_y - start_y}, duration={duration})')
    
    def _gen_real_mouse_scroll(self, data: dict, node_id: str, processed: set):
        """真实鼠标滚轮"""
        clicks = data.get('clicks', 3)
        direction = data.get('direction', 'down')
        
        self._add_comment('真实鼠标滚轮 - 需要 pyautogui')
        self._add_line('import pyautogui')
        scroll_amount = clicks if direction == 'up' else -clicks
        self._add_line(f'pyautogui.scroll({scroll_amount})')
    
    def _gen_real_keyboard(self, data: dict, node_id: str, processed: set):
        """真实键盘输入"""
        text = self._resolve_variable_reference(data.get('text', ''))
        interval = data.get('interval', 0.05)
        
        self._add_comment('真实键盘输入 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'pyautogui.typewrite(str({text}), interval={interval})')
    
    def _gen_shutdown_system(self, data: dict, node_id: str, processed: set):
        """系统关机/重启"""
        action = data.get('action', 'shutdown')
        delay = data.get('delay', 0)
        
        self._add_comment(f'系统操作: {action}')
        self._add_line('import subprocess')
        if action == 'shutdown':
            self._add_line(f'subprocess.run(["shutdown", "/s", "/t", "{delay}"], shell=True)')
        elif action == 'restart':
            self._add_line(f'subprocess.run(["shutdown", "/r", "/t", "{delay}"], shell=True)')
        elif action == 'logout':
            self._add_line('subprocess.run(["shutdown", "/l"], shell=True)')
    
    def _gen_lock_screen(self, data: dict, node_id: str, processed: set):
        """锁定屏幕"""
        self._add_comment('锁定屏幕')
        self._add_line('import ctypes')
        self._add_line('ctypes.windll.user32.LockWorkStation()')
    
    def _gen_window_focus(self, data: dict, node_id: str, processed: set):
        """窗口聚焦"""
        window_title = self._resolve_variable_reference(data.get('windowTitle', ''))
        
        self._add_comment('窗口聚焦 - 需要 pygetwindow')
        self._add_line('import pygetwindow as gw')
        self._add_line(f'_windows = gw.getWindowsWithTitle({window_title})')
        self._add_line('if _windows:')
        self.indent_level += 1
        self._add_line('_windows[0].activate()')
        self.indent_level -= 1
    
    def _gen_get_mouse_position(self, data: dict, node_id: str, processed: set):
        """获取鼠标位置"""
        variable_name = data.get('variableName', '')
        
        self._add_comment('获取鼠标位置 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line('_pos = pyautogui.position()')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = {{"x": _pos.x, "y": _pos.y}}')
    
    def _gen_screenshot_screen(self, data: dict, node_id: str, processed: set):
        """屏幕截图"""
        save_path = self._resolve_variable_reference(data.get('savePath', 'screenshot.png'))
        variable_name = data.get('variableName', '')
        
        self._add_comment('屏幕截图 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'_screenshot = pyautogui.screenshot()')
        self._add_line(f'_screenshot.save({save_path})')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = {save_path}')

    # ==================== 文件重命名模块 ====================
    
    def _gen_rename_file(self, data: dict, node_id: str, processed: set):
        """重命名文件"""
        source_path = self._resolve_variable_reference(data.get('sourcePath', ''))
        new_name = self._resolve_variable_reference(data.get('newName', ''))
        
        self._add_line(f'_source = Path({source_path})')
        self._add_line(f'_new_path = _source.parent / {new_name}')
        self._add_line('_source.rename(_new_path)')
    
    def _gen_rename_folder(self, data: dict, node_id: str, processed: set):
        """重命名文件夹"""
        self._gen_rename_file(data, node_id, processed)

    # ==================== 网络共享模块 ====================
    
    def _gen_share_folder(self, data: dict, node_id: str, processed: set):
        """共享文件夹 - 需要手动实现"""
        self._add_comment('共享文件夹 - 需要启动 HTTP 服务器')
        self._add_line('pass  # TODO: 实现文件夹共享')
    
    def _gen_share_file(self, data: dict, node_id: str, processed: set):
        """共享文件 - 需要手动实现"""
        self._add_comment('共享文件 - 需要启动 HTTP 服务器')
        self._add_line('pass  # TODO: 实现文件共享')
    
    def _gen_stop_share(self, data: dict, node_id: str, processed: set):
        """停止共享"""
        self._add_comment('停止共享')
        self._add_line('pass  # TODO: 实现停止共享')

    # ==================== 媒体处理模块 ====================
    
    def _gen_format_convert(self, data: dict, node_id: str, processed: set):
        """格式转换 - 需要 ffmpeg"""
        self._add_comment('格式转换 - 需要安装 ffmpeg')
        self._add_line('pass  # TODO: 使用 ffmpeg 实现格式转换')
    
    def _gen_compress_image(self, data: dict, node_id: str, processed: set):
        """压缩图片"""
        self._add_comment('压缩图片 - 需要 Pillow')
        self._add_line('pass  # TODO: 使用 Pillow 实现图片压缩')
    
    def _gen_compress_video(self, data: dict, node_id: str, processed: set):
        """压缩视频 - 需要 ffmpeg"""
        self._add_comment('压缩视频 - 需要安装 ffmpeg')
        self._add_line('pass  # TODO: 使用 ffmpeg 实现视频压缩')

    # ==================== 其他模块 ====================
    
    def _gen_export_log(self, data: dict, node_id: str, processed: set):
        """导出日志"""
        save_path = self._resolve_variable_reference(data.get('savePath', 'log.txt'))
        
        self._add_comment('导出日志')
        self._add_line(f'with open({save_path}, "w", encoding="utf-8") as _f:')
        self.indent_level += 1
        self._add_line('_f.write("工作流执行日志\\n")')
        self.indent_level -= 1
    
    def _gen_network_capture(self, data: dict, node_id: str, processed: set):
        """网络抓包 - 需要手动实现"""
        self._add_comment('网络抓包 - 需要配置 Playwright 网络监听')
        self._add_line('pass  # TODO: 实现网络抓包')
    
    def _gen_macro_recorder(self, data: dict, node_id: str, processed: set):
        """宏录制器 - 需要手动实现"""
        self._add_comment('宏录制器 - 需要实现宏回放逻辑')
        self._add_line('pass  # TODO: 实现宏回放')
    
    def _gen_text_to_speech(self, data: dict, node_id: str, processed: set):
        """文字转语音"""
        text = self._resolve_variable_reference(data.get('text', ''))
        
        self._add_comment('文字转语音 - 需要 pyttsx3')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('import pyttsx3')
        self._add_line('_engine = pyttsx3.init()')
        self._add_line(f'_engine.say(str({text}))')
        self._add_line('_engine.runAndWait()')
        self.indent_level -= 1
        self._add_line('except ImportError:')
        self.indent_level += 1
        self._add_line(f'print(f"语音播报: {{{text}}}")')
        self.indent_level -= 1
    
    def _gen_play_music(self, data: dict, node_id: str, processed: set):
        """播放音乐 - 需要手动实现"""
        self._add_comment('播放音乐 - 需要音频播放库')
        self._add_line('pass  # TODO: 实现音乐播放')
    
    def _gen_play_video(self, data: dict, node_id: str, processed: set):
        """播放视频 - 需要手动实现"""
        self._add_comment('播放视频 - 需要视频播放库')
        self._add_line('pass  # TODO: 实现视频播放')
    
    def _gen_view_image(self, data: dict, node_id: str, processed: set):
        """查看图片"""
        image_url = self._resolve_variable_reference(data.get('imageUrl', ''))
        
        self._add_comment('查看图片')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('from PIL import Image')
        self._add_line(f'_img = Image.open({image_url})')
        self._add_line('_img.show()')
        self.indent_level -= 1
        self._add_line('except:')
        self.indent_level += 1
        self._add_line(f'print(f"查看图片: {{{image_url}}}")')
        self.indent_level -= 1
    
    def _gen_click_image(self, data: dict, node_id: str, processed: set):
        """点击图像 - 需要 pyautogui"""
        image_path = self._resolve_variable_reference(data.get('imagePath', ''))
        
        self._add_comment('点击图像 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'_location = pyautogui.locateOnScreen({image_path})')
        self._add_line('if _location:')
        self.indent_level += 1
        self._add_line('_center = pyautogui.center(_location)')
        self._add_line('pyautogui.click(_center)')
        self.indent_level -= 1
    
    def _gen_click_text(self, data: dict, node_id: str, processed: set):
        """点击文本 - 需要 OCR"""
        self._add_comment('点击文本 - 需要 OCR 识别')
        self._add_line('pass  # TODO: 实现 OCR 文本点击')
    
    def _gen_hover_image(self, data: dict, node_id: str, processed: set):
        """悬停图像 - 需要 pyautogui"""
        image_path = self._resolve_variable_reference(data.get('imagePath', ''))
        
        self._add_comment('悬停图像 - 需要 pyautogui')
        self._add_line('import pyautogui')
        self._add_line(f'_location = pyautogui.locateOnScreen({image_path})')
        self._add_line('if _location:')
        self.indent_level += 1
        self._add_line('_center = pyautogui.center(_location)')
        self._add_line('pyautogui.moveTo(_center)')
        self.indent_level -= 1
    
    def _gen_hover_text(self, data: dict, node_id: str, processed: set):
        """悬停文本 - 需要 OCR"""
        self._add_comment('悬停文本 - 需要 OCR 识别')
        self._add_line('pass  # TODO: 实现 OCR 文本悬停')
    
    def _gen_drag_image(self, data: dict, node_id: str, processed: set):
        """拖拽图像 - 需要 pyautogui"""
        self._add_comment('拖拽图像 - 需要 pyautogui')
        self._add_line('pass  # TODO: 实现图像拖拽')
    
    def _gen_image_grayscale(self, data: dict, node_id: str, processed: set):
        """图片灰度化"""
        input_path = self._resolve_variable_reference(data.get('inputPath', ''))
        output_path = self._resolve_variable_reference(data.get('outputPath', ''))
        
        self._add_comment('图片灰度化 - 需要 Pillow')
        self._add_line('from PIL import Image')
        self._add_line(f'_img = Image.open({input_path}).convert("L")')
        self._add_line(f'_img.save({output_path})')
    
    def _gen_image_round_corners(self, data: dict, node_id: str, processed: set):
        """图片圆角化"""
        self._add_comment('图片圆角化 - 需要 Pillow')
        self._add_line('pass  # TODO: 实现图片圆角化')
    
    def _gen_audio_to_text(self, data: dict, node_id: str, processed: set):
        """音频转文字"""
        self._add_comment('音频转文字 - 需要语音识别服务')
        self._add_line('pass  # TODO: 实现音频转文字')
    
    def _gen_qr_generate(self, data: dict, node_id: str, processed: set):
        """生成二维码"""
        content = self._resolve_variable_reference(data.get('content', ''))
        save_path = self._resolve_variable_reference(data.get('savePath', 'qrcode.png'))
        
        self._add_comment('生成二维码 - 需要 qrcode')
        self._add_line('import qrcode')
        self._add_line(f'_qr = qrcode.make({content})')
        self._add_line(f'_qr.save({save_path})')
    
    def _gen_qr_decode(self, data: dict, node_id: str, processed: set):
        """解码二维码"""
        image_path = self._resolve_variable_reference(data.get('imagePath', ''))
        variable_name = data.get('variableName', '')
        
        self._add_comment('解码二维码 - 需要 pyzbar')
        self._add_line('from pyzbar.pyzbar import decode')
        self._add_line('from PIL import Image')
        self._add_line(f'_result = decode(Image.open({image_path}))')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _result[0].data.decode() if _result else ""')
    
    def _gen_screen_record(self, data: dict, node_id: str, processed: set):
        """屏幕录制"""
        self._add_comment('屏幕录制 - 需要 ffmpeg 或 pyautogui')
        self._add_line('pass  # TODO: 实现屏幕录制')
    
    def _gen_face_recognition(self, data: dict, node_id: str, processed: set):
        """人脸识别"""
        self._add_comment('人脸识别 - 需要 face_recognition 库')
        self._add_line('pass  # TODO: 实现人脸识别')
    
    def _gen_image_ocr(self, data: dict, node_id: str, processed: set):
        """图片 OCR"""
        image_path = self._resolve_variable_reference(data.get('imagePath', ''))
        variable_name = data.get('variableName', '')
        
        self._add_comment('图片 OCR - 需要 pytesseract 或其他 OCR 库')
        self._add_line('try:')
        self.indent_level += 1
        self._add_line('import pytesseract')
        self._add_line('from PIL import Image')
        self._add_line(f'_text = pytesseract.image_to_string(Image.open({image_path}), lang="chi_sim+eng")')
        if variable_name:
            self._add_line(f'variables["{variable_name}"] = _text')
        self.indent_level -= 1
        self._add_line('except ImportError:')
        self.indent_level += 1
        self._add_line('print("OCR 需要安装 pytesseract")')
        self.indent_level -= 1


def export_workflow_to_playwright(workflow_data: dict) -> str:
    """导出工作流为 Playwright Python 代码的便捷函数"""
    exporter = PlaywrightExporter()
    return exporter.export(workflow_data)
