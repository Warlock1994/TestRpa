"""触发器模块执行器实现"""
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)
from .type_utils import to_int


@register_executor
class WebhookTriggerExecutor(ModuleExecutor):
    """Webhook触发器执行器"""

    @property
    def module_type(self) -> str:
        return "webhook_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        Webhook触发器 - 等待HTTP请求触发
        配置项：
        - webhookId: Webhook唯一标识符（自动生成）
        - method: 允许的HTTP方法（GET/POST/PUT/DELETE/ANY）
        - timeout: 超时时间（秒），0表示无限等待
        - saveToVariable: 保存请求数据的变量名
        - validateHeaders: 验证请求头（JSON格式，可选）
        - validateParams: 验证查询参数（JSON格式，可选）
        - responseBody: 自定义响应内容（JSON格式，可选）
        - responseStatus: 自定义响应状态码（默认200）
        - autoSetParams: 是否自动将请求参数设置为变量（默认True）
        - paramPrefix: 变量名前缀（默认"webhook_"）
        """
        webhook_id = context.resolve_value(config.get('webhookId', ''))
        method = context.resolve_value(config.get('method', 'ANY'))
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'webhook_data')
        validate_headers_str = context.resolve_value(config.get('validateHeaders', ''))
        validate_params_str = context.resolve_value(config.get('validateParams', ''))
        response_body_str = context.resolve_value(config.get('responseBody', ''))
        response_status = to_int(config.get('responseStatus', 200), 200, context)
        auto_set_params = config.get('autoSetParams', True)
        param_prefix = context.resolve_value(config.get('paramPrefix', 'webhook_'))

        if not webhook_id:
            return ModuleResult(success=False, error="Webhook ID不能为空")

        # 解析验证规则
        validate_headers = {}
        validate_params = {}
        response_body = {}
        
        if validate_headers_str:
            try:
                validate_headers = json.loads(validate_headers_str)
            except json.JSONDecodeError:
                return ModuleResult(success=False, error="请求头验证规则格式错误，必须是有效的JSON")
        
        if validate_params_str:
            try:
                validate_params = json.loads(validate_params_str)
            except json.JSONDecodeError:
                return ModuleResult(success=False, error="查询参数验证规则格式错误，必须是有效的JSON")
        
        if response_body_str:
            try:
                response_body = json.loads(response_body_str)
            except json.JSONDecodeError:
                return ModuleResult(success=False, error="响应内容格式错误，必须是有效的JSON")

        # 注册Webhook到全局触发器管理器
        from app.services.trigger_manager import trigger_manager
        
        webhook_url = f"http://localhost:8000/api/triggers/webhook/{webhook_id}"
        
        # 创建等待事件
        event = asyncio.Event()
        webhook_data = {}

        def on_webhook_triggered(data: dict):
            nonlocal webhook_data
            
            # 验证请求头
            if validate_headers:
                request_headers = data.get('headers', {})
                for key, expected_value in validate_headers.items():
                    if request_headers.get(key) != expected_value:
                        context.add_log('warning', f"⚠️ 请求头验证失败: {key}", None)
                        return False
            
            # 验证查询参数
            if validate_params:
                request_params = data.get('query', {})
                for key, expected_value in validate_params.items():
                    if request_params.get(key) != expected_value:
                        context.add_log('warning', f"⚠️ 查询参数验证失败: {key}", None)
                        return False
            
            webhook_data = data
            # 添加自定义响应
            if response_body:
                webhook_data['customResponse'] = {
                    'body': response_body,
                    'status': response_status
                }
            event.set()
            return True

        # 注册Webhook
        trigger_manager.register_webhook(webhook_id, method, on_webhook_triggered)

        try:
            context.add_log('info', f"🌐 Webhook已就绪，等待触发...", None)
            context.add_log('info', f"📍 Webhook URL: {webhook_url}", None)
            context.add_log('info', f"🔧 允许的HTTP方法: {method}", None)
            await context.send_progress(f"🌐 Webhook已就绪，等待触发...")
            await context.send_progress(f"📍 Webhook URL: {webhook_url}")
            await context.send_progress(f"🔧 允许的HTTP方法: {method}")
            
            if validate_headers:
                context.add_log('info', f"🔐 已启用请求头验证", None)
                await context.send_progress(f"🔐 已启用请求头验证")
            if validate_params:
                context.add_log('info', f"🔐 已启用查询参数验证", None)
                await context.send_progress(f"🔐 已启用查询参数验证")

            # 等待触发
            if timeout > 0:
                try:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    return ModuleResult(
                        success=False,
                        error=f"Webhook等待超时（{timeout}秒）"
                    )
            else:
                await event.wait()

            # 保存请求数据到变量
            context.set_variable(save_to_variable, webhook_data)

            # 自动将请求参数设置为变量
            if auto_set_params:
                # 设置查询参数为变量
                query_params = webhook_data.get('query', {})
                for key, value in query_params.items():
                    var_name = f"{param_prefix}{key}"
                    context.set_variable(var_name, value)
                    context.add_log('info', f"📝 已设置变量: {var_name} = {value}", None)
                
                # 设置请求体参数为变量（如果是POST/PUT请求）
                body_data = webhook_data.get('body', {})
                if isinstance(body_data, dict):
                    for key, value in body_data.items():
                        var_name = f"{param_prefix}{key}"
                        context.set_variable(var_name, value)
                        context.add_log('info', f"📝 已设置变量: {var_name} = {value}", None)
                
                # 设置请求头为变量（可选，使用header_前缀）
                headers = webhook_data.get('headers', {})
                for key, value in headers.items():
                    # 只设置自定义请求头，跳过标准HTTP头
                    if key.lower() not in ['host', 'connection', 'user-agent', 'accept', 'accept-encoding', 'accept-language']:
                        var_name = f"{param_prefix}header_{key.lower().replace('-', '_')}"
                        context.set_variable(var_name, value)
                        context.add_log('info', f"📝 已设置变量: {var_name} = {value}", None)

            return ModuleResult(
                success=True,
                message=f"Webhook已触发，数据已保存到变量: {save_to_variable}",
                data=webhook_data
            )

        finally:
            # 清理Webhook注册
            trigger_manager.unregister_webhook(webhook_id)


@register_executor
class HotkeyTriggerExecutor(ModuleExecutor):
    """热键触发器执行器"""

    @property
    def module_type(self) -> str:
        return "hotkey_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        热键触发器 - 等待指定热键按下
        配置项：
        - hotkey: 热键组合（如：ctrl+shift+f1）
        - timeout: 超时时间（秒），0表示无限等待
        """
        hotkey = context.resolve_value(config.get('hotkey', ''))
        timeout = to_int(config.get('timeout', 0), 0, context)

        if not hotkey:
            return ModuleResult(success=False, error="热键不能为空")

        # 注册热键到全局触发器管理器
        from app.services.trigger_manager import trigger_manager

        # 创建等待事件
        event = asyncio.Event()

        def on_hotkey_pressed():
            event.set()

        # 注册热键
        trigger_id = trigger_manager.register_hotkey(hotkey, on_hotkey_pressed)

        try:
            context.add_log('info', f"⌨️ 热键监听已启动: {hotkey}", None)
            context.add_log('info', f"💡 请按下热键以继续执行工作流", None)
            await context.send_progress(f"⌨️ 热键监听已启动: {hotkey}")
            await context.send_progress(f"💡 请按下热键以继续执行工作流")

            # 等待热键按下
            if timeout > 0:
                try:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    return ModuleResult(
                        success=False,
                        error=f"热键等待超时（{timeout}秒）"
                    )
            else:
                await event.wait()

            return ModuleResult(
                success=True,
                message=f"热键已触发: {hotkey}"
            )

        finally:
            # 清理热键注册
            trigger_manager.unregister_hotkey(trigger_id)


