"""工作流执行器 - 异步版本，支持真正的并行执行"""
import asyncio
import time
from datetime import datetime
from typing import Optional, Callable, Awaitable
from uuid import uuid4

from app.models.workflow import (
    Workflow,
    WorkflowNode,
    ExecutionResult,
    ExecutionStatus,
    LogLevel,
    LogEntry,
)
from app.executors import ExecutionContext, ModuleResult, registry
from app.services.workflow_parser import WorkflowParser, ExecutionGraph


# 模块默认超时时间配置（毫秒）
# 根据模块实际使用场景设置合理的默认超时
# 超时为0表示不限制超时（非阻塞或需要用户交互的模块）
MODULE_DEFAULT_TIMEOUTS = {
    # 浏览器操作 - 网页加载可能较慢
    'open_page': 60000,        # 60秒
    'click_element': 30000,    # 30秒
    'hover_element': 30000,    # 30秒
    'input_text': 30000,       # 30秒
    'get_element_info': 30000, # 30秒
    'wait': 0,                 # 固定等待不需要超时（由模块内部控制）
    'wait_element': 60000,     # 60秒
    'close_page': 10000,       # 10秒
    'refresh_page': 60000,     # 60秒
    'go_back': 30000,          # 30秒
    'go_forward': 30000,       # 30秒
    'handle_dialog': 30000,    # 30秒
    # 表单操作
    'select_dropdown': 30000,  # 30秒
    'set_checkbox': 30000,     # 30秒
    'drag_element': 30000,     # 30秒
    'scroll_page': 30000,      # 30秒
    'upload_file': 120000,     # 2分钟
    # 数据处理 - 通常很快
    'set_variable': 5000,      # 5秒
    'json_parse': 5000,        # 5秒
    'base64': 10000,           # 10秒
    'random_number': 5000,     # 5秒
    'get_time': 5000,          # 5秒
    'download_file': 300000,   # 5分钟
    'save_image': 60000,       # 1分钟
    'screenshot': 30000,       # 30秒
    'read_excel': 60000,       # 1分钟
    # 字符串操作 - 很快
    'regex_extract': 10000,    # 10秒
    'string_replace': 5000,    # 5秒
    'string_split': 5000,      # 5秒
    'string_join': 5000,       # 5秒
    'string_concat': 5000,     # 5秒
    'string_trim': 5000,       # 5秒
    'string_case': 5000,       # 5秒
    'string_substring': 5000,  # 5秒
    # 列表/字典操作 - 很快
    'list_operation': 10000,   # 10秒
    'list_get': 5000,          # 5秒
    'list_length': 5000,       # 5秒
    'list_export': 60000,      # 1分钟（导出可能较慢）
    'dict_operation': 10000,   # 10秒
    'dict_get': 5000,          # 5秒
    'dict_keys': 5000,         # 5秒
    # 数据表格操作
    'table_add_row': 5000,     # 5秒
    'table_add_column': 5000,  # 5秒
    'table_set_cell': 5000,    # 5秒
    'table_get_cell': 5000,    # 5秒
    'table_delete_row': 5000,  # 5秒
    'table_clear': 5000,       # 5秒
    'table_export': 60000,     # 1分钟
    # 数据库操作
    'db_connect': 30000,       # 30秒
    'db_query': 120000,        # 2分钟
    'db_execute': 120000,      # 2分钟
    'db_insert': 60000,        # 1分钟
    'db_update': 60000,        # 1分钟
    'db_delete': 60000,        # 1分钟
    'db_close': 10000,         # 10秒
    # 网络请求
    'api_request': 120000,     # 2分钟
    'send_email': 60000,       # 1分钟
    # AI能力 - 需要较长时间
    'ai_chat': 180000,         # 3分钟
    'ai_vision': 180000,       # 3分钟
    # 验证码
    'ocr_captcha': 60000,      # 1分钟
    'slider_captcha': 60000,   # 1分钟
    # 流程控制 - 不超时（由内部逻辑控制）
    'condition': 5000,         # 5秒
    'loop': 0,                 # 循环本身不超时
    'foreach': 0,              # 遍历本身不超时
    'break_loop': 5000,        # 5秒
    'continue_loop': 5000,     # 5秒
    'scheduled_task': 0,       # 定时任务不超时
    'subflow': 0,              # 子流程不超时
    # 辅助工具
    'print_log': 5000,         # 5秒
    'play_sound': 10000,       # 10秒
    'system_notification': 5000, # 5秒
    'play_music': 0,           # 不超时（阻塞型，等待用户关闭）
    'play_video': 0,           # 不超时（阻塞型，等待用户关闭）
    'view_image': 0,           # 不超时（阻塞型，等待用户关闭）
    'input_prompt': 0,         # 不超时（阻塞型，等待用户输入）
    'text_to_speech': 120000,  # 2分钟
    'js_script': 60000,        # 1分钟
    'set_clipboard': 5000,     # 5秒
    'get_clipboard': 5000,     # 5秒
    'keyboard_action': 10000,  # 10秒
    'real_mouse_scroll': 10000,# 10秒
    # 系统操作
    'shutdown_system': 30000,  # 30秒
    'lock_screen': 10000,      # 10秒
    'window_focus': 10000,     # 10秒
    'real_mouse_click': 10000, # 10秒
    'real_mouse_move': 10000,  # 10秒
    'real_mouse_drag': 10000,  # 10秒
    'real_keyboard': 30000,    # 30秒
    'run_command': 300000,     # 5分钟
    'click_image': 60000,      # 1分钟
    'click_text': 120000,      # 2分钟（OCR识别较慢，首次需要下载模型）
    'hover_image': 60000,      # 1分钟
    'hover_text': 120000,      # 2分钟（OCR识别较慢）
    'drag_image': 60000,       # 1分钟
    'get_mouse_position': 5000,# 5秒
    'screenshot_screen': 10000,# 10秒
    'rename_file': 10000,      # 10秒
    'network_capture': 0,      # 不超时（非阻塞，后台运行）
    'macro_recorder': 0,       # 不超时（宏播放时间由用户录制内容决定）
    # 网络共享 - 非阻塞（启动服务后立即返回）
    'share_folder': 10000,     # 10秒（启动服务）
    'share_file': 10000,       # 10秒（启动服务）
    'stop_share': 5000,        # 5秒
    # 屏幕共享 - 非阻塞（启动服务后立即返回）
    'start_screen_share': 10000,  # 10秒（启动服务）
    'stop_screen_share': 5000,    # 5秒
    # 文件操作
    'list_files': 30000,       # 30秒
    'copy_file': 300000,       # 5分钟
    'move_file': 300000,       # 5分钟
    'delete_file': 30000,      # 30秒
    'create_folder': 10000,    # 10秒
    'file_exists': 5000,       # 5秒
    'get_file_info': 10000,    # 10秒
    'read_text_file': 60000,   # 1分钟
    'write_text_file': 60000,  # 1分钟
    'rename_folder': 10000,    # 10秒
    # 媒体处理 - FFmpeg操作耗时
    'format_convert': 600000,  # 10分钟
    'compress_image': 120000,  # 2分钟
    'compress_video': 1800000, # 30分钟
    'extract_audio': 300000,   # 5分钟
    'trim_video': 600000,      # 10分钟
    'merge_media': 1800000,    # 30分钟
    'add_watermark': 600000,   # 10分钟
    'download_m3u8': 1800000,  # 30分钟（下载可能很慢）
    'rotate_video': 600000,    # 10分钟
    'video_speed': 600000,     # 10分钟
    'extract_frame': 60000,    # 1分钟
    'add_subtitle': 600000,    # 10分钟
    'adjust_volume': 300000,   # 5分钟
    'resize_video': 600000,    # 10分钟
    # 图像处理
    'image_grayscale': 60000,  # 1分钟
    'image_round_corners': 60000, # 1分钟
    # 音频处理
    'audio_to_text': 300000,   # 5分钟（语音识别可能较慢）
    # 二维码
    'qr_generate': 10000,      # 10秒
    'qr_decode': 30000,        # 30秒
    # 录屏 - 非阻塞（启动后立即返回，后台录制）
    'screen_record': 10000,    # 10秒（启动录屏）
    # AI识别
    'face_recognition': 60000, # 1分钟
    'image_ocr': 60000,        # 1分钟
    # PDF处理
    'pdf_to_images': 300000,   # 5分钟
    'images_to_pdf': 300000,   # 5分钟
    'pdf_merge': 300000,       # 5分钟
    'pdf_split': 300000,       # 5分钟
    'pdf_extract_text': 120000,# 2分钟
    'pdf_extract_images': 300000, # 5分钟
    'pdf_encrypt': 60000,      # 1分钟
    'pdf_decrypt': 60000,      # 1分钟
    'pdf_add_watermark': 300000, # 5分钟
    'pdf_rotate': 120000,      # 2分钟
    'pdf_delete_pages': 120000,# 2分钟
    'pdf_get_info': 30000,     # 30秒
    'pdf_compress': 600000,    # 10分钟
    'pdf_insert_pages': 300000,# 5分钟
    'pdf_reorder_pages': 120000, # 2分钟
    'pdf_to_word': 600000,     # 10分钟
    # 其他
    'export_log': 30000,       # 30秒
    # 触发器模块 - 不超时（等待事件触发）
    'webhook_trigger': 0,      # 不超时（等待webhook请求）
    'hotkey_trigger': 0,       # 不超时（等待热键触发）
    'file_watcher_trigger': 0, # 不超时（等待文件变化）
    'email_trigger': 0,        # 不超时（等待邮件）
    'api_trigger': 0,          # 不超时（等待API请求）
    'mouse_trigger': 0,        # 不超时（等待鼠标事件）
    'image_trigger': 0,        # 不超时（等待图像出现）
    'sound_trigger': 0,        # 不超时（等待声音）
    'face_trigger': 0,         # 不超时（等待人脸）
    'element_change_trigger': 0, # 不超时（等待元素变化）
    # QQ自动化
    'qq_wait_message': 0,      # 不超时（阻塞型，等待消息）
    'qq_send_message': 30000,  # 30秒
    'qq_send_image': 60000,    # 1分钟
    'qq_send_file': 120000,    # 2分钟
    'qq_get_friends': 30000,   # 30秒
    'qq_get_groups': 30000,    # 30秒
    'qq_get_group_members': 30000, # 30秒
    'qq_get_login_info': 10000,# 10秒
    # 微信自动化
    'wechat_wait_message': 0,  # 不超时（阻塞型，等待消息）
    'wechat_send_message': 30000,  # 30秒
    'wechat_send_file': 120000,    # 2分钟
    'wechat_get_messages': 30000,  # 30秒
    'wechat_get_sessions': 30000,  # 30秒
    'wechat_get_login_info': 10000,# 10秒
    # 分组/备注 - 不执行
    'group': 0,
    'note': 0,
}


