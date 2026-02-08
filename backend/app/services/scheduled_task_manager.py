"""计划任务调度管理服务"""
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.models.scheduled_task import (
    ScheduledTask,
    ScheduledTaskExecutionLog,
    ScheduledTaskExecutionLogCreate
)
from app.services.trigger_manager import trigger_manager


class ScheduledTaskManager:
    """计划任务管理器"""
    
    def __init__(self, data_dir: str = "backend/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.tasks_file = self.data_dir / "scheduled_tasks.json"
        self.logs_file = self.data_dir / "scheduled_task_logs.json"
        
        # 内存存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.logs: List[ScheduledTaskExecutionLog] = []
        
        # APScheduler调度器
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        
        # 热键触发器映射
        self.hotkey_triggers: Dict[str, str] = {}  # trigger_id -> task_id
        
        # 工作流执行回调
        self.workflow_executor_callback = None
        
        # 保存事件循环引用
        self.event_loop = None
        
        # 正在执行的任务（用于强制停止）
        self.running_tasks: Dict[str, asyncio.Task] = {}  # task_id -> asyncio.Task
        
        # 正在执行的工作流执行器（用于强制停止工作流）
        self.running_executors: Dict[str, any] = {}  # task_id -> WorkflowExecutor
        
        # 标记是否已执行启动触发器
        self.startup_triggers_executed = False
        
        # 加载数据
        self._load_tasks()
        self._load_logs()
        
        print("[ScheduledTaskManager] 计划任务管理器已初始化")
    
    def set_workflow_executor(self, callback):
        """设置工作流执行回调函数"""
        self.workflow_executor_callback = callback
        # 同时保存当前事件循环
        try:
            self.event_loop = asyncio.get_running_loop()
            print("[ScheduledTaskManager] 工作流执行器已初始化")
            
            # 在工作流执行器初始化后,执行启动触发器(只执行一次)
            if not self.startup_triggers_executed:
                self._execute_startup_triggers()
                self.startup_triggers_executed = True
        except RuntimeError:
            print("[ScheduledTaskManager] 警告: 无法获取运行中的事件循环")
    
    # ==================== 任务管理 ====================
    
    def create_task(self, task: ScheduledTask) -> ScheduledTask:
        """创建计划任务"""
        self.tasks[task.id] = task
        self._save_tasks()
        
        # 如果任务已启用，注册触发器
        if task.enabled:
            self._register_task_trigger(task)
        
        print(f"[ScheduledTaskManager] 创建任务: {task.name} ({task.id})")
        return task
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取计划任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[ScheduledTask]:
        """获取所有计划任务"""
        return list(self.tasks.values())
    
    def update_task(self, task_id: str, updates: dict) -> Optional[ScheduledTask]:
        """更新计划任务"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        # 保存旧的启用状态
        old_enabled = task.enabled
        
        # 更新字段
        for key, value in updates.items():
            if value is not None and hasattr(task, key):
                # 如果是 trigger 字段，需要转换为对象
                if key == 'trigger' and isinstance(value, dict):
                    from app.models.scheduled_task import ScheduledTaskTrigger
                    value = ScheduledTaskTrigger(**value)
                setattr(task, key, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save_tasks()
        
        # 如果启用状态或触发器配置改变，重新注册触发器
        if old_enabled != task.enabled or 'trigger' in updates:
            self._unregister_task_trigger(task)
            if task.enabled:
                self._register_task_trigger(task)
        
        print(f"[ScheduledTaskManager] 更新任务: {task.name} ({task_id})")
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """删除计划任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # 注销触发器
        self._unregister_task_trigger(task)
        
        # 删除任务
        del self.tasks[task_id]
        self._save_tasks()
        
        print(f"[ScheduledTaskManager] 删除任务: {task.name} ({task_id})")
        return True
    
    def toggle_task(self, task_id: str, enabled: bool) -> Optional[ScheduledTask]:
        """启用/禁用计划任务"""
        return self.update_task(task_id, {'enabled': enabled})
    
    # ==================== 触发器注册 ====================
    
    def _register_task_trigger(self, task: ScheduledTask):
        """注册任务触发器"""
        trigger = task.trigger
        
        if trigger.type == 'time':
            self._register_time_trigger(task)
        elif trigger.type == 'hotkey':
            self._register_hotkey_trigger(task)
        elif trigger.type == 'startup':
            # 启动触发器不在这里注册,而是在服务启动时统一执行
            pass
    
    def _unregister_task_trigger(self, task: ScheduledTask):
        """注销任务触发器"""
        trigger = task.trigger
        
        if trigger.type == 'time':
            # 移除APScheduler任务
            try:
                self.scheduler.remove_job(task.id)
            except:
                pass
        elif trigger.type == 'hotkey':
            # 移除热键触发器
            for trigger_id, task_id in list(self.hotkey_triggers.items()):
                if task_id == task.id:
                    trigger_manager.unregister_hotkey(trigger_id)
                    del self.hotkey_triggers[trigger_id]
        elif trigger.type == 'startup':
            # 启动触发器不需要注销
            pass
    
    def _register_time_trigger(self, task: ScheduledTask):
        """注册时间触发器"""
        trigger = task.trigger
        schedule_type = trigger.schedule_type
        
        try:
            if schedule_type == 'once':
                # 一次性执行
                start_datetime = datetime.fromisoformat(f"{trigger.start_date} {trigger.start_time}")
                apscheduler_trigger = DateTrigger(run_date=start_datetime)
                
            elif schedule_type == 'daily':
                # 每日执行
                hour, minute, second = map(int, trigger.daily_time.split(':'))
                apscheduler_trigger = CronTrigger(hour=hour, minute=minute, second=second)
                
            elif schedule_type == 'weekly':
                # 每周执行
                hour, minute, second = map(int, trigger.weekly_time.split(':'))
                # APScheduler的day_of_week: 0=周一, 6=周日
                # 我们的weekly_days: 0=周日, 1=周一, ...
                # 需要转换
                days_of_week = ','.join([str((day - 1) % 7) for day in trigger.weekly_days])
                apscheduler_trigger = CronTrigger(
                    day_of_week=days_of_week,
                    hour=hour,
                    minute=minute,
                    second=second
                )
                
            elif schedule_type == 'monthly':
                # 每月执行
                hour, minute, second = map(int, trigger.monthly_time.split(':'))
                apscheduler_trigger = CronTrigger(
                    day=trigger.monthly_day,
                    hour=hour,
                    minute=minute,
                    second=second
                )
                
            elif schedule_type == 'interval':
                # 间隔执行
                apscheduler_trigger = IntervalTrigger(seconds=trigger.interval_seconds)
            
            else:
                print(f"[ScheduledTaskManager] 未知的调度类型: {schedule_type}")
                return
            
            # 添加到调度器
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=apscheduler_trigger,
                args=[task.id, 'time'],
                id=task.id,
                replace_existing=True
            )
            
            # 更新下次执行时间
            job = self.scheduler.get_job(task.id)
            if job and job.next_run_time:
                task.next_execution_time = job.next_run_time.isoformat()
                self._save_tasks()
            
            print(f"[ScheduledTaskManager] 注册时间触发器: {task.name} ({schedule_type})")
            
        except Exception as e:
            print(f"[ScheduledTaskManager] 注册时间触发器失败: {e}")
    
    def _register_hotkey_trigger(self, task: ScheduledTask):
        """注册热键触发器"""
        trigger = task.trigger
        hotkey = trigger.hotkey
        
        if not hotkey:
            return
        
        # 创建回调函数 - 需要在非事件循环线程中安全调度
        def callback():
            # 使用保存的事件循环引用
            try:
                if self.event_loop and not self.event_loop.is_closed():
                    # 使用call_soon_threadsafe在事件循环中调度协程
                    asyncio.run_coroutine_threadsafe(
                        self._execute_task(task.id, 'hotkey'),
                        self.event_loop
                    )
                else:
                    print(f"[ScheduledTaskManager] 事件循环不可用,无法执行热键任务")
            except Exception as e:
                print(f"[ScheduledTaskManager] 热键回调异常: {e}")
        
        # 注册热键
        trigger_id = trigger_manager.register_hotkey(hotkey, callback)
        self.hotkey_triggers[trigger_id] = task.id
        
        print(f"[ScheduledTaskManager] 注册热键触发器: {task.name} ({hotkey})")
    
    def _register_startup_trigger(self, task: ScheduledTask):
        """注册启动触发器 - 已废弃,改用_execute_startup_triggers"""
        pass
    
    def _execute_startup_triggers(self):
        """执行所有启动触发器(仅在服务启动时执行一次)"""
        startup_tasks = [task for task in self.tasks.values() 
                        if task.enabled and task.trigger.type == 'startup']
        
        if not startup_tasks:
            return
        
        print(f"[ScheduledTaskManager] 发现 {len(startup_tasks)} 个启动触发任务")
        
        for task in startup_tasks:
            delay = task.trigger.startup_delay or 0
            
            # 延迟执行
            async def delayed_execute(task_id: str, task_name: str, delay_seconds: int):
                if delay_seconds > 0:
                    print(f"[ScheduledTaskManager] 启动任务 {task_name} 将在 {delay_seconds} 秒后执行")
                    await asyncio.sleep(delay_seconds)
                await self._execute_task(task_id, 'startup')
            
            # 使用事件循环调度
            if self.event_loop:
                asyncio.run_coroutine_threadsafe(
                    delayed_execute(task.id, task.name, delay),
                    self.event_loop
                )
                print(f"[ScheduledTaskManager] 已调度启动任务: {task.name} (延迟{delay}秒)")
    
    # ==================== 任务执行 ====================
    
    async def _execute_task(self, task_id: str, trigger_type: str):
        """执行计划任务"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"[ScheduledTaskManager] 任务不存在: {task_id}")
            return
        
        if not task.enabled:
            print(f"[ScheduledTaskManager] 任务已禁用: {task.name}")
            return
        
        if task.is_running:
            print(f"[ScheduledTaskManager] 任务正在执行中: {task.name}")
            return
        
        print(f"[ScheduledTaskManager] 开始执行任务: {task.name} (触发方式: {trigger_type})")
        
        # 标记为执行中
        task.is_running = True
        
        # 创建执行日志
        log = ScheduledTaskExecutionLog(
            task_id=task.id,
            task_name=task.name,
            workflow_id=task.workflow_id,
            workflow_name=task.workflow_name or '',
            trigger_type=trigger_type,
            trigger_time=datetime.now().isoformat(),
            start_time=datetime.now().isoformat(),
            status='running'
        )
        self.logs.append(log)
        self._save_logs()
        
        # 创建异步任务并保存引用
        async def execute_workflow():
            executor = None
            try:
                # 执行工作流
                if self.workflow_executor_callback:
                    result = await self.workflow_executor_callback(task.workflow_id, task_id)
                    executor = result.get('executor')  # 获取执行器引用
                    
                    # 更新日志
                    log.end_time = datetime.now().isoformat()
                    log.duration = (datetime.fromisoformat(log.end_time) - 
                                   datetime.fromisoformat(log.start_time)).total_seconds()
                    
                    # 判断执行状态
                    if result.get('stopped'):
                        # 任务被停止
                        log.status = 'stopped'
                        log.error = '任务被手动停止'
                    elif result.get('success'):
                        # 任务成功
                        log.status = 'success'
                        log.error = None
                    else:
                        # 任务失败
                        log.status = 'failed'
                        log.error = result.get('error')
                    
                    log.executed_nodes = result.get('executed_nodes', 0)
                    log.failed_nodes = result.get('failed_nodes', 0)
                    log.collected_data_count = len(result.get('collected_data', []))
                    
                    # 更新任务统计
                    task.total_executions += 1
                    if log.status == 'success':
                        task.success_executions += 1
                    else:
                        task.failed_executions += 1
                    task.last_execution_time = log.end_time
                    task.last_execution_status = log.status
                    task.last_execution_error = log.error
                    
                    print(f"[ScheduledTaskManager] 任务执行完成: {task.name} ({log.status})")
                else:
                    log.status = 'failed'
                    log.error = '工作流执行器未初始化'
                    print(f"[ScheduledTaskManager] 工作流执行器未初始化")
            
            except asyncio.CancelledError:
                # 任务被取消
                log.end_time = datetime.now().isoformat()
                log.duration = (datetime.fromisoformat(log.end_time) - 
                               datetime.fromisoformat(log.start_time)).total_seconds()
                log.status = 'stopped'
                log.error = '任务被手动停止'
                task.total_executions += 1
                task.failed_executions += 1
                task.last_execution_time = log.end_time
                task.last_execution_status = 'stopped'
                task.last_execution_error = '任务被手动停止'
                print(f"[ScheduledTaskManager] 任务被取消: {task.name}")
                raise
            
            except Exception as e:
                log.end_time = datetime.now().isoformat()
                log.status = 'failed'
                log.error = str(e)
                task.total_executions += 1
                task.failed_executions += 1
                task.last_execution_time = log.end_time
                task.last_execution_status = 'failed'
                task.last_execution_error = str(e)
                print(f"[ScheduledTaskManager] 任务执行失败: {task.name} - {e}")
            
            finally:
                # 标记为未执行
                task.is_running = False
                # 从运行任务列表中移除
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                # 从执行器列表中移除
                if task_id in self.running_executors:
                    del self.running_executors[task_id]
                self._save_tasks()
                self._save_logs()
                
                # 处理重复执行
                if task.trigger.repeat_enabled:
                    task.current_repeat_count += 1
                    if (task.trigger.repeat_count is None or 
                        task.current_repeat_count < task.trigger.repeat_count):
                        # 继续重复
                        if task.trigger.repeat_interval:
                            await asyncio.sleep(task.trigger.repeat_interval)
                            await self._execute_task(task_id, trigger_type)
                    else:
                        # 重复完成，重置计数
                        task.current_repeat_count = 0
                        self._save_tasks()
        
        # 创建并保存异步任务
        workflow_task = asyncio.create_task(execute_workflow())
        self.running_tasks[task_id] = workflow_task
        
        try:
            await workflow_task
        except asyncio.CancelledError:
            pass  # 任务被取消，已在 execute_workflow 中处理
    
    async def execute_task_manually(self, task_id: str):
        """手动执行任务"""
        await self._execute_task(task_id, 'manual')
    
    async def stop_task(self, task_id: str) -> bool:
        """强制停止正在执行的任务"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"[ScheduledTaskManager] 任务不存在: {task_id}")
            return False
        
        if not task.is_running:
            print(f"[ScheduledTaskManager] 任务未在执行: {task.name}")
            return False
        
        print(f"[ScheduledTaskManager] 开始停止任务: {task.name}")
        
        # 1. 停止工作流执行器（这是关键！）
        if task_id in self.running_executors:
            executor = self.running_executors[task_id]
            try:
                print(f"[ScheduledTaskManager] 调用工作流执行器的 stop() 方法")
                await executor.stop()
                print(f"[ScheduledTaskManager] 工作流执行器已停止")
            except Exception as e:
                print(f"[ScheduledTaskManager] 停止工作流执行器时出错: {e}")
        
        # 2. 取消正在执行的异步任务
        if task_id in self.running_tasks:
            running_task = self.running_tasks[task_id]
            if not running_task.done():
                running_task.cancel()
                print(f"[ScheduledTaskManager] 已取消异步任务")
        
        # 3. 标记为未执行
        task.is_running = False
        self._save_tasks()
        
        # 4. 更新最后一条日志
        task_logs = [log for log in self.logs if log.task_id == task_id and log.status == 'running']
        if task_logs:
            latest_log = task_logs[-1]
            latest_log.end_time = datetime.now().isoformat()
            latest_log.duration = (datetime.fromisoformat(latest_log.end_time) - 
                                  datetime.fromisoformat(latest_log.start_time)).total_seconds()
            latest_log.status = 'stopped'
            latest_log.error = '任务被手动停止'
            self._save_logs()
        
        print(f"[ScheduledTaskManager] 任务已停止: {task.name}")
        return True
    
    # ==================== 执行日志管理 ====================
    
    def get_task_logs(self, task_id: str, limit: int = 100) -> List[ScheduledTaskExecutionLog]:
        """获取任务执行日志"""
        task_logs = [log for log in self.logs if log.task_id == task_id]
        # 按时间倒序排序
        task_logs.sort(key=lambda x: x.start_time, reverse=True)
        return task_logs[:limit]
    
    def get_all_logs(self, limit: int = 100) -> List[ScheduledTaskExecutionLog]:
        """获取所有执行日志"""
        sorted_logs = sorted(self.logs, key=lambda x: x.start_time, reverse=True)
        return sorted_logs[:limit]
    
    def clear_logs(self, task_id: Optional[str] = None):
        """清空执行日志"""
        if task_id:
            self.logs = [log for log in self.logs if log.task_id != task_id]
        else:
            self.logs = []
        self._save_logs()
    
    # ==================== 数据持久化 ====================
    
    def _load_tasks(self):
        """加载任务数据"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = ScheduledTask(**task_data)
                        self.tasks[task.id] = task
                        # 如果任务已启用，注册触发器
                        if task.enabled:
                            self._register_task_trigger(task)
                print(f"[ScheduledTaskManager] 加载了 {len(self.tasks)} 个任务")
            except Exception as e:
                print(f"[ScheduledTaskManager] 加载任务失败: {e}")
    
    def _save_tasks(self):
        """保存任务数据"""
        try:
            data = [task.dict() for task in self.tasks.values()]
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ScheduledTaskManager] 保存任务失败: {e}")
    
    def _load_logs(self):
        """加载执行日志"""
        if self.logs_file.exists():
            try:
                with open(self.logs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logs = [ScheduledTaskExecutionLog(**log_data) for log_data in data]
                # 只保留最近1000条日志
                if len(self.logs) > 1000:
                    self.logs = sorted(self.logs, key=lambda x: x.start_time, reverse=True)[:1000]
                print(f"[ScheduledTaskManager] 加载了 {len(self.logs)} 条执行日志")
            except Exception as e:
                print(f"[ScheduledTaskManager] 加载日志失败: {e}")
    
    def _save_logs(self):
        """保存执行日志"""
        try:
            # 只保存最近1000条日志
            logs_to_save = sorted(self.logs, key=lambda x: x.start_time, reverse=True)[:1000]
            data = [log.dict() for log in logs_to_save]
            with open(self.logs_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ScheduledTaskManager] 保存日志失败: {e}")


# 全局计划任务管理器实例
scheduled_task_manager = ScheduledTaskManager()