@register_executor
class FileWatcherTriggerExecutor(ModuleExecutor):
    """文件监控触发器执行器"""

    @property
    def module_type(self) -> str:
        return "file_watcher_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        文件监控触发器 - 监控文件或文件夹的变化
        配置项：
        - watchPath: 监控路径（文件或文件夹）
        - watchType: 监控类型（created/modified/deleted/any）
        - filePattern: 文件名模式（支持通配符，如：*.txt）
        - timeout: 超时时间（秒），0表示无限等待
        - saveToVariable: 保存事件信息的变量名
        """
        watch_path = context.resolve_value(config.get('watchPath', ''))
        watch_type = context.resolve_value(config.get('watchType', 'any'))
        file_pattern = context.resolve_value(config.get('filePattern', '*'))
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'file_event')

        if not watch_path:
            return ModuleResult(success=False, error="监控路径不能为空")

        watch_path_obj = Path(watch_path)
        if not watch_path_obj.exists():
            return ModuleResult(success=False, error=f"监控路径不存在: {watch_path}")

        # 注册文件监控到全局触发器管理器
        from app.services.trigger_manager import trigger_manager

        # 创建等待事件
        event = asyncio.Event()
        event_data = {}

        def on_file_event(event_type: str, file_path: str):
            nonlocal event_data
            event_data = {
                'eventType': event_type,
                'filePath': file_path,
                'fileName': os.path.basename(file_path),
                'timestamp': datetime.now().isoformat()
            }
            event.set()

        # 注册文件监控
        watcher_id = trigger_manager.register_file_watcher(
            watch_path,
            watch_type,
            file_pattern,
            on_file_event
        )

        try:
            context.add_log('info', f"📁 文件监控已启动", None)
            context.add_log('info', f"📍 监控路径: {watch_path}", None)
            context.add_log('info', f"🔍 监控类型: {watch_type}", None)
            context.add_log('info', f"📄 文件模式: {file_pattern}", None)
            await context.send_progress(f"📁 文件监控已启动")
            await context.send_progress(f"📍 监控路径: {watch_path}")
            await context.send_progress(f"🔍 监控类型: {watch_type}")
            await context.send_progress(f"📄 文件模式: {file_pattern}")

            # 等待文件事件
            if timeout > 0:
                try:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    return ModuleResult(
                        success=False,
                        error=f"文件监控等待超时（{timeout}秒）"
                    )
            else:
                await event.wait()

            # 保存事件数据到变量
            context.set_variable(save_to_variable, event_data)

            return ModuleResult(
                success=True,
                message=f"文件事件已触发: {event_data['eventType']} - {event_data['fileName']}",
                data=event_data
            )

        finally:
            # 清理文件监控
            trigger_manager.unregister_file_watcher(watcher_id)


@register_executor
class EmailTriggerExecutor(ModuleExecutor):
    """邮件触发器执行器"""

    @property
    def module_type(self) -> str:
        return "email_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        邮件触发器 - 监控邮箱收到新邮件
        配置项：
        - emailServer: 邮件服务器（如：imap.qq.com）
        - emailPort: 端口（默认993）
        - emailAccount: 邮箱账号
        - emailPassword: 邮箱密码或授权码
        - fromFilter: 发件人过滤（可选）
        - subjectFilter: 主题关键词过滤（可选）
        - timeout: 超时时间（秒），0表示无限等待
        - checkInterval: 检查间隔（秒，默认30）
        - saveToVariable: 保存邮件信息的变量名
        """
        email_server = context.resolve_value(config.get('emailServer', ''))
        email_port = to_int(config.get('emailPort', 993), 993, context)
        email_account = context.resolve_value(config.get('emailAccount', ''))
        email_password = context.resolve_value(config.get('emailPassword', ''))
        from_filter = context.resolve_value(config.get('fromFilter', ''))
        subject_filter = context.resolve_value(config.get('subjectFilter', ''))
        timeout = to_int(config.get('timeout', 0), 0, context)
        check_interval = to_int(config.get('checkInterval', 30), 30, context)
        save_to_variable = config.get('saveToVariable', 'email_data')

        if not all([email_server, email_account, email_password]):
            return ModuleResult(success=False, error="邮件服务器、账号和密码不能为空")

        # 注册邮件监控到全局触发器管理器
        from app.services.trigger_manager import trigger_manager

        # 创建等待事件
        event = asyncio.Event()
        email_data = {}

        def on_email_received(data: dict):
            nonlocal email_data
            email_data = data
            event.set()

        # 注册邮件监控
        monitor_id = trigger_manager.register_email_monitor(
            email_server,
            email_port,
            email_account,
            email_password,
            from_filter,
            subject_filter,
            check_interval,
            on_email_received
        )

        try:
            context.add_log('info', f"📧 邮件监控已启动", None)
            context.add_log('info', f"📍 邮件服务器: {email_server}:{email_port}", None)
            context.add_log('info', f"👤 监控账号: {email_account}", None)
            await context.send_progress(f"📧 邮件监控已启动")
            await context.send_progress(f"📍 邮件服务器: {email_server}:{email_port}")
            await context.send_progress(f"👤 监控账号: {email_account}")
            if from_filter:
                context.add_log('info', f"🔍 发件人过滤: {from_filter}", None)
                await context.send_progress(f"🔍 发件人过滤: {from_filter}")
            if subject_filter:
                context.add_log('info', f"🔍 主题过滤: {subject_filter}", None)
                await context.send_progress(f"🔍 主题过滤: {subject_filter}")

            # 等待邮件
            if timeout > 0:
                try:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    return ModuleResult(
                        success=False,
                        error=f"邮件监控等待超时（{timeout}秒）"
                    )
            else:
                await event.wait()

            # 保存邮件数据到变量
            context.set_variable(save_to_variable, email_data)

            return ModuleResult(
                success=True,
                message=f"收到新邮件: {email_data.get('subject', '无主题')}",
                data=email_data
            )

        finally:
            # 清理邮件监控
            trigger_manager.unregister_email_monitor(monitor_id)


