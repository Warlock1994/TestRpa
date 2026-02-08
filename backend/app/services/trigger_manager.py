"""触发器管理服务 - 统一管理所有触发器"""
import asyncio
import imaplib
import email
import os
import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional, Set
from threading import Thread
import time

from pynput import keyboard


class TriggerManager:
    """全局触发器管理器"""

    def __init__(self):
        # Webhook触发器
        self.webhooks: Dict[str, dict] = {}  # webhook_id -> {method, callback}

        # 热键触发器
        self.hotkeys: Dict[str, dict] = {}  # trigger_id -> {hotkey, callback}
        self.hotkey_listener: Optional[keyboard.GlobalHotKeys] = None
        self.hotkey_thread: Optional[Thread] = None

        # 文件监控触发器
        self.file_watchers: Dict[str, dict] = {}  # watcher_id -> {path, type, pattern, callback}
        self.file_watcher_tasks: Dict[str, asyncio.Task] = {}

        # 邮件监控触发器
        self.email_monitors: Dict[str, dict] = {}  # monitor_id -> {config, callback}
        self.email_monitor_tasks: Dict[str, asyncio.Task] = {}

    # ==================== Webhook触发器 ====================

    def register_webhook(self, webhook_id: str, method: str, callback: Callable):
        """注册Webhook触发器"""
        self.webhooks[webhook_id] = {
            'method': method,
            'callback': callback
        }
        print(f"[TriggerManager] Webhook已注册: {webhook_id} ({method})")

    def unregister_webhook(self, webhook_id: str):
        """注销Webhook触发器"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            print(f"[TriggerManager] Webhook已注销: {webhook_id}")

    def trigger_webhook(self, webhook_id: str, method: str, data: dict) -> bool:
        """触发Webhook"""
        if webhook_id not in self.webhooks:
            return False

        webhook = self.webhooks[webhook_id]
        allowed_method = webhook['method']

        # 检查HTTP方法是否匹配
        if allowed_method != 'ANY' and allowed_method != method:
            return False

        # 调用回调函数
        callback = webhook['callback']
        callback(data)
        return True

    # ==================== 热键触发器 ====================

    def register_hotkey(self, hotkey: str, callback: Callable) -> str:
        """注册热键触发器"""
        import uuid
        trigger_id = str(uuid.uuid4())

        # 标准化热键格式（转换为pynput格式）
        normalized_hotkey = self._normalize_hotkey(hotkey)

        self.hotkeys[trigger_id] = {
            'hotkey': normalized_hotkey,
            'original': hotkey,
            'callback': callback
        }

        # 重新启动热键监听器
        self._restart_hotkey_listener()

        print(f"[TriggerManager] 热键已注册: {hotkey} -> {normalized_hotkey}")
        return trigger_id

    def unregister_hotkey(self, trigger_id: str):
        """注销热键触发器"""
        if trigger_id in self.hotkeys:
            hotkey = self.hotkeys[trigger_id]['original']
            del self.hotkeys[trigger_id]
            print(f"[TriggerManager] 热键已注销: {hotkey}")

            # 重新启动热键监听器
            self._restart_hotkey_listener()

    def _normalize_hotkey(self, hotkey: str) -> str:
        """标准化热键格式"""
        # 将用户输入的热键转换为pynput格式
        # 例如: ctrl+shift+f1 -> <ctrl>+<shift>+<f1>
        parts = hotkey.lower().split('+')
        normalized_parts = []

        # 特殊键映射表
        special_keys = {
            'ctrl', 'alt', 'shift', 'cmd', 'win',
            'esc', 'escape', 'tab', 'capslock', 'caps_lock',
            'enter', 'return', 'backspace', 'delete', 'del',
            'insert', 'home', 'end', 'pageup', 'page_up',
            'pagedown', 'page_down', 'up', 'down', 'left', 'right',
            'space', 'numlock', 'num_lock', 'scroll_lock',
            'print_screen', 'pause'
        }

        for part in parts:
            part = part.strip()
            
            # 功能键 F1-F12
            if part.startswith('f') and len(part) <= 3 and part[1:].isdigit():
                normalized_parts.append(f'<{part}>')
            # 特殊键需要用尖括号包裹
            elif part in special_keys:
                # 标准化某些键名
                if part == 'escape':
                    part = 'esc'
                elif part == 'return':
                    part = 'enter'
                elif part == 'del':
                    part = 'delete'
                elif part == 'caps_lock':
                    part = 'capslock'
                elif part == 'page_up':
                    part = 'pageup'
                elif part == 'page_down':
                    part = 'pagedown'
                elif part == 'num_lock':
                    part = 'numlock'
                
                normalized_parts.append(f'<{part}>')
            # 单个字母或数字不需要尖括号
            elif len(part) == 1:
                normalized_parts.append(part)
            # 其他情况也加尖括号
            else:
                normalized_parts.append(f'<{part}>')

        return '+'.join(normalized_parts)

    def _restart_hotkey_listener(self):
        """重新启动热键监听器"""
        # 停止旧的监听器
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except:
                pass

        # 如果没有热键，不启动监听器
        if not self.hotkeys:
            return

        # 构建热键映射
        hotkey_map = {}
        for trigger_id, data in self.hotkeys.items():
            hotkey = data['hotkey']
            callback = data['callback']
            hotkey_map[hotkey] = callback

        # 启动新的监听器
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()
            print(f"[TriggerManager] 热键监听器已启动，监听 {len(hotkey_map)} 个热键")
        except Exception as e:
            print(f"[TriggerManager] 热键监听器启动失败: {e}")

    # ==================== 文件监控触发器 ====================

    def register_file_watcher(
        self,
        watch_path: str,
        watch_type: str,
        file_pattern: str,
        callback: Callable
    ) -> str:
        """注册文件监控触发器"""
        import uuid
        watcher_id = str(uuid.uuid4())

        self.file_watchers[watcher_id] = {
            'path': watch_path,
            'type': watch_type,
            'pattern': file_pattern,
            'callback': callback,
            'last_snapshot': self._get_directory_snapshot(watch_path)
        }

        # 启动监控任务
        task = asyncio.create_task(self._file_watcher_loop(watcher_id))
        self.file_watcher_tasks[watcher_id] = task

        print(f"[TriggerManager] 文件监控已注册: {watch_path} ({watch_type})")
        return watcher_id

    def unregister_file_watcher(self, watcher_id: str):
        """注销文件监控触发器"""
        if watcher_id in self.file_watchers:
            del self.file_watchers[watcher_id]

        if watcher_id in self.file_watcher_tasks:
            task = self.file_watcher_tasks[watcher_id]
            task.cancel()
            del self.file_watcher_tasks[watcher_id]

        print(f"[TriggerManager] 文件监控已注销: {watcher_id}")

    def _get_directory_snapshot(self, path: str) -> dict:
        """获取目录快照"""
        snapshot = {}
        path_obj = Path(path)

        if path_obj.is_file():
            # 监控单个文件
            if path_obj.exists():
                stat = path_obj.stat()
                snapshot[str(path_obj)] = {
                    'mtime': stat.st_mtime,
                    'size': stat.st_size
                }
        else:
            # 监控目录
            for file_path in path_obj.rglob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    snapshot[str(file_path)] = {
                        'mtime': stat.st_mtime,
                        'size': stat.st_size
                    }

        return snapshot

    async def _file_watcher_loop(self, watcher_id: str):
        """文件监控循环"""
        try:
            while watcher_id in self.file_watchers:
                watcher = self.file_watchers[watcher_id]
                watch_path = watcher['path']
                watch_type = watcher['type']
                file_pattern = watcher['pattern']
                callback = watcher['callback']
                last_snapshot = watcher['last_snapshot']

                # 获取当前快照
                current_snapshot = self._get_directory_snapshot(watch_path)

                # 检测新增文件
                if watch_type in ['created', 'any']:
                    for file_path in current_snapshot:
                        if file_path not in last_snapshot:
                            if fnmatch.fnmatch(os.path.basename(file_path), file_pattern):
                                callback('created', file_path)
                                watcher['last_snapshot'] = current_snapshot
                                return  # 触发后退出

                # 检测修改文件
                if watch_type in ['modified', 'any']:
                    for file_path in current_snapshot:
                        if file_path in last_snapshot:
                            if current_snapshot[file_path]['mtime'] != last_snapshot[file_path]['mtime']:
                                if fnmatch.fnmatch(os.path.basename(file_path), file_pattern):
                                    callback('modified', file_path)
                                    watcher['last_snapshot'] = current_snapshot
                                    return  # 触发后退出

                # 检测删除文件
                if watch_type in ['deleted', 'any']:
                    for file_path in last_snapshot:
                        if file_path not in current_snapshot:
                            if fnmatch.fnmatch(os.path.basename(file_path), file_pattern):
                                callback('deleted', file_path)
                                watcher['last_snapshot'] = current_snapshot
                                return  # 触发后退出

                # 更新快照
                watcher['last_snapshot'] = current_snapshot

                # 等待1秒后再次检查
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[TriggerManager] 文件监控异常: {e}")

    # ==================== 邮件监控触发器 ====================

    def register_email_monitor(
        self,
        server: str,
        port: int,
        account: str,
        password: str,
        from_filter: str,
        subject_filter: str,
        check_interval: int,
        callback: Callable
    ) -> str:
        """注册邮件监控触发器"""
        import uuid
        monitor_id = str(uuid.uuid4())

        self.email_monitors[monitor_id] = {
            'server': server,
            'port': port,
            'account': account,
            'password': password,
            'from_filter': from_filter,
            'subject_filter': subject_filter,
            'check_interval': check_interval,
            'callback': callback,
            'last_check_time': time.time()
        }

        # 启动监控任务
        task = asyncio.create_task(self._email_monitor_loop(monitor_id))
        self.email_monitor_tasks[monitor_id] = task

        print(f"[TriggerManager] 邮件监控已注册: {account}@{server}")
        return monitor_id

    def unregister_email_monitor(self, monitor_id: str):
        """注销邮件监控触发器"""
        if monitor_id in self.email_monitors:
            del self.email_monitors[monitor_id]

        if monitor_id in self.email_monitor_tasks:
            task = self.email_monitor_tasks[monitor_id]
            task.cancel()
            del self.email_monitor_tasks[monitor_id]

        print(f"[TriggerManager] 邮件监控已注销: {monitor_id}")

    async def _email_monitor_loop(self, monitor_id: str):
        """邮件监控循环"""
        try:
            while monitor_id in self.email_monitors:
                monitor = self.email_monitors[monitor_id]
                server = monitor['server']
                port = monitor['port']
                account = monitor['account']
                password = monitor['password']
                from_filter = monitor['from_filter']
                subject_filter = monitor['subject_filter']
                check_interval = monitor['check_interval']
                callback = monitor['callback']
                last_check_time = monitor['last_check_time']

                try:
                    # 连接IMAP服务器
                    mail = imaplib.IMAP4_SSL(server, port)
                    mail.login(account, password)
                    mail.select('INBOX')

                    # 搜索未读邮件
                    status, messages = mail.search(None, 'UNSEEN')
                    if status == 'OK':
                        email_ids = messages[0].split()

                        for email_id in email_ids:
                            # 获取邮件
                            status, msg_data = mail.fetch(email_id, '(RFC822)')
                            if status != 'OK':
                                continue

                            # 解析邮件
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)

                            # 获取邮件信息
                            from_addr = email.utils.parseaddr(msg.get('From', ''))[1]
                            subject = self._decode_email_header(msg.get('Subject', ''))
                            date_str = msg.get('Date', '')
                            
                            # 获取邮件正文
                            body = self._get_email_body(msg)

                            # 应用过滤器
                            if from_filter and from_filter not in from_addr:
                                continue
                            if subject_filter and subject_filter not in subject:
                                continue

                            # 触发回调
                            email_data = {
                                'from': from_addr,
                                'subject': subject,
                                'date': date_str,
                                'body': body,
                                'timestamp': datetime.now().isoformat()
                            }
                            callback(email_data)

                            # 标记为已读
                            mail.store(email_id, '+FLAGS', '\\Seen')

                            # 更新最后检查时间
                            monitor['last_check_time'] = time.time()

                            # 触发后退出
                            mail.close()
                            mail.logout()
                            return

                    mail.close()
                    mail.logout()

                except Exception as e:
                    print(f"[TriggerManager] 邮件检查失败: {e}")

                # 等待下次检查
                await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[TriggerManager] 邮件监控异常: {e}")

    def _decode_email_header(self, header: str) -> str:
        """解码邮件头"""
        decoded_parts = []
        for part, encoding in email.header.decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        return ''.join(decoded_parts)

    def _get_email_body(self, msg) -> str:
        """获取邮件正文"""
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        return body


# 全局触发器管理器实例
trigger_manager = TriggerManager()