def get_module_default_timeout(module_type: str) -> int:
    """获取模块默认超时时间（毫秒）"""
    return MODULE_DEFAULT_TIMEOUTS.get(module_type, 30000)


class WorkflowExecutor:
    """工作流执行器 - 使用异步Playwright实现真正的并行执行"""
    
    def __init__(
        self,
        workflow: Workflow,
        on_log: Optional[Callable[[LogEntry], Awaitable[None]]] = None,
        on_node_start: Optional[Callable[[str], Awaitable[None]]] = None,
        on_node_complete: Optional[Callable[[str, ModuleResult], Awaitable[None]]] = None,
        on_variable_update: Optional[Callable[[str, any], Awaitable[None]]] = None,
        on_data_row: Optional[Callable[[dict], Awaitable[None]]] = None,
        headless: bool = False,
        browser_config: Optional[dict] = None,
    ):
        self.workflow = workflow
        self.on_log = on_log
        self.on_node_start = on_node_start
        self.on_node_complete = on_node_complete
        self.on_variable_update = on_variable_update
        self.on_data_row = on_data_row
        self.headless = headless
        self.browser_config = browser_config
        
        self.context = ExecutionContext(headless=headless, browser_config=browser_config)
        self._setup_progress_callback()
        self.graph: Optional[ExecutionGraph] = None
        self.is_running = False
        self.should_stop = False
        
        self.executed_nodes = 0
        self.failed_nodes = 0
        self.start_time: Optional[datetime] = None
        
        self._result: Optional[ExecutionResult] = None
        
        # 并行执行相关
        self._executed_node_ids: set[str] = set()
        self._executing_node_ids: set[str] = set()
        self._node_lock = asyncio.Lock()
        self._pending_nodes: dict[str, set[str]] = {}
        self._last_data_rows_count = 0
        self._sent_data_rows_count = 0
        self._running_tasks: set[asyncio.Task] = set()  # 跟踪所有运行中的任务

    def _setup_progress_callback(self):
        """设置进度回调，让模块执行器可以发送进度日志"""
        async def progress_callback(message: str, level: str = "info"):
            level_map = {
                'info': LogLevel.INFO,
                'warning': LogLevel.WARNING,
                'error': LogLevel.ERROR,
                'success': LogLevel.SUCCESS
            }
            log_level = level_map.get(level, LogLevel.INFO)
            await self._log(log_level, message, is_system_log=True)
        
        self.context._progress_callback = progress_callback
        
        # 设置变量更新回调
        async def variable_update_callback(name: str, value: any):
            await self._notify_variable_update(name, value)
        
        self.context._variable_update_callback = variable_update_callback

    async def _log(self, level: LogLevel, message: str, node_id: Optional[str] = None, 
                   details: Optional[dict] = None, duration: Optional[float] = None,
                   is_user_log: bool = False, is_system_log: bool = False):
        """记录日志"""
        log_details = details.copy() if details else {}
        log_details['is_user_log'] = is_user_log
        log_details['is_system_log'] = is_system_log
        
        entry = LogEntry(
            id=str(uuid4()),
            timestamp=datetime.now(),
            level=level,
            node_id=node_id,
            message=message,
            details=log_details,
            duration=duration,
        )
        
        # 同时存储到 context._logs 中（用于导出日志模块）
        level_str = level.value if hasattr(level, 'value') else str(level)
        timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        self.context.add_log(
            level=level_str,
            message=message,
            node_id=node_id,
            duration=duration,
            timestamp=timestamp_str
        )
        
        if self.on_log:
            try:
                await self.on_log(entry)
            except Exception as e:
                print(f"发送日志失败: {e}")
    
    async def _send_data_row(self, row_data: dict):
        """发送数据行到前端"""
        MAX_PREVIEW_ROWS = 20
        if self._sent_data_rows_count >= MAX_PREVIEW_ROWS:
            return
        if self.on_data_row:
            try:
                await self.on_data_row(row_data)
            except Exception as e:
                print(f"发送数据行失败: {e}")
        self._sent_data_rows_count += 1
    
    async def _notify_node_start(self, node_id: str):
        """通知节点开始执行"""
        if self.on_node_start:
            try:
                await self.on_node_start(node_id)
            except Exception as e:
                print(f"通知节点开始失败: {e}")
    
    async def _notify_node_complete(self, node_id: str, result: ModuleResult):
        """通知节点执行完成"""
        if self.on_node_complete:
            try:
                await self.on_node_complete(node_id, result)
            except Exception as e:
                print(f"通知节点完成失败: {e}")
    
    async def _notify_variable_update(self, name: str, value: any):
        """通知变量更新"""
        if self.on_variable_update:
            try:
                await self.on_variable_update(name, value)
            except Exception as e:
                print(f"通知变量更新失败: {e}")

    async def _execute_parallel(self, node_ids: list[str]):
        """并行执行多个节点分支"""
        if not node_ids or self.should_stop:
            return
        
        # 过滤掉子流程节点（如果已经收集了子流程节点列表）
        if hasattr(self, '_subflow_node_ids'):
            filtered_node_ids = [nid for nid in node_ids if nid not in self._subflow_node_ids]
            if len(filtered_node_ids) < len(node_ids):
                skipped = len(node_ids) - len(filtered_node_ids)
                print(f"[DEBUG] 过滤掉 {skipped} 个子流程节点")
            node_ids = filtered_node_ids
        
        if not node_ids:
            return
        
        async with self._node_lock:
            nodes_to_execute = [
                nid for nid in node_ids 
                if nid not in self._executed_node_ids and nid not in self._executing_node_ids
            ]
            if not nodes_to_execute:
                return
            for nid in nodes_to_execute:
                self._executing_node_ids.add(nid)
        
        # 调试：打印要执行的节点
        for nid in nodes_to_execute:
            node = self.graph.get_node(nid)
            if node:
                label = node.data.get('label', node.type)
                print(f"[DEBUG] 准备执行节点: {nid} ({node.type}: {label})")
        
        if len(nodes_to_execute) == 1:
            if self.should_stop:
                return
            task = asyncio.create_task(self._execute_from_node(nodes_to_execute[0]))
            self._running_tasks.add(task)
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                self._running_tasks.discard(task)
        else:
            await self._log(LogLevel.INFO, f"🔀 检测到 {len(nodes_to_execute)} 个分支，并行执行...")
            tasks = []
            for node_id in nodes_to_execute:
                if self.should_stop:
                    break
                task = asyncio.create_task(self._execute_from_node(node_id))
                self._running_tasks.add(task)
                tasks.append(task)
            
            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except asyncio.CancelledError:
                    pass
                finally:
                    for task in tasks:
                        self._running_tasks.discard(task)
            
            if not self.should_stop:
                await self._log(LogLevel.INFO, f"🔀 {len(nodes_to_execute)} 个分支执行完成")
    
    async def _execute_from_node(self, node_id: str):
        """从指定节点开始执行"""
        if self.should_stop:
            return
        
        async with self._node_lock:
            if node_id in self._executed_node_ids:
                return
            self._executing_node_ids.add(node_id)
        
        node = self.graph.get_node(node_id)
        if not node:
            async with self._node_lock:
                self._executing_node_ids.discard(node_id)
            return
        
        result = await self._execute_node(node)
        
        async with self._node_lock:
            self._executed_node_ids.add(node_id)
            self._executing_node_ids.discard(node_id)
        
        if self.should_stop:
            return
        
        if self.context.should_break:
            return
        
        if self.context.should_continue:
            return
        
        if result and result.branch:
            next_nodes = self.graph.get_next_nodes(node_id, result.branch)
        else:
            next_nodes = self.graph.get_next_nodes(node_id)
        
        # 如果节点执行失败，检查是否有异常处理分支
        if result and not result.success:
            error_nodes = self.graph.get_error_nodes(node_id)
            if error_nodes:
                # 有异常处理分支，执行异常处理流程
                print(f"[DEBUG] 节点 {node.type} 失败，触发异常处理分支")
                await self._log(LogLevel.WARNING, f"⚠️ 节点失败，触发异常处理流程", node_id=node_id)
                await self._execute_parallel(error_nodes)
                return
            else:
                # 没有异常处理分支，对于关键节点停止执行
                if node.type in ('open_page', 'click_element', 'input_text', 'wait_element', 'select_dropdown'):
                    print(f"[DEBUG] 关键节点 {node.type} 失败，停止后续执行")
                    return
        
        if node.type in ('loop', 'foreach'):
            body_nodes = self.graph.get_loop_body_nodes(node_id)
            done_nodes = self.graph.get_loop_done_nodes(node_id)
            await self._handle_loop(node, body_nodes, done_nodes)
        else:
            await self._notify_successors(next_nodes, node_id)


    async def _notify_successors(self, next_nodes: list[str], completed_node_id: str):
        """通知后继节点当前节点已完成"""
        if not next_nodes or self.should_stop:
            return
        
        nodes_ready_to_execute = []
        
        async with self._node_lock:
            for next_id in next_nodes:
                if next_id in self._executed_node_ids or next_id in self._executing_node_ids:
                    continue
                
                prev_nodes = self.graph.get_prev_nodes(next_id)
                
                if len(prev_nodes) <= 1:
                    nodes_ready_to_execute.append(next_id)
                    continue
                
                if next_id not in self._pending_nodes:
                    self._pending_nodes[next_id] = set(
                        pid for pid in prev_nodes if pid not in self._executed_node_ids
                    )
                
                self._pending_nodes[next_id].discard(completed_node_id)
                
                if len(self._pending_nodes[next_id]) == 0:
                    nodes_ready_to_execute.append(next_id)
                    del self._pending_nodes[next_id]
                else:
                    remaining = len(self._pending_nodes[next_id])
                    await self._log(LogLevel.INFO, f"⏳ 等待汇合: 还有 {remaining} 个前驱分支未完成")
        
        if nodes_ready_to_execute:
            await self._execute_parallel(nodes_ready_to_execute)

    async def _execute_node(self, node: WorkflowNode) -> Optional[ModuleResult]:
        """执行单个节点"""
        if self.should_stop:
            return None
        
        # 跳过分组、便签和子流程头节点
        if node.type in ('group', 'note', 'subflow_header'):
            return ModuleResult(success=True, message="跳过")
        
        # 检查节点是否被禁用
        if node.data.get('disabled', False):
            label = node.data.get('label', node.type)
            return ModuleResult(success=True, message=f"已跳过（禁用）")
        
        label = node.data.get('label', node.type)
        print(f"[DEBUG] 开始执行节点: {node.id} ({node.type}: {label})")
        
        await self._notify_node_start(node.id)
        
        executor = registry.get(node.type)
        if not executor:
            print(f"[DEBUG] 未找到执行器: {node.type}")
            await self._log(LogLevel.WARNING, f"未知的模块类型: {node.type}", node_id=node.id)
            return ModuleResult(success=True, message=f"跳过未知模块: {node.type}")
        
        config = node.data.get('config', None)
        if config is None:
            # 配置直接在 node.data 中，而不是在 config 子字段
            config = node.data
        print(f"[DEBUG] 节点配置: {config}")
        
        # 获取超时配置（毫秒）
        # 对于某些模块（如 qq_wait_message），强制使用模块默认超时，忽略节点配置中的 timeout 字段
        # 因为这些模块有自己内部的超时逻辑（如 waitTimeout）
        modules_with_internal_timeout = {'qq_wait_message', 'wechat_wait_message', 'wait', 'loop', 'foreach', 'scheduled_task', 'subflow', 
                                          'play_music', 'play_video', 'view_image', 'input_prompt'}
        
        if node.type in modules_with_internal_timeout:
            # 这些模块强制使用模块默认超时（通常是0，表示无超时限制）
            timeout_ms = get_module_default_timeout(node.type)
        else:
            # 优先使用节点配置的超时，否则使用模块默认超时
            timeout_ms = config.get('timeout')
            if timeout_ms is None:
                timeout_ms = get_module_default_timeout(node.type)
            try:
                timeout_ms = int(timeout_ms)
            except (ValueError, TypeError):
                timeout_ms = get_module_default_timeout(node.type)
        
        # 超时为0表示不限制超时
        if timeout_ms <= 0:
            timeout_seconds = None  # 无超时限制
        else:
            timeout_seconds = timeout_ms / 1000.0
        
        start_time = time.time()
        
        try:
            timeout_display = f"{timeout_seconds}秒" if timeout_seconds else "无限制"
            print(f"[DEBUG] 调用执行器: {node.type}, 超时: {timeout_display}")
            
            # 使用 asyncio.wait_for 来控制超时（如果有超时限制）
            try:
                if timeout_seconds is not None:
                    result = await asyncio.wait_for(
                        executor.execute(config, self.context),
                        timeout=timeout_seconds
                    )
                else:
                    # 无超时限制，直接执行
                    result = await executor.execute(config, self.context)
            except asyncio.TimeoutError:
                duration = (time.time() - start_time) * 1000
                error_msg = f"执行超时 ({timeout_ms}ms)"
                print(f"[ERROR] 节点 {node.id} ({label}) {error_msg}")
                return ModuleResult(success=False, error=error_msg, duration=duration)
            
            print(f"[DEBUG] 执行器返回: success={result.success}, message={result.message}, error={result.error}")
            
            # 处理子流程调用
            if node.type == 'subflow' and result.success and result.data:
                subflow_group_id = result.data.get('subflow_group_id')
                subflow_name = config.get('subflowName', '')
                if subflow_group_id:
                    subflow_result = await self._execute_subflow_group(subflow_group_id, subflow_name)
                    if not subflow_result.success:
                        result = subflow_result
            
            duration = (time.time() - start_time) * 1000
            result.duration = duration
            
            self.executed_nodes += 1
            
            if result.success:
                # 重要模块列表 - 这些模块的日志在简洁模式下也会显示
                # 包括：用户交互、网络请求、文件共享、AI、数据库、邮件、命令执行等
                important_modules = {
                    # 用户交互/输出
                    'print_log',           # 用户打印日志
                    'input_prompt',        # 输入提示 - 显示用户输入
                    'system_notification', # 系统通知
                    'text_to_speech',      # 文字转语音
                    
                    # 网络共享
                    'share_folder',        # 文件夹共享 - 显示访问地址
                    'share_file',          # 文件共享 - 显示访问地址
                    'stop_share',          # 停止共享
                    
                    # 屏幕共享
                    'start_screen_share',  # 开始屏幕共享 - 显示访问地址
                    'stop_screen_share',   # 停止屏幕共享
                    
                    # 网络请求
                    'api_request',         # API请求 - 显示请求结果
                    'send_email',          # 发送邮件 - 显示发送结果
                    
                    # 数据库操作
                    'db_connect',          # 数据库连接 - 显示连接状态
                    'db_query',            # 数据库查询 - 显示查询结果
                    'db_execute',          # 数据库执行 - 显示执行结果
                    'db_insert',           # 数据库插入
                    'db_update',           # 数据库更新
                    'db_delete',           # 数据库删除
                    'db_close',            # 数据库关闭
                    
                    # AI能力
                    'ai_chat',             # AI对话 - 显示AI回复
                    'ai_vision',           # AI视觉 - 显示识别结果
                    
                    # 图像/文本识别点击
                    'click_image',         # 点击图像 - 显示点击结果
                    'click_text',          # 点击文本 - 显示点击结果
                    'hover_image',         # 悬停图像
                    'hover_text',          # 悬停文本
                    'image_ocr',           # OCR识别 - 显示识别结果
                    
                    # 命令/脚本执行
                    'run_command',         # 运行命令 - 显示执行结果
                    'js_script',           # 运行JS脚本
                    
                    # 文件操作
                    'download_file',       # 下载文件 - 显示下载结果
                    'upload_file',         # 上传文件 - 显示上传结果
                    'read_text_file',      # 读取文件 - 显示读取结果
                    'write_text_file',     # 写入文件 - 显示写入结果
                    'copy_file',           # 复制文件
                    'move_file',           # 移动文件
                    'delete_file',         # 删除文件
                    'rename_file',         # 重命名文件
                    
                    # QQ自动化
                    'qq_send_message',     # QQ发送消息
                    'qq_send_image',       # QQ发送图片
                    'qq_send_file',        # QQ发送文件
                    'qq_wait_message',     # QQ等待消息
                    
                    # 微信自动化
                    'wechat_send_message', # 微信发送消息
                    'wechat_send_file',    # 微信发送文件
                    
                    # 子流程
                    'subflow',             # 子流程调用
                    
                    # 录屏
                    'screen_record',       # 录屏
                    
                    # 音频处理
                    'audio_to_text',       # 音频转文字
                    
                    # 导出
                    'export_log',          # 导出日志
                    'table_export',        # 导出表格
                    'list_export',         # 导出列表
                }
                is_user_log = node.type in important_modules
                
                # 触发器模块标记为系统日志
                trigger_modules = {
                    'webhook_trigger',
                    'hotkey_trigger',
                    'file_watcher_trigger',
                    'email_trigger',
                    'api_trigger',
                    'mouse_trigger',
                    'image_trigger',
                    'sound_trigger',
                    'face_trigger',
                    'element_change_trigger',
                }
                is_system_log = node.type in trigger_modules
                
                log_level = LogLevel.INFO
                if node.type == 'print_log' and result.log_level:
                    level_map = {'info': LogLevel.INFO, 'warning': LogLevel.WARNING, 
                                 'error': LogLevel.ERROR, 'success': LogLevel.SUCCESS}
                    log_level = level_map.get(result.log_level, LogLevel.INFO)
                
                await self._log(log_level, f"[{label}] {result.message}", 
                               node_id=node.id, duration=duration, is_user_log=is_user_log, is_system_log=is_system_log)
            else:
                self.failed_nodes += 1
                print(f"[ERROR] 节点失败: {label} - {result.error}")
                await self._log(LogLevel.ERROR, f"[{label}] {result.error}", 
                               node_id=node.id, duration=duration)
            
            current_rows_count = len(self.context.data_rows)
            if current_rows_count > self._last_data_rows_count:
                for i in range(self._last_data_rows_count, current_rows_count):
                    await self._send_data_row(self.context.data_rows[i])
                self._last_data_rows_count = current_rows_count
            
            await self._notify_node_complete(node.id, result)
            return result
            
        except Exception as e:
            import traceback
            duration = (time.time() - start_time) * 1000
            self.failed_nodes += 1
            error_msg = f"执行异常: {str(e)}"
            print(f"[ERROR] 节点 {node.id} ({label}) 执行失败: {e}")
            traceback.print_exc()
            await self._log(LogLevel.ERROR, f"[{label}] {error_msg}", node_id=node.id, duration=duration)
            result = ModuleResult(success=False, error=error_msg, duration=duration)
            await self._notify_node_complete(node.id, result)
            return result

    def _parse_dimension(self, value, default: int = 300) -> int:
        """解析尺寸值，支持数字和字符串（如 '300px'）"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # 移除 'px' 后缀并转换为数字
            try:
                return int(value.replace('px', '').strip())
            except ValueError:
                return default
        return default

    def _get_subflow_node_ids(self) -> set[str]:
        """获取所有子流程分组内的节点ID"""
        subflow_node_ids = set()
        
        # 找出所有子流程分组和子流程头
        subflow_groups = []
        subflow_headers = []
        for node in self.workflow.nodes:
            if node.type == 'group' and node.data.get('isSubflow', False):
                subflow_groups.append(node)
            elif node.type == 'subflow_header':
                subflow_headers.append(node)
        
        # 对于每个子流程分组，找出其范围内的所有节点
        for group in subflow_groups:
            group_x = group.position.x
            group_y = group.position.y
            # 优先从 data 属性获取宽高（前端 NodeResizer 保存的），其次从 style 属性获取
            group_width = group.data.get('width')
            group_height = group.data.get('height')
            if group_width is None or group_height is None:
                style = group.style or {}
                group_width = group_width or style.get('width', 300)
                group_height = group_height or style.get('height', 200)
            # 确保宽高是数字类型
            group_width = self._parse_dimension(group_width, 300)
            group_height = self._parse_dimension(group_height, 200)
            
            for node in self.workflow.nodes:
                if node.id == group.id:
                    continue
                if node.type in ('group', 'note'):
                    continue
                # 检查节点是否在分组范围内
                node_x = node.position.x
                node_y = node.position.y
                if (group_x <= node_x <= group_x + group_width and
                    group_y <= node_y <= group_y + group_height):
                    subflow_node_ids.add(node.id)
        
        # 对于子流程头节点，找出从它开始的所有连接的节点
        for header in subflow_headers:
            # 子流程头节点本身也要排除
            subflow_node_ids.add(header.id)
            header_label = header.data.get('label', header.data.get('subflowName', '未命名'))
            print(f"[DEBUG] 处理子流程头: {header.id}, 名称: {header_label}")
            
            # 从子流程头开始，沿着连接找到所有节点（使用BFS遍历整个子流程图）
            visited = set()
            queue = [header.id]
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                # 获取当前节点信息用于调试
                current_node = next((n for n in self.workflow.nodes if n.id == current_id), None)
                current_label = current_node.data.get('label', current_node.type) if current_node else 'unknown'
                
                # 找到从当前节点出发的所有边
                outgoing_edges = [e for e in self.workflow.edges if e.source == current_id]
                print(f"[DEBUG]   节点 {current_id} ({current_label}) 有 {len(outgoing_edges)} 条出边")
                
                for edge in outgoing_edges:
                    if edge.target not in visited:
                        target_node = next((n for n in self.workflow.nodes if n.id == edge.target), None)
                        if target_node:
                            target_label = target_node.data.get('label', target_node.type)
                            print(f"[DEBUG]     -> 边: {edge.source} -> {edge.target} (类型: {target_node.type}, 标签: {target_label})")
                            if target_node.type not in ('group', 'note', 'subflow_header'):
                                queue.append(edge.target)
                                subflow_node_ids.add(edge.target)
                                print(f"[DEBUG]       ✓ 添加到子流程节点列表")
                            else:
                                print(f"[DEBUG]       ✗ 跳过 (类型: {target_node.type})")
            
            print(f"[DEBUG] 子流程头 {header.id} ({header_label}) 收集到 {len(visited)-1} 个节点")
        
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] 总共收集到 {len(subflow_node_ids)} 个子流程节点")
        for node_id in subflow_node_ids:
            node = next((n for n in self.workflow.nodes if n.id == node_id), None)
            if node:
                label = node.data.get('label', node.type)
                print(f"[DEBUG]   - {node_id}: {node.type} ({label})")
        print(f"[DEBUG] ========================================")
        return subflow_node_ids

    async def _execute_subflow_group(self, group_id: str, subflow_name: str = None) -> ModuleResult:
        """执行子流程分组内的模块"""
        # 找到子流程分组或子流程头 - 优先通过名称查找（因为导入后 ID 会变），ID 作为备用
        group_node = None
        is_header_mode = False
        
        # 优先通过名称查找
        if subflow_name:
            for node in self.workflow.nodes:
                # 查找分组形式的子流程
                if (node.type == 'group' and 
                    node.data.get('isSubflow') == True and 
                    node.data.get('subflowName') == subflow_name):
                    group_node = node
                    break
                # 查找函数头形式的子流程
                elif (node.type == 'subflow_header' and 
                      node.data.get('subflowName') == subflow_name):
                    group_node = node
                    is_header_mode = True
                    break
        
        # 如果通过名称找不到，尝试通过 ID 查找
        if not group_node and group_id:
            for node in self.workflow.nodes:
                if node.id == group_id:
                    if node.type == 'group':
                        group_node = node
                        break
                    elif node.type == 'subflow_header':
                        group_node = node
                        is_header_mode = True
                        break
        
        if not group_node:
            error_msg = f"找不到子流程: {subflow_name or group_id}"
            return ModuleResult(success=False, error=error_msg)
        
        subflow_name = group_node.data.get('subflowName', '子流程')
        await self._log(LogLevel.INFO, f"📦 开始执行子流程 [{subflow_name}]", is_system_log=True)
        
        # 根据模式获取子流程内的节点
        if is_header_mode:
            # 函数头模式：从头节点开始，沿着连接找到所有节点
            nodes_in_group = []
            visited = set()
            queue = [group_node.id]
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                # 找到从当前节点出发的所有边
                for edge in self.workflow.edges:
                    if edge.source == current_id and edge.target not in visited:
                        target_node = next((n for n in self.workflow.nodes if n.id == edge.target), None)
                        if target_node and target_node.type not in ('group', 'note', 'subflow_header'):
                            nodes_in_group.append(target_node)
                            queue.append(edge.target)
        else:
            # 分组模式：获取分组范围内的所有节点
            # 获取分组的位置和大小
            # 优先从 data 属性获取宽高（前端 NodeResizer 保存的），其次从 style 属性获取
            group_x = group_node.position.x
            group_y = group_node.position.y
            group_width = group_node.data.get('width')
            group_height = group_node.data.get('height')
            if group_width is None or group_height is None:
                style = group_node.style or {}
                group_width = group_width or style.get('width', 300)
                group_height = group_height or style.get('height', 200)
            # 确保宽高是数字类型
            group_width = self._parse_dimension(group_width, 300)
            group_height = self._parse_dimension(group_height, 200)
            
            # 调试：打印分组范围
            print(f"[DEBUG] 子流程分组范围: x={group_x}, y={group_y}, width={group_width}, height={group_height}")
            print(f"[DEBUG] 分组 data.width={group_node.data.get('width')}, data.height={group_node.data.get('height')}")
            
            # 找出在分组范围内的所有节点
            nodes_in_group = []
            for node in self.workflow.nodes:
                if node.id == group_node.id:
                    continue
                if node.type in ('group', 'note'):
                    continue
                # 检查节点是否在分组范围内
                node_x = node.position.x
                node_y = node.position.y
                # 节点在分组范围内的判断：节点左上角在分组内
                if (group_x <= node_x <= group_x + group_width and
                    group_y <= node_y <= group_y + group_height):
                    nodes_in_group.append(node)
                    print(f"[DEBUG] 节点在分组内: {node.id} ({node.type}) at ({node_x}, {node_y})")
                else:
                    print(f"[DEBUG] 节点不在分组内: {node.id} ({node.type}) at ({node_x}, {node_y})")
        
        if not nodes_in_group:
            await self._log(LogLevel.WARNING, f"📦 子流程 [{subflow_name}] 为空", is_system_log=True)
            return ModuleResult(success=True, message=f"子流程 [{subflow_name}] 为空")
        
        # 找出子流程内的起始节点（没有入边的节点）
        node_ids_in_group = {n.id for n in nodes_in_group}
        nodes_with_incoming = set()
        for edge in self.workflow.edges:
            if edge.target in node_ids_in_group and edge.source in node_ids_in_group:
                nodes_with_incoming.add(edge.target)
        
        start_nodes = [n for n in nodes_in_group if n.id not in nodes_with_incoming]
        
        if not start_nodes:
            # 如果没有明确的起始节点，按位置排序取第一个
            start_nodes = sorted(nodes_in_group, key=lambda n: (n.position.y, n.position.x))[:1]
        
        # 使用主流程的执行逻辑来执行子流程
        # 保存当前执行状态
        original_executed_ids = self._executed_node_ids.copy()
        original_executing_ids = self._executing_node_ids.copy()
        original_pending_nodes = self._pending_nodes.copy()
        
        # 重置执行状态（仅针对子流程内的节点）
        # 注意：不清空全局状态，只是标记子流程内的节点为未执行
        subflow_executed_ids = set()
        
        try:
            # 执行子流程的起始节点
            start_node_ids = [n.id for n in start_nodes]
            
            # 使用主流程的并行执行逻辑
            await self._execute_parallel_subflow(start_node_ids, node_ids_in_group, subflow_executed_ids)
            
            # 检查是否有错误发生
            subflow_error = None
            for node_id in subflow_executed_ids:
                # 这里无法直接获取执行结果，但如果有错误，主流程会处理
                pass
            
            await self._log(LogLevel.INFO, f"📦 子流程 [{subflow_name}] 执行完成，共执行 {len(subflow_executed_ids)} 个节点", is_system_log=True)
            return ModuleResult(success=True, message=f"子流程 [{subflow_name}] 执行完成")
            
        except Exception as e:
            await self._log(LogLevel.ERROR, f"📦 子流程 [{subflow_name}] 执行失败: {str(e)}", is_system_log=True)
            return ModuleResult(success=False, error=f"子流程执行失败: {str(e)}")
        finally:
            # 恢复原始执行状态（不影响主流程）
            # 注意：子流程执行的节点应该被标记为已执行
            pass
    
    async def _execute_parallel_subflow(self, node_ids: list[str], allowed_nodes: set[str], executed_ids: set[str]):
        """在子流程范围内并行执行节点（支持循环、条件等控制流）"""
        if not node_ids or self.should_stop:
            return
        
        # 过滤出可以执行的节点
        nodes_to_execute = []
        for node_id in node_ids:
            if node_id not in allowed_nodes:
                continue
            if node_id in executed_ids:
                continue
            
            # 检查前置节点是否都已执行
            prev_nodes = self.graph.get_prev_nodes(node_id)
            prev_in_subflow = [pid for pid in prev_nodes if pid in allowed_nodes]
            
            # 如果没有前置节点，或者所有前置节点都已执行，则可以执行
            if not prev_in_subflow or all(pid in executed_ids for pid in prev_in_subflow):
                nodes_to_execute.append(node_id)
        
        if not nodes_to_execute:
            return
        
        print(f"[DEBUG] _execute_parallel_subflow: 准备执行 {len(nodes_to_execute)} 个节点")
        for nid in nodes_to_execute:
            node = self.graph.get_node(nid)
            if node:
                label = node.data.get('label', node.type)
                print(f"[DEBUG]   - {nid}: {node.type} ({label})")
        
        # 并行执行所有可执行的节点
        tasks = [self._execute_node_in_subflow(node_id, allowed_nodes, executed_ids) for node_id in nodes_to_execute]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_node_in_subflow(self, node_id: str, allowed_nodes: set[str], executed_ids: set[str]):
        """在子流程中执行单个节点（支持循环、条件等控制流）"""
        if node_id in executed_ids or self.should_stop:
            return
        
        node = self.graph.get_node(node_id)
        if not node:
            return
        
        # 标记为已执行
        executed_ids.add(node_id)
        
        # 处理循环节点（特殊处理，不直接执行）
        if node.type in ('loop', 'foreach'):
            body_nodes = self.graph.get_loop_body_nodes(node_id)
            done_nodes = self.graph.get_loop_done_nodes(node_id)
            
            print(f"[DEBUG] 子流程中的循环节点 {node_id} ({node.type})")
            print(f"[DEBUG]   body_nodes: {body_nodes}")
            print(f"[DEBUG]   done_nodes: {done_nodes}")
            
            # 只处理子流程范围内的循环体和完成分支
            body_nodes_in_subflow = [nid for nid in body_nodes if nid in allowed_nodes]
            done_nodes_in_subflow = [nid for nid in done_nodes if nid in allowed_nodes]
            
            print(f"[DEBUG]   body_nodes_in_subflow: {body_nodes_in_subflow}")
            print(f"[DEBUG]   done_nodes_in_subflow: {done_nodes_in_subflow}")
            
            # 调用循环处理逻辑
            await self._handle_loop_in_subflow(node, body_nodes_in_subflow, done_nodes_in_subflow, allowed_nodes, executed_ids)
            return
        
        # 执行普通节点
        result = await self._execute_node(node)
        
        # 处理执行结果
        if result and not result.success:
            # 节点执行失败，检查是否有错误分支
            error_nodes = self.graph.get_error_nodes(node_id)
            error_nodes_in_subflow = [nid for nid in error_nodes if nid in allowed_nodes]
            
            if error_nodes_in_subflow:
                # 有错误分支，继续执行错误分支
                await self._execute_parallel_subflow(error_nodes_in_subflow, allowed_nodes, executed_ids)
                return
            else:
                # 没有错误分支，停止执行
                return
        
        # 获取下一个节点
        if result and result.branch:
            next_nodes = self.graph.get_next_nodes(node_id, result.branch)
        else:
            next_nodes = self.graph.get_next_nodes(node_id)
        
        # 只执行子流程范围内的节点
        next_nodes_in_subflow = [nid for nid in next_nodes if nid in allowed_nodes]
        
        # 继续执行后续节点
        if next_nodes_in_subflow:
            await self._execute_parallel_subflow(next_nodes_in_subflow, allowed_nodes, executed_ids)
    
    async def _handle_loop_in_subflow(self, loop_node: WorkflowNode, body_nodes: list[str], done_nodes: list[str], allowed_nodes: set[str], executed_ids: set[str]):
        """在子流程中处理循环执行"""
        loop_config = loop_node.data
        
        # 先执行循环节点本身，获取循环状态
        result = await self._execute_node(loop_node)
        if not result or not result.success:
            print(f"[DEBUG] 循环节点执行失败")
            return
        
        print(f"[DEBUG] 循环节点执行成功，result.data: {result.data}")
        
        # 从执行结果中获取循环状态
        loop_state = result.data if result.data else {}
        loop_type = loop_state.get('type', loop_config.get('loopType', 'count'))
        
        print(f"[DEBUG] 循环类型: {loop_type}")
        print(f"[DEBUG] 循环体节点: {body_nodes}")
        
        # 收集循环体内的所有节点（包括嵌套的节点）
        all_body_nodes = await self._collect_loop_body_nodes_in_subflow(body_nodes, allowed_nodes)
        print(f"[DEBUG] 循环体内所有节点（包括嵌套）: {all_body_nodes}")
        
        if loop_type == 'count':
            # 计数循环
            count = int(loop_config.get('count', 1))
            index_var = loop_config.get('indexVariable', 'loop_index')
            
            print(f"[DEBUG] 开始计数循环，次数: {count}")
            
            for i in range(count):
                if self.should_stop:
                    break
                
                self.context.variables[index_var] = i
                print(f"[DEBUG] 循环第 {i} 次，执行循环体")
                
                # 执行循环体（仅子流程范围内）
                if body_nodes:
                    # 每次循环重置循环体内所有节点的执行状态
                    # 注意：需要将循环节点本身标记为已执行，这样循环体节点才能执行
                    body_executed = {loop_node.id}
                    await self._execute_parallel_subflow(body_nodes, allowed_nodes, body_executed)
                    print(f"[DEBUG] 循环第 {i} 次完成，执行了 {len(body_executed) - 1} 个节点: {body_executed - {loop_node.id}}")
                    # 将循环体执行的节点添加到总执行列表（不包括循环节点本身，因为它已经在外层执行过了）
                    executed_ids.update(body_executed - {loop_node.id})
        
        elif loop_type == 'while':
            # 条件循环
            condition = loop_config.get('condition', '')
            index_var = loop_config.get('indexVariable', 'loop_index')
            max_iterations = 1000
            iteration = 0
            
            print(f"[DEBUG] 开始条件循环，条件: {condition}")
            
            while iteration < max_iterations:
                if self.should_stop:
                    break
                
                try:
                    should_continue = eval(condition, {"__builtins__": {}}, self.context.variables)
                    if not should_continue:
                        print(f"[DEBUG] 条件不满足，退出循环")
                        break
                except Exception as e:
                    await self._log(LogLevel.ERROR, f"循环条件求值失败: {str(e)}", node_id=loop_node.id)
                    break
                
                self.context.variables[index_var] = iteration
                print(f"[DEBUG] 循环第 {iteration} 次，执行循环体")
                
                # 执行循环体（仅子流程范围内）
                if body_nodes:
                    body_executed = {loop_node.id}
                    await self._execute_parallel_subflow(body_nodes, allowed_nodes, body_executed)
                    print(f"[DEBUG] 循环第 {iteration} 次完成，执行了 {len(body_executed) - 1} 个节点: {body_executed - {loop_node.id}}")
                    executed_ids.update(body_executed - {loop_node.id})
                
                iteration += 1
        
        elif loop_type == 'foreach':
            # 遍历列表
            data = loop_state.get('data', [])
            item_var = loop_state.get('item_variable', 'item')
            index_var = loop_state.get('index_variable', 'index')
            
            print(f"[DEBUG] 开始遍历循环，数据长度: {len(data)}")
            
            for i, item in enumerate(data):
                if self.should_stop:
                    break
                
                # 设置循环变量
                self.context.variables[item_var] = item
                self.context.variables[index_var] = i
                print(f"[DEBUG] 循环第 {i} 次，item={item}")
                
                # 执行循环体（仅子流程范围内）
                if body_nodes:
                    body_executed = {loop_node.id}
                    await self._execute_parallel_subflow(body_nodes, allowed_nodes, body_executed)
                    print(f"[DEBUG] 循环第 {i} 次完成，执行了 {len(body_executed) - 1} 个节点: {body_executed - {loop_node.id}}")
                    executed_ids.update(body_executed - {loop_node.id})
        
        # 清理循环状态
        if self.context.loop_stack and self.context.loop_stack[-1].get('type') == loop_type:
            self.context.loop_stack.pop()
        
        print(f"[DEBUG] 循环结束，执行完成分支: {done_nodes}")
        
        # 循环结束后执行完成分支（仅子流程范围内）
        if done_nodes:
            await self._execute_parallel_subflow(done_nodes, allowed_nodes, executed_ids)
    
    async def _collect_loop_body_nodes_in_subflow(self, start_nodes: list[str], allowed_nodes: set[str]) -> set[str]:
        """收集子流程中循环体内的所有节点（包括嵌套的节点）"""
        collected = set()
        to_visit = list(start_nodes)
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in collected or node_id not in allowed_nodes:
                continue
            collected.add(node_id)
            
            node = self.graph.get_node(node_id)
            if not node:
                continue
            
            # 获取所有后继节点
            next_nodes = []
            
            # 如果是条件节点，获取所有分支
            if node.type == 'condition':
                if node_id in self.graph.condition_branches:
                    for branch_target in self.graph.condition_branches[node_id].values():
                        if branch_target:
                            next_nodes.append(branch_target)
            # 如果是循环节点，获取循环体和完成分支
            elif node.type in ('loop', 'foreach'):
                if node_id in self.graph.loop_branches:
                    for branch_targets in self.graph.loop_branches[node_id].values():
                        next_nodes.extend(branch_targets)
            else:
                # 普通节点，获取默认后继
                next_nodes = self.graph.get_next_nodes(node_id)
            
            for next_id in next_nodes:
                if next_id not in collected and next_id in allowed_nodes:
                    to_visit.append(next_id)
        
        return collected


    async def _handle_loop(self, loop_node: WorkflowNode, body_nodes: list[str], done_nodes: list[str]):
        """处理循环执行"""
        if not self.context.loop_stack:
            await self._notify_successors(done_nodes, loop_node.id)
            return
        
        loop_state = self.context.loop_stack[-1]
        loop_type = loop_state['type']
        
        while not self.should_stop:
            should_continue = False
            
            if loop_type == 'count':
                should_continue = loop_state['current_index'] < loop_state['count']
            elif loop_type == 'range':
                current = loop_state['current_index']
                end_value = loop_state['end_value']
                step_value = loop_state['step_value']
                should_continue = current <= end_value if step_value > 0 else current >= end_value
            elif loop_type == 'while':
                condition_value = self.context.get_variable(loop_state['condition'], False)
                should_continue = bool(condition_value)
            elif loop_type == 'foreach':
                should_continue = loop_state['current_index'] < len(loop_state['data'])
            
            if not should_continue:
                break
            
            self.context.should_continue = False
            
            if body_nodes:
                async with self._node_lock:
                    for nid in body_nodes:
                        self._executed_node_ids.discard(nid)
                        self._executing_node_ids.discard(nid)
                
                # 收集循环体内的所有节点
                all_body_nodes = await self._collect_loop_body_nodes(body_nodes)
                
                # 收集错误处理分支的节点
                error_branch_nodes = self._collect_error_branch_nodes(all_body_nodes)
                
                async with self._node_lock:
                    # 清除循环体节点的执行状态
                    for nid in all_body_nodes:
                        self._executed_node_ids.discard(nid)
                        self._executing_node_ids.discard(nid)
                        # 清除待处理节点的前驱等待状态
                        if nid in self._pending_nodes:
                            del self._pending_nodes[nid]
                    
                    # 清除错误处理分支节点的执行状态（这样下次循环如果再报错，错误处理流程可以再次执行）
                    for nid in error_branch_nodes:
                        self._executed_node_ids.discard(nid)
                        self._executing_node_ids.discard(nid)
                        if nid in self._pending_nodes:
                            del self._pending_nodes[nid]
                
                await self._execute_parallel(body_nodes)
            
            if self.context.should_break:
                self.context.should_break = False
                break
            
            if loop_type == 'count':
                loop_state['current_index'] += 1
                self.context.set_variable(loop_state['index_variable'], loop_state['current_index'])
            elif loop_type == 'range':
                loop_state['current_index'] += loop_state['step_value']
                self.context.set_variable(loop_state['index_variable'], loop_state['current_index'])
            elif loop_type == 'foreach':
                loop_state['current_index'] += 1
                if loop_state['current_index'] < len(loop_state['data']):
                    self.context.set_variable(loop_state['item_variable'], 
                                              loop_state['data'][loop_state['current_index']])
                    self.context.set_variable(loop_state['index_variable'], loop_state['current_index'])
        
        if self.context.loop_stack:
            self.context.loop_stack.pop()
        
        if done_nodes and not self.should_stop:
            await self._execute_parallel(done_nodes)

    async def _collect_loop_body_nodes(self, start_nodes: list[str]) -> set[str]:
        """收集循环体内的所有节点（包括条件分支的所有路径）
        
        注意：不收集错误处理分支的节点，因为错误处理分支只在节点失败时才执行。
        错误处理分支的节点会在 _collect_error_branch_nodes 中单独收集。
        """
        collected = set()
        to_visit = list(start_nodes)
        
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in collected:
                continue
            collected.add(node_id)
            
            node = self.graph.get_node(node_id)
            if not node:
                continue
            
            # 获取所有后继节点
            next_nodes = []
            
            # 如果是条件节点，获取所有分支
            if node.type == 'condition':
                if node_id in self.graph.condition_branches:
                    for branch_target in self.graph.condition_branches[node_id].values():
                        if branch_target:
                            next_nodes.append(branch_target)
            # 如果是循环节点，获取循环体和完成分支
            elif node.type in ('loop', 'foreach'):
                if node_id in self.graph.loop_branches:
                    for branch_targets in self.graph.loop_branches[node_id].values():
                        next_nodes.extend(branch_targets)
            else:
                # 普通节点，获取默认后继
                next_nodes = self.graph.get_next_nodes(node_id)
            
            for next_id in next_nodes:
                if next_id not in collected:
                    to_visit.append(next_id)
        
        return collected

    def _collect_error_branch_nodes(self, body_nodes: set[str]) -> set[str]:
        """收集循环体内所有节点的错误处理分支节点"""
        error_nodes = set()
        to_visit = []
        
        # 首先收集循环体内所有节点的直接错误处理分支
        for node_id in body_nodes:
            error_branch_nodes = self.graph.get_error_nodes(node_id)
            for error_node_id in error_branch_nodes:
                if error_node_id not in body_nodes and error_node_id not in error_nodes:
                    to_visit.append(error_node_id)
        
        # 然后递归收集错误处理分支的后继节点
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in error_nodes or node_id in body_nodes:
                continue
            error_nodes.add(node_id)
            
            node = self.graph.get_node(node_id)
            if not node:
                continue
            
            # 获取后继节点
            next_nodes = self.graph.get_next_nodes(node_id)
            for next_id in next_nodes:
                if next_id not in error_nodes and next_id not in body_nodes:
                    to_visit.append(next_id)
            
            # 错误处理分支的节点也可能有自己的错误处理分支
            error_branch_nodes = self.graph.get_error_nodes(node_id)
            for error_node_id in error_branch_nodes:
                if error_node_id not in error_nodes and error_node_id not in body_nodes:
                    to_visit.append(error_node_id)
        
        return error_nodes
        
        return collected

    async def _cleanup(self):
        """清理资源（内部方法，清理所有资源包括浏览器）"""
        try:
            # 终止所有正在运行的 FFmpeg 进程
            try:
                from app.executors.media import ffmpeg_manager
                await ffmpeg_manager.terminate_all()
            except Exception as e:
                print(f"清理 FFmpeg 进程时出错: {e}")
            
            if self.context.page:
                try:
                    await self.context.page.close()
                except:
                    pass
                self.context.page = None
            
            if self.context.browser_context:
                try:
                    await self.context.browser_context.close()
                except:
                    pass
                self.context.browser_context = None
            
            if self.context.browser:
                try:
                    await self.context.browser.close()
                except:
                    pass
                self.context.browser = None
            
            if self.context._playwright:
                try:
                    await self.context._playwright.stop()
                except:
                    pass
                self.context._playwright = None
            
            # 清理上下文中的数据，防止内存泄漏
            self.context.variables.clear()
            self.context.data_rows.clear()
            self.context.current_row.clear()
            self.context.loop_stack.clear()
            
            # 清理执行器内部状态
            self._executed_node_ids.clear()
            self._executing_node_ids.clear()
            self._pending_nodes.clear()
            self._running_tasks.clear()
            self.graph = None
            
        except Exception as e:
            print(f"清理资源时出错: {e}")
    
    async def cleanup(self):
        """清理浏览器资源（公共方法，仅清理浏览器）"""
        try:
            if self.context.page:
                try:
                    await self.context.page.close()
                except:
                    pass
                self.context.page = None
            
            if self.context.browser_context:
                try:
                    await self.context.browser_context.close()
                except:
                    pass
                self.context.browser_context = None
            
            if self.context.browser:
                try:
                    await self.context.browser.close()
                except:
                    pass
                self.context.browser = None
            
            if self.context._playwright:
                try:
                    await self.context._playwright.stop()
                except:
                    pass
                self.context._playwright = None
        except Exception as e:
            print(f"关闭浏览器时出错: {e}")


    async def execute(self) -> ExecutionResult:
        """执行工作流"""
        from playwright.async_api import async_playwright
        import os
        
        self.is_running = True
        self.should_stop = False
        self.start_time = datetime.now()
        self.executed_nodes = 0
        self.failed_nodes = 0
        self._executed_node_ids.clear()
        self._executing_node_ids.clear()
        self._pending_nodes.clear()
        self._last_data_rows_count = 0
        self._sent_data_rows_count = 0
        self._running_tasks.clear()
        
        self.context.variables.clear()
        self.context.data_rows.clear()
        self.context.current_row.clear()
        self.context.loop_stack.clear()
        self.context.should_break = False
        self.context.should_continue = False
        
        for var in self.workflow.variables:
            self.context.set_variable(var.name, var.value)
        
        await self._log(LogLevel.INFO, "🚀 工作流开始执行", is_system_log=True)
        
        try:
            parser = WorkflowParser(self.workflow)
            self.graph = parser.parse()
            
            playwright = await async_playwright().start()
            self.context._playwright = playwright
            
            # 获取浏览器数据目录：优先使用全局配置，否则使用默认目录
            if self.browser_config and self.browser_config.get('userDataDir'):
                user_data_dir = self.browser_config.get('userDataDir')
            else:
                # 使用默认目录
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                user_data_dir = os.path.join(backend_dir, 'browser_data')
            
            # 确保目录存在
            os.makedirs(user_data_dir, exist_ok=True)
            self.context._user_data_dir = user_data_dir
            print(f"[WorkflowExecutor] 使用浏览器数据目录: {user_data_dir}")
            
            # 收集所有子流程分组内的节点ID（这些节点不应该被主流程直接执行）
            self._subflow_node_ids = self._get_subflow_node_ids()
            
            start_nodes = self.graph.get_start_nodes()
            # 过滤掉子流程内的起始节点
            start_nodes = [nid for nid in start_nodes if nid not in self._subflow_node_ids]
            
            # 调试：打印起始节点信息
            print(f"[DEBUG] 找到 {len(start_nodes)} 个起始节点:")
            for nid in start_nodes:
                node = self.graph.get_node(nid)
                if node:
                    label = node.data.get('label', node.type)
                    print(f"  - {nid}: {node.type} ({label})")
            
            # 调试：打印所有节点和边的信息
            print(f"[DEBUG] 工作流共有 {len(self.graph.nodes)} 个节点:")
            for nid, node in self.graph.nodes.items():
                label = node.data.get('label', node.type)
                prev_nodes = self.graph.get_prev_nodes(nid)
                next_nodes = self.graph.get_next_nodes(nid)
                print(f"  - {nid}: {node.type} ({label})")
                print(f"    前驱: {prev_nodes}")
                print(f"    后继: {next_nodes}")
            
            if not start_nodes:
                await self._log(LogLevel.WARNING, "没有找到起始节点")
            else:
                await self._execute_parallel(start_nodes)
            
            if self.context.current_row:
                self.context.commit_row()
                if len(self.context.data_rows) > self._last_data_rows_count:
                    for i in range(self._last_data_rows_count, len(self.context.data_rows)):
                        await self._send_data_row(self.context.data_rows[i])
            
            if self.should_stop:
                status = ExecutionStatus.STOPPED
                await self._log(LogLevel.WARNING, "⏹️ 工作流已停止", is_system_log=True)
            elif self.failed_nodes > 0:
                status = ExecutionStatus.FAILED
                await self._log(LogLevel.ERROR, f"❌ 工作流执行完成，有 {self.failed_nodes} 个节点失败", is_system_log=True)
            else:
                status = ExecutionStatus.COMPLETED
                duration = (datetime.now() - self.start_time).total_seconds()
                await self._log(LogLevel.SUCCESS, f"✅ 工作流执行完成，共执行 {self.executed_nodes} 个节点，耗时 {duration:.2f}秒", is_system_log=True)
            
            self._result = ExecutionResult(
                workflow_id=self.workflow.id,
                status=status,
                started_at=self.start_time,
                completed_at=datetime.now(),
                total_nodes=len(self.workflow.nodes),
                executed_nodes=self.executed_nodes,
                failed_nodes=self.failed_nodes,
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self._log(LogLevel.ERROR, f"💥 工作流执行异常: {str(e)}", is_system_log=True)
            self._result = ExecutionResult(
                workflow_id=self.workflow.id,
                status=ExecutionStatus.FAILED,
                started_at=self.start_time,
                completed_at=datetime.now(),
                total_nodes=len(self.workflow.nodes),
                executed_nodes=self.executed_nodes,
                failed_nodes=self.failed_nodes,
                error_message=str(e),
            )
        finally:
            # 注意：不在这里自动清理浏览器，由调用方根据 autoCloseBrowser 配置决定是否关闭
            # 但需要清理其他资源
            try:
                # 终止所有正在运行的 FFmpeg 进程
                try:
                    from app.executors.media import ffmpeg_manager
                    await ffmpeg_manager.terminate_all()
                except Exception as e:
                    print(f"清理 FFmpeg 进程时出错: {e}")
                
                # 清理上下文中的数据，防止内存泄漏
                # ⚠️ 注意：不要清空 variables，因为外部需要保存全局变量
                # self.context.variables.clear()  # ❌ 不要清空！
                self.context.data_rows.clear()
                self.context.current_row.clear()
                self.context.loop_stack.clear()
                
                # 清理执行器内部状态
                self._executed_node_ids.clear()
                self._executing_node_ids.clear()
                self._pending_nodes.clear()
                self._running_tasks.clear()
                self.graph = None
            except Exception as e:
                print(f"清理资源时出错: {e}")
            
            self.is_running = False
        
        return self._result

    async def stop(self):
        """停止工作流执行 - 立即强制停止所有操作"""
        self.should_stop = True
        await self._log(LogLevel.WARNING, "正在停止工作流...", is_system_log=True)
        
        # 1. 终止所有正在运行的 FFmpeg 进程
        try:
            from app.executors.media import ffmpeg_manager
            await ffmpeg_manager.terminate_all()
        except Exception as e:
            print(f"终止 FFmpeg 进程时出错: {e}")
        
        # 2. 取消所有正在运行的任务
        for task in list(self._running_tasks):
            if not task.done():
                task.cancel()
        
        # 等待任务取消完成（最多1秒）
        if self._running_tasks:
            try:
                await asyncio.wait(list(self._running_tasks), timeout=1.0)
            except:
                pass
        self._running_tasks.clear()
        
        # 3. 强制关闭浏览器以中断正在进行的操作
        try:
            if self.context.page:
                try:
                    await self.context.page.close()
                except:
                    pass
                self.context.page = None
            
            if self.context.browser_context:
                try:
                    await self.context.browser_context.close()
                except:
                    pass
                self.context.browser_context = None
            
            if self.context.browser:
                try:
                    await self.context.browser.close()
                except:
                    pass
                self.context.browser = None
            
            if self.context._playwright:
                try:
                    await self.context._playwright.stop()
                except:
                    pass
                self.context._playwright = None
        except Exception as e:
            print(f"停止时关闭浏览器出错: {e}")
        
        self.is_running = False

    def get_collected_data(self) -> list[dict]:
        """获取收集的数据"""
        if self.context.current_row:
            self.context.commit_row()
        return self.context.data_rows.copy()