@register_executor
class ApiTriggerExecutor(ModuleExecutor):
    """API触发器执行器"""

    @property
    def module_type(self) -> str:
        return "api_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        API触发器 - 轮询API接口直到满足条件
        配置项：
        - apiUrl: API接口地址
        - method: HTTP方法（GET/POST）
        - headers: 请求头（JSON格式）
        - body: 请求体（JSON格式，仅POST）
        - conditionPath: 条件判断的JSON路径（如：data.status）
        - conditionValue: 期望的值
        - conditionOperator: 比较运算符（==, !=, >, <, contains）
        - checkInterval: 检查间隔（秒，默认10）
        - timeout: 超时时间（秒），0表示无限等待
        - saveToVariable: 保存响应数据的变量名
        """
        api_url = context.resolve_value(config.get('apiUrl', ''))
        method = context.resolve_value(config.get('method', 'GET'))
        headers_str = context.resolve_value(config.get('headers', '{}'))
        body_str = context.resolve_value(config.get('body', '{}'))
        condition_path = context.resolve_value(config.get('conditionPath', ''))
        condition_value = context.resolve_value(config.get('conditionValue', ''))
        condition_operator = context.resolve_value(config.get('conditionOperator', '=='))
        check_interval = to_int(config.get('checkInterval', 10), 10, context)
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'api_response')

        if not api_url:
            return ModuleResult(success=False, error="API地址不能为空")

        # 解析headers和body
        try:
            headers = json.loads(headers_str) if headers_str else {}
        except json.JSONDecodeError:
            return ModuleResult(success=False, error="请求头格式错误，必须是有效的JSON")

        try:
            body = json.loads(body_str) if body_str and method == 'POST' else None
        except json.JSONDecodeError:
            return ModuleResult(success=False, error="请求体格式错误，必须是有效的JSON")

        import httpx

        context.add_log('info', f"🌐 API轮询已启动", None)
        context.add_log('info', f"📍 API地址: {api_url}", None)
        context.add_log('info', f"🔧 HTTP方法: {method}", None)
        await context.send_progress(f"🌐 API轮询已启动")
        await context.send_progress(f"📍 API地址: {api_url}")
        await context.send_progress(f"🔧 HTTP方法: {method}")
        if condition_path:
            context.add_log('info', f"🔍 条件: {condition_path} {condition_operator} {condition_value}", None)
            await context.send_progress(f"🔍 条件: {condition_path} {condition_operator} {condition_value}")

        start_time = time.time()
        check_count = 0

        while True:
            check_count += 1

            try:
                # 发送API请求
                async with httpx.AsyncClient() as client:
                    if method == 'POST':
                        response = await client.post(api_url, headers=headers, json=body, timeout=30)
                    else:
                        response = await client.get(api_url, headers=headers, timeout=30)

                    response.raise_for_status()
                    response_data = response.json()

                # 如果没有设置条件，直接返回
                if not condition_path:
                    context.set_variable(save_to_variable, response_data)
                    return ModuleResult(
                        success=True,
                        message=f"API请求成功（第{check_count}次检查）",
                        data=response_data
                    )

                # 检查条件
                from jsonpath_ng import parse
                jsonpath_expr = parse(condition_path)
                matches = jsonpath_expr.find(response_data)

                if matches:
                    actual_value = matches[0].value

                    # 比较值
                    condition_met = False
                    if condition_operator == '==':
                        condition_met = str(actual_value) == str(condition_value)
                    elif condition_operator == '!=':
                        condition_met = str(actual_value) != str(condition_value)
                    elif condition_operator == '>':
                        try:
                            condition_met = float(actual_value) > float(condition_value)
                        except (ValueError, TypeError):
                            pass
                    elif condition_operator == '<':
                        try:
                            condition_met = float(actual_value) < float(condition_value)
                        except (ValueError, TypeError):
                            pass
                    elif condition_operator == 'contains':
                        condition_met = str(condition_value) in str(actual_value)

                    if condition_met:
                        context.set_variable(save_to_variable, response_data)
                        return ModuleResult(
                            success=True,
                            message=f"API条件满足（第{check_count}次检查）: {condition_path} = {actual_value}",
                            data=response_data
                        )

                # 条件未满足，继续等待
                context.add_log('info', f"⏳ 第{check_count}次检查，条件未满足，{check_interval}秒后重试...", None)
                await context.send_progress(f"⏳ 第{check_count}次检查，条件未满足，{check_interval}秒后重试...")

            except Exception as e:
                context.add_log('warning', f"⚠️ 第{check_count}次检查失败: {str(e)}", None)
                await context.send_progress(f"⚠️ 第{check_count}次检查失败: {str(e)}", "warning")

            # 检查超时
            if timeout > 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return ModuleResult(
                        success=False,
                        error=f"API轮询超时（{timeout}秒，共检查{check_count}次）"
                    )

            # 等待下次检查
            await asyncio.sleep(check_interval)




@register_executor
class MouseTriggerExecutor(ModuleExecutor):
    """鼠标触发器执行器"""

    @property
    def module_type(self) -> str:
        return "mouse_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        鼠标触发器 - 监听鼠标事件
        配置项：
        - triggerType: 触发类型（left_click/right_click/middle_click/scroll_up/scroll_down/move）
        - moveDistance: 移动距离阈值（像素，仅移动类型有效）
        - timeout: 超时时间（秒），0表示无限等待
        - saveToVariable: 保存鼠标位置的变量名
        """
        trigger_type = context.resolve_value(config.get('triggerType', 'left_click'))
        move_distance = to_int(config.get('moveDistance', 100), 100, context)
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'mouse_position')

        try:
            import ctypes
            from pynput import mouse
            
            context.add_log('info', f"🖱️ 鼠标触发器已启动", None)
            
            trigger_type_labels = {
                'left_click': '左键点击',
                'right_click': '右键点击',
                'middle_click': '中键点击',
                'scroll_up': '向上滚动',
                'scroll_down': '向下滚动',
                'move': f'移动超过{move_distance}像素'
            }
            context.add_log('info', f"📌 触发条件: {trigger_type_labels.get(trigger_type, trigger_type)}", None)
            
            # 创建等待事件
            event = asyncio.Event()
            mouse_data = {}
            start_pos = None
            
            def on_click(x, y, button, pressed):
                nonlocal mouse_data
                if not pressed:  # 只在释放时触发
                    if trigger_type == 'left_click' and button == mouse.Button.left:
                        mouse_data = {'x': x, 'y': y, 'button': 'left'}
                        event.set()
                    elif trigger_type == 'right_click' and button == mouse.Button.right:
                        mouse_data = {'x': x, 'y': y, 'button': 'right'}
                        event.set()
                    elif trigger_type == 'middle_click' and button == mouse.Button.middle:
                        mouse_data = {'x': x, 'y': y, 'button': 'middle'}
                        event.set()
            
            def on_scroll(x, y, dx, dy):
                nonlocal mouse_data
                if trigger_type == 'scroll_up' and dy > 0:
                    mouse_data = {'x': x, 'y': y, 'direction': 'up', 'delta': dy}
                    event.set()
                elif trigger_type == 'scroll_down' and dy < 0:
                    mouse_data = {'x': x, 'y': y, 'direction': 'down', 'delta': abs(dy)}
                    event.set()
            
            def on_move(x, y):
                nonlocal mouse_data, start_pos
                if trigger_type == 'move':
                    if start_pos is None:
                        start_pos = (x, y)
                    else:
                        distance = ((x - start_pos[0]) ** 2 + (y - start_pos[1]) ** 2) ** 0.5
                        if distance >= move_distance:
                            mouse_data = {'x': x, 'y': y, 'start_x': start_pos[0], 'start_y': start_pos[1], 'distance': int(distance)}
                            event.set()
            
            # 启动监听器
            listener = mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll,
                on_move=on_move
            )
            listener.start()
            
            try:
                # 等待触发或超时
                if timeout > 0:
                    await asyncio.wait_for(event.wait(), timeout=timeout)
                else:
                    await event.wait()
                
                # 保存数据到变量
                if save_to_variable and mouse_data:
                    context.set_variable(save_to_variable, mouse_data)
                
                listener.stop()
                
                return ModuleResult(
                    success=True,
                    message=f"鼠标触发器已触发: {trigger_type_labels.get(trigger_type, trigger_type)}",
                    data=mouse_data
                )
            
            except asyncio.TimeoutError:
                listener.stop()
                return ModuleResult(
                    success=False,
                    error=f"鼠标触发器超时（{timeout}秒）"
                )
        
        except ImportError:
            return ModuleResult(
                success=False,
                error="鼠标触发器初始化失败，请检查系统配置"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"鼠标触发器失败: {str(e)}")


@register_executor
class ImageTriggerExecutor(ModuleExecutor):
    """图像触发器执行器"""

    @property
    def module_type(self) -> str:
        return "image_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        图像触发器 - 检测屏幕上出现指定图像时触发
        配置项：
        - imagePath: 图像文件路径
        - confidence: 匹配置信度（0-1）
        - checkInterval: 检查间隔（秒）
        - timeout: 超时时间（秒），0表示无限等待
        - searchRegion: 搜索区域（可选）
        - saveToVariable: 保存图像位置的变量名
        """
        import ctypes
        
        image_path = context.resolve_value(config.get('imagePath', ''))
        confidence = float(config.get('confidence', 0.8))
        check_interval = float(config.get('checkInterval', 0.5))
        timeout = to_int(config.get('timeout', 0), 0, context)
        search_region = config.get('searchRegion', None)
        save_to_variable = config.get('saveToVariable', 'image_position')
        
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
                return ModuleResult(success=False, error="无法读取图像文件")
            
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
            
            context.add_log('info', f"🖼️ 图像触发器已启动", None)
            if use_region:
                context.add_log('info', f"📍 搜索区域: ({region_x}, {region_y}) - ({region_x + region_w}, {region_y + region_h})", None)
            else:
                context.add_log('info', f"📍 搜索区域: 整个屏幕", None)
            context.add_log('info', f"🎯 匹配置信度: {confidence:.0%}", None)
            
            start_time = time.time()
            found = False
            center_x, center_y = 0, 0
            best_confidence = 0
            
            while True:
                # 检查超时
                if timeout > 0 and time.time() - start_time >= timeout:
                    return ModuleResult(
                        success=False,
                        error=f"图像触发器超时（{timeout}秒），最高匹配度: {best_confidence:.2%}"
                    )
                
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
            
            # 保存位置到变量
            if save_to_variable:
                image_data = {'x': center_x, 'y': center_y, 'confidence': best_confidence}
                context.set_variable(save_to_variable, image_data)
            
            return ModuleResult(
                success=True,
                message=f"图像触发器已触发，位置: ({center_x}, {center_y})，匹配度: {best_confidence:.2%}",
                data={'x': center_x, 'y': center_y, 'confidence': best_confidence}
            )
        
        except ImportError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else "opencv-python/Pillow"
            return ModuleResult(
                success=False,
                error=f"图像触发器初始化失败: {missing}"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"图像触发器失败: {str(e)}")


@register_executor
class SoundTriggerExecutor(ModuleExecutor):
    """声音触发器执行器"""

    @property
    def module_type(self) -> str:
        return "sound_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        声音触发器 - 检测系统音频输出音量
        配置项：
        - volumeThreshold: 音量阈值（0-100）
        - checkInterval: 检查间隔（秒）
        - timeout: 超时时间（秒），0表示无限等待
        - saveToVariable: 保存音量值的变量名
        """
        volume_threshold = to_int(config.get('volumeThreshold', 50), 50, context)
        check_interval = float(config.get('checkInterval', 0.1))
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'sound_volume')
        
        try:
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
            
            context.add_log('info', f"🔊 声音触发器已启动", None)
            context.add_log('info', f"📊 音量阈值: {volume_threshold}%", None)
            
            # 获取默认音频设备
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
            meter = interface.QueryInterface(IAudioMeterInformation)
            
            start_time = time.time()
            
            while True:
                # 检查超时
                if timeout > 0 and time.time() - start_time >= timeout:
                    return ModuleResult(
                        success=False,
                        error=f"声音触发器超时（{timeout}秒）"
                    )
                
                # 获取当前音量（0.0-1.0）
                current_volume = meter.GetPeakValue()
                current_volume_percent = int(current_volume * 100)
                
                # 检查是否达到阈值
                if current_volume_percent >= volume_threshold:
                    # 保存音量到变量
                    if save_to_variable:
                        context.set_variable(save_to_variable, current_volume_percent)
                    
                    return ModuleResult(
                        success=True,
                        message=f"声音触发器已触发，当前音量: {current_volume_percent}%",
                        data={'volume': current_volume_percent}
                    )
                
                await asyncio.sleep(check_interval)
        
        except ImportError:
            return ModuleResult(
                success=False,
                error="声音触发器初始化失败，请检查系统配置"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"声音触发器失败: {str(e)}")


@register_executor
class FaceTriggerExecutor(ModuleExecutor):
    """人脸触发器执行器"""

    @property
    def module_type(self) -> str:
        return "face_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        人脸触发器 - 实时识别摄像头中的人脸
        配置项：
        - targetFaceImage: 目标人脸图片路径
        - tolerance: 匹配容差（0-1，越小越严格）
        - checkInterval: 检查间隔（秒）
        - timeout: 超时时间（秒），0表示无限等待
        - cameraIndex: 摄像头索引（默认0）
        - saveToVariable: 保存识别结果的变量名
        """
        target_face_image = context.resolve_value(config.get('targetFaceImage', ''))
        tolerance = float(config.get('tolerance', 0.6))
        check_interval = float(config.get('checkInterval', 0.5))
        timeout = to_int(config.get('timeout', 0), 0, context)
        camera_index = to_int(config.get('cameraIndex', 0), 0, context)
        save_to_variable = config.get('saveToVariable', 'face_detected')
        
        if not target_face_image:
            return ModuleResult(success=False, error="目标人脸图片路径不能为空")
        
        if not Path(target_face_image).exists():
            return ModuleResult(success=False, error=f"目标人脸图片不存在: {target_face_image}")
        
        try:
            import face_recognition
            import cv2
            import numpy as np
            
            context.add_log('info', f"👤 人脸触发器已启动", None)
            context.add_log('info', f"📷 使用摄像头: {camera_index}", None)
            context.add_log('info', f"🎯 匹配容差: {tolerance}", None)
            
            # 加载目标人脸
            target_image = face_recognition.load_image_file(target_face_image)
            target_encodings = face_recognition.face_encodings(target_image)
            
            if len(target_encodings) == 0:
                return ModuleResult(success=False, error="目标图片中未检测到人脸")
            
            target_encoding = target_encodings[0]
            context.add_log('info', f"✅ 目标人脸已加载", None)
            
            # 打开摄像头
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return ModuleResult(success=False, error=f"无法打开摄像头 {camera_index}")
            
            context.add_log('info', f"📹 摄像头已打开，开始监控...", None)
            await context.send_progress(f"📹 摄像头已打开，开始监控...")
            
            start_time = time.time()
            frame_count = 0
            
            try:
                while True:
                    # 检查超时
                    if timeout > 0 and time.time() - start_time >= timeout:
                        cap.release()
                        return ModuleResult(
                            success=False,
                            error=f"人脸触发器超时（{timeout}秒）"
                        )
                    
                    # 读取摄像头帧
                    ret, frame = cap.read()
                    if not ret:
                        await asyncio.sleep(check_interval)
                        continue
                    
                    frame_count += 1
                    
                    # 每隔一定帧数进行人脸识别（提高性能）
                    if frame_count % max(1, int(check_interval * 30)) != 0:
                        await asyncio.sleep(0.01)
                        continue
                    
                    # 转换颜色空间（OpenCV使用BGR，face_recognition使用RGB）
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # 检测人脸位置和编码
                    face_locations = face_recognition.face_locations(rgb_frame)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    # 比对每个检测到的人脸
                    for face_encoding, face_location in zip(face_encodings, face_locations):
                        # 计算人脸距离
                        face_distance = face_recognition.face_distance([target_encoding], face_encoding)[0]
                        is_match = face_distance <= tolerance
                        
                        if is_match:
                            # 找到匹配的人脸
                            top, right, bottom, left = face_location
                            confidence = 1 - face_distance
                            
                            # 保存结果到变量
                            if save_to_variable:
                                result_data = {
                                    'matched': True,
                                    'confidence': float(confidence),
                                    'face_location': {
                                        'top': int(top),
                                        'right': int(right),
                                        'bottom': int(bottom),
                                        'left': int(left)
                                    },
                                    'timestamp': datetime.now().isoformat()
                                }
                                context.set_variable(save_to_variable, result_data)
                            
                            cap.release()
                            
                            return ModuleResult(
                                success=True,
                                message=f"人脸触发器已触发，匹配度: {confidence:.2%}",
                                data={
                                    'matched': True,
                                    'confidence': float(confidence),
                                    'face_location': {'top': int(top), 'right': int(right), 'bottom': int(bottom), 'left': int(left)}
                                }
                            )
                    
                    # 等待下次检查
                    await asyncio.sleep(check_interval)
            
            finally:
                cap.release()
        
        except ImportError:
            return ModuleResult(
                success=False,
                error="人脸触发器初始化失败，请检查系统配置"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"人脸触发器失败: {str(e)}")


@register_executor
class ElementChangeTriggerExecutor(ModuleExecutor):
    """子元素变化触发器执行器"""

    @property
    def module_type(self) -> str:
        return "element_change_trigger"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        子元素变化触发器 - 使用MutationObserver监控元素子元素变化
        配置项：
        - selector: 要监控的元素选择器
        - observeType: 监控类型 (childList=子元素, attributes=属性, characterData=文本内容)
        - timeout: 超时时间（秒），0表示无限等待
        - saveNewElementSelector: 保存新增元素选择器的变量名
        - saveChangeInfo: 保存变化信息的变量名
        """
        selector = context.resolve_value(config.get('selector', ''))
        observe_type = config.get('observeType', 'childList')  # childList, attributes, characterData
        timeout = to_int(config.get('timeout', 0), 0, context)
        save_new_element_selector = config.get('saveNewElementSelector', 'new_element_selector')
        save_change_info = config.get('saveChangeInfo', 'element_change_info')
        
        if not selector:
            return ModuleResult(success=False, error="元素选择器不能为空")
        
        if context.browser_context is None:
            return ModuleResult(success=False, error="浏览器未初始化，请先打开网页")
        
        page = context.page
        if not page:
            return ModuleResult(success=False, error="页面未初始化，请先打开网页")
        
        try:
            context.add_log('info', f"👁️ 子元素变化触发器已启动", None)
            context.add_log('info', f"🎯 监控元素: {selector}", None)
            context.add_log('info', f"📋 监控类型: {observe_type}", None)
            await context.send_progress(f"👁️ 开始监控元素变化...")
            
            # 等待元素出现
            try:
                await page.wait_for_selector(selector, timeout=10000)
            except Exception:
                return ModuleResult(success=False, error=f"未找到元素: {selector}")
            
            # 注入MutationObserver监控脚本
            observer_result = await page.evaluate('''
                (params) => {
                    return new Promise((resolve, reject) => {
                        const { selector, observeType, timeout } = params;
                        const target = document.querySelector(selector);
                        if (!target) {
                            reject(new Error('未找到目标元素'));
                            return;
                        }
                        
                        // 配置观察选项
                        const config = {
                            childList: observeType === 'childList',
                            attributes: observeType === 'attributes',
                            characterData: observeType === 'characterData',
                            subtree: true,  // 监控所有后代节点
                            attributeOldValue: observeType === 'attributes',
                            characterDataOldValue: observeType === 'characterData'
                        };
                        
                        // 记录初始状态
                        const initialState = {
                            childCount: target.children.length,
                            innerHTML: target.innerHTML.substring(0, 1000)
                        };
                        
                        let timeoutId = null;
                        
                        // 创建观察者
                        const observer = new MutationObserver((mutations) => {
                            // 清除超时定时器
                            if (timeoutId) {
                                clearTimeout(timeoutId);
                            }
                            
                            // 停止观察
                            observer.disconnect();
                            
                            // 分析变化
                            const changes = [];
                            const addedNodes = [];
                            const removedNodes = [];
                            
                            mutations.forEach(mutation => {
                                if (mutation.type === 'childList') {
                                    // 子元素变化
                                    mutation.addedNodes.forEach(node => {
                                        if (node.nodeType === 1) { // 元素节点
                                            addedNodes.push({
                                                tagName: node.tagName?.toLowerCase(),
                                                className: node.className,
                                                id: node.id,
                                                textContent: node.textContent?.substring(0, 100) || ''
                                            });
                                        }
                                    });
                                    
                                    mutation.removedNodes.forEach(node => {
                                        if (node.nodeType === 1) {
                                            removedNodes.push({
                                                tagName: node.tagName?.toLowerCase(),
                                                className: node.className,
                                                id: node.id
                                            });
                                        }
                                    });
                                    
                                    changes.push({
                                        type: 'childList',
                                        addedCount: mutation.addedNodes.length,
                                        removedCount: mutation.removedNodes.length
                                    });
                                } else if (mutation.type === 'attributes') {
                                    // 属性变化
                                    changes.push({
                                        type: 'attributes',
                                        attributeName: mutation.attributeName,
                                        oldValue: mutation.oldValue,
                                        newValue: mutation.target.getAttribute(mutation.attributeName)
                                    });
                                } else if (mutation.type === 'characterData') {
                                    // 文本内容变化
                                    changes.push({
                                        type: 'characterData',
                                        oldValue: mutation.oldValue,
                                        newValue: mutation.target.textContent
                                    });
                                }
                            });
                            
                            // 获取新增元素的信息
                            let newElementSelector = null;
                            let newElementText = null;
                            let lastAddedElement = null;
                            
                            // 从mutations中找到最后一个新增的元素节点
                            for (let i = mutations.length - 1; i >= 0; i--) {
                                const mutation = mutations[i];
                                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                                    // 从后往前找第一个元素节点
                                    for (let j = mutation.addedNodes.length - 1; j >= 0; j--) {
                                        const node = mutation.addedNodes[j];
                                        if (node.nodeType === 1) { // 元素节点
                                            lastAddedElement = node;
                                            break;
                                        }
                                    }
                                    if (lastAddedElement) break;
                                }
                            }
                            
                            if (lastAddedElement) {
                                // 获取元素的文本内容
                                newElementText = lastAddedElement.textContent?.trim() || '';
                                
                                // 生成唯一选择器（尝试多种方式）
                                if (lastAddedElement.id) {
                                    newElementSelector = '#' + lastAddedElement.id;
                                } else {
                                    // 使用元素在父元素中的精确位置
                                    const parent = lastAddedElement.parentElement;
                                    if (parent) {
                                        const siblings = Array.from(parent.children);
                                        const index = siblings.indexOf(lastAddedElement);
                                        const tagName = lastAddedElement.tagName.toLowerCase();
                                        
                                        // 生成更精确的选择器：父选择器 > 标签:nth-child(精确位置)
                                        newElementSelector = selector + ' > ' + tagName + ':nth-child(' + (index + 1) + ')';
                                    }
                                }
                            }
                            
                            // 返回结果
                            resolve({
                                success: true,
                                changes: changes,
                                addedNodes: addedNodes,
                                removedNodes: removedNodes,
                                newElementSelector: newElementSelector,
                                newElementText: newElementText,
                                currentChildCount: target.children.length,
                                initialChildCount: initialState.childCount,
                                mutationCount: mutations.length
                            });
                        });
                        
                        // 开始观察
                        observer.observe(target, config);
                        
                        // 设置超时
                        if (timeout > 0) {
                            timeoutId = setTimeout(() => {
                                observer.disconnect();
                                reject(new Error(`监控超时（${timeout}秒）`));
                            }, timeout * 1000);
                        }
                    });
                }
            ''', {
                'selector': selector,
                'observeType': observe_type,
                'timeout': timeout
            })
            
            # 处理结果
            if observer_result.get('success'):
                changes = observer_result.get('changes', [])
                added_nodes = observer_result.get('addedNodes', [])
                removed_nodes = observer_result.get('removedNodes', [])
                new_element_selector = observer_result.get('newElementSelector')
                new_element_text = observer_result.get('newElementText', '')
                current_count = observer_result.get('currentChildCount', 0)
                initial_count = observer_result.get('initialChildCount', 0)
                mutation_count = observer_result.get('mutationCount', 0)
                
                # 生成变化描述
                change_desc = []
                if added_nodes:
                    change_desc.append(f"新增{len(added_nodes)}个元素")
                if removed_nodes:
                    change_desc.append(f"删除{len(removed_nodes)}个元素")
                if not change_desc:
                    change_desc.append("元素发生变化")
                
                context.add_log('info', f"✅ 检测到变化: {', '.join(change_desc)}", None)
                context.add_log('info', f"📊 子元素数量: {initial_count} → {current_count}", None)
                context.add_log('info', f"🔄 变化次数: {mutation_count}", None)
                
                if new_element_selector:
                    context.add_log('info', f"🎯 新增元素选择器: {new_element_selector}", None)
                
                if new_element_text:
                    context.add_log('info', f"📝 新增元素内容: {new_element_text[:100]}", None)
                
                # 保存变化信息
                change_info = {
                    'changeType': 'childList' if added_nodes or removed_nodes else observe_type,
                    'previousCount': initial_count,
                    'currentCount': current_count,
                    'addedCount': len(added_nodes),
                    'removedCount': len(removed_nodes),
                    'mutationCount': mutation_count,
                    'changes': changes,
                    'addedNodes': added_nodes,
                    'removedNodes': removed_nodes,
                    'newElementText': new_element_text,
                    'timestamp': datetime.now().isoformat()
                }
                
                if save_change_info:
                    context.set_variable(save_change_info, change_info)
                
                # 保存新增元素选择器
                if new_element_selector and save_new_element_selector:
                    context.set_variable(save_new_element_selector, new_element_selector)
                    context.add_log('debug', f"🔍 生成的选择器: {new_element_selector}", None)
                    if new_element_text:
                        context.add_log('debug', f"📄 元素文本内容: {new_element_text[:100]}", None)
                
                return ModuleResult(
                    success=True,
                    message=f"子元素变化触发器已触发: {', '.join(change_desc)}",
                    data={
                        **change_info,
                        'newElementSelector': new_element_selector,
                        'newElementText': new_element_text
                    }
                )
            else:
                return ModuleResult(success=False, error="MutationObserver监控失败")
        
        except Exception as e:
            error_msg = str(e)
            if '监控超时' in error_msg:
                return ModuleResult(success=False, error=f"子元素变化触发器超时（{timeout}秒）")
            return ModuleResult(success=False, error=f"子元素变化触发器失败: {error_msg}")

