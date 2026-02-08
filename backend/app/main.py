import asyncio
import sys
import threading
import uuid
from pathlib import Path

# Windows 上需要设置事件循环策略以支持 Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

# 创建Socket.IO服务器
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=120,  # ping 超时 120秒
    ping_interval=25,  # ping 间隔 25秒
)

# 创建FastAPI应用
app = FastAPI(
    title="Web Automation API",
    description="网页自动化工作流构建平台后端API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入并注册路由
from app.api.workflows import router as workflows_router
from app.api.element_picker import router as element_picker_router
from app.api.data_assets import router as data_assets_router
from app.api.image_assets import router as image_assets_router
from app.api.browser import router as browser_router
from app.api.system import router as system_router, set_napcat_sio
from app.api.local_workflows import router as local_workflows_router
from app.api.triggers import router as triggers_router
from app.api.scheduled_tasks import router as scheduled_tasks_router
app.include_router(workflows_router)
app.include_router(element_picker_router)
app.include_router(data_assets_router)
app.include_router(image_assets_router)
app.include_router(browser_router)
app.include_router(system_router)
app.include_router(local_workflows_router)
app.include_router(triggers_router)
app.include_router(scheduled_tasks_router)

# 设置 NapCat 的 socketio 实例
set_napcat_sio(sio)

# 将Socket.IO挂载到FastAPI
socket_app = socketio.ASGIApp(sio, app)


@app.get("/")
async def root():
    return {"message": "Web Automation API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/config")
async def get_config():
    """获取服务配置信息"""
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'WebRPAConfig.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    "backend": config.get('backend', {}),
                    "frontend": config.get('frontend', {}),
                    "frameworkHub": config.get('frameworkHub', {})
                }
    except Exception as e:
        print(f"[Config API] 读取配置文件失败: {e}")
    
    # 返回默认配置
    return {
        "backend": {"host": "0.0.0.0", "port": 8000, "reload": False},
        "frontend": {"host": "0.0.0.0", "port": 5173},
        "frameworkHub": {"host": "0.0.0.0", "port": 3000}
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时设置主事件循环"""
    loop = asyncio.get_event_loop()
    set_main_loop(loop)
    
    # 启动全局热键服务
    from app.services.global_hotkey import get_hotkey_service
    hotkey_service = get_hotkey_service()
    hotkey_service.set_main_loop(loop)
    hotkey_service.set_callbacks(
        on_run=on_hotkey_run_workflow,
        on_stop=on_hotkey_stop_workflow,
        on_macro_start=on_hotkey_macro_start,
        on_macro_stop=on_hotkey_macro_stop
    )
    hotkey_service.start()
    
    # 初始化计划任务管理器的工作流执行回调
    from app.services.scheduled_task_manager import scheduled_task_manager
    from app.api.workflows import workflows_store, executions_store, execution_results, execution_data
    from app.api.local_workflows import DEFAULT_WORKFLOW_FOLDER
    from app.services.workflow_executor import WorkflowExecutor
    from app.models.workflow import Workflow
    import json
    
    async def execute_workflow_for_scheduled_task(workflow_filename: str, task_id: str = None):
        """为计划任务执行工作流
        
        Args:
            workflow_filename: 工作流文件名
            task_id: 计划任务ID（用于保存执行器引用）
        
        Returns:
            dict: 包含执行结果和执行器引用
        """
        from pathlib import Path
        
        executor = None
        try:
            # 先尝试从内存中获取工作流
            workflow = workflows_store.get(workflow_filename)
            
            # 如果内存中没有，从文件系统加载
            if not workflow:
                try:
                    # 使用默认工作流文件夹
                    workflow_path = Path(DEFAULT_WORKFLOW_FOLDER) / workflow_filename
                    
                    if not workflow_path.exists():
                        return {
                            'success': False,
                            'error': f'工作流文件不存在: {workflow_filename}',
                            'executed_nodes': 0,
                            'failed_nodes': 0,
                            'collected_data': [],
                            'executor': None
                        }
                    
                    # 加载工作流文件
                    with open(workflow_path, 'r', encoding='utf-8') as f:
                        workflow_data = json.load(f)
                    
                    # 创建工作流对象
                    workflow = Workflow(**workflow_data)
                    
                    # 缓存到内存中
                    workflows_store[workflow_filename] = workflow
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'加载工作流失败: {str(e)}',
                        'executed_nodes': 0,
                        'failed_nodes': 0,
                        'collected_data': [],
                        'executor': None
                    }
            
            # 检查是否已在执行
            if workflow_filename in executions_store:
                existing_executor = executions_store[workflow_filename]
                if existing_executor.is_running:
                    return {
                        'success': False,
                        'error': '工作流正在执行中',
                        'executed_nodes': 0,
                        'failed_nodes': 0,
                        'collected_data': [],
                        'executor': None
                    }
            
            # 创建执行器（无回调，静默执行）
            # 使用与手动执行相同的浏览器配置，确保持久化数据可用
            browser_data_dir = Path(__file__).parent.parent / "browser_data"
            
            executor = WorkflowExecutor(
                workflow=workflow,
                headless=True,  # 计划任务默认无头模式
                browser_config={
                    'type': 'msedge',
                    'executablePath': None,
                    'fullscreen': False,
                    'launchArgs': None,
                }
            )
            
            # 设置user_data_dir以使用持久化数据
            executor.context._user_data_dir = str(browser_data_dir)
            
            executions_store[workflow_filename] = executor
            
            # 如果提供了 task_id，保存执行器引用到计划任务管理器
            if task_id:
                scheduled_task_manager.running_executors[task_id] = executor
                print(f"[execute_workflow_for_scheduled_task] 已保存执行器引用: task_id={task_id}")
            
            # 执行工作流
            result = await executor.execute()
            
            # 收集数据
            collected_data = executor.get_collected_data()
            
            # 保存结果
            execution_results[workflow_filename] = result
            execution_data[workflow_filename] = collected_data
            
            # 清理执行器
            if workflow_filename in executions_store:
                del executions_store[workflow_filename]
            
            # 判断执行状态
            is_success = result.status.value == 'completed'
            is_stopped = result.status.value == 'stopped'
            
            return {
                'success': is_success,
                'stopped': is_stopped,
                'error': None if is_success else (result.error_message or '执行失败'),
                'executed_nodes': result.executed_nodes,
                'failed_nodes': result.failed_nodes,
                'collected_data': collected_data,
                'executor': executor
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            # 清理执行器
            if workflow_filename in executions_store:
                del executions_store[workflow_filename]
            
            return {
                'success': False,
                'error': str(e),
                'executed_nodes': 0,
                'failed_nodes': 0,
                'collected_data': [],
                'executor': executor
            }
    
    scheduled_task_manager.set_workflow_executor(execute_workflow_for_scheduled_task)
    print("[ScheduledTaskManager] 工作流执行器已初始化")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    from app.services.global_hotkey import get_hotkey_service
    hotkey_service = get_hotkey_service()
    hotkey_service.stop()


# 当前活动的工作流ID（用于热键控制）
current_workflow_id: str | None = None


def set_current_workflow_id(workflow_id: str | None):
    """设置当前活动的工作流ID"""
    global current_workflow_id
    current_workflow_id = workflow_id


async def on_hotkey_run_workflow():
    """热键触发运行工作流"""
    global current_workflow_id
    
    print(f"[GlobalHotkey] 当前工作流ID: {current_workflow_id}")
    
    if not current_workflow_id:
        print("[GlobalHotkey] 没有活动的工作流")
        await sio.emit('hotkey:no_workflow', {})
        return
    
    # 通知前端执行工作流
    print(f"[GlobalHotkey] 触发运行工作流: {current_workflow_id}")
    await sio.emit('hotkey:run_workflow', {'workflowId': current_workflow_id})


async def on_hotkey_stop_workflow():
    """热键触发停止工作流"""
    global current_workflow_id
    
    if not current_workflow_id:
        print("[GlobalHotkey] 没有活动的工作流")
        return
    
    # 通知前端停止工作流
    print(f"[GlobalHotkey] 触发停止工作流")
    await sio.emit('hotkey:stop_workflow', {'workflowId': current_workflow_id})


async def on_hotkey_macro_start():
    """热键触发开始录制宏 (F9)"""
    print("[GlobalHotkey] 触发开始录制宏")
    # 通知前端开始录制宏
    await sio.emit('hotkey:macro_start', {})


async def on_hotkey_macro_stop():
    """热键触发停止录制宏 (F10)"""
    print("[GlobalHotkey] 触发停止录制宏")
    # 通知前端停止录制宏
    await sio.emit('hotkey:macro_stop', {})


# Socket.IO事件处理
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # 清理该客户端的日志开关状态
    if sid in log_enabled_by_client:
        del log_enabled_by_client[sid]


@sio.event
async def execution_stop(sid, data):
    """处理停止执行请求"""
    workflow_id = data.get('workflowId')
    if workflow_id:
        # 先清理所有等待中的事件，让阻塞的线程能够退出
        clear_all_pending_events()
        
        from app.api.workflows import executions_store
        executor = executions_store.get(workflow_id)
        if executor and executor.is_running:
            await executor.stop()


# 全局日志开关状态
log_enabled_by_client: dict[str, bool] = {}


@sio.event
async def set_verbose_log(sid, data):
    """处理详细日志开关设置"""
    enabled = data.get('enabled', False)
    log_enabled_by_client[sid] = enabled
    print(f"Client {sid} set verbose_log to {enabled}")


@sio.event
async def set_current_workflow(sid, data):
    """设置当前活动的工作流ID（用于热键控制）"""
    workflow_id = data.get('workflowId')
    set_current_workflow_id(workflow_id)
    print(f"[GlobalHotkey] 当前工作流已设置: {workflow_id} (来自客户端: {sid})")


def is_log_enabled() -> bool:
    """检查是否有客户端连接"""
    # 只要有客户端连接就发送日志，由前端决定是否显示
    return len(log_enabled_by_client) > 0 or True  # 始终返回True，确保日志发送


def clear_all_pending_events():
    """清理所有等待中的事件，用于停止执行时释放阻塞的线程"""
    # 清理输入弹窗事件
    with input_prompt_lock:
        for event in input_prompt_events.values():
            event.set()
        input_prompt_events.clear()
        input_prompt_results.clear()
    
    # 清理语音合成事件
    with tts_lock:
        for event in tts_events.values():
            event.set()
        tts_events.clear()
        tts_results.clear()
    
    # 清理JS脚本事件
    with js_script_lock:
        for event in js_script_events.values():
            event.set()
        js_script_events.clear()
        js_script_results.clear()
    
    # 清理播放音乐事件
    with play_music_lock:
        for event in play_music_events.values():
            event.set()
        play_music_events.clear()
        play_music_results.clear()
    
    # 清理播放视频事件
    with play_video_lock:
        for event in play_video_events.values():
            event.set()
        play_video_events.clear()
        play_video_results.clear()
    
    # 清理查看图片事件
    with view_image_lock:
        for event in view_image_events.values():
            event.set()
        view_image_events.clear()
        view_image_results.clear()


# 存储输入弹窗的等待事件（使用线程安全的Event）
input_prompt_events: dict[str, threading.Event] = {}
input_prompt_results: dict[str, str | None] = {}
input_prompt_lock = threading.Lock()

# 存储语音合成的等待事件
tts_events: dict[str, threading.Event] = {}
tts_results: dict[str, bool] = {}
tts_lock = threading.Lock()

# 存储JS脚本执行的等待事件
js_script_events: dict[str, threading.Event] = {}
js_script_results: dict[str, dict] = {}
js_script_lock = threading.Lock()

# 存储播放音乐的等待事件
play_music_events: dict[str, threading.Event] = {}
play_music_results: dict[str, dict] = {}
play_music_lock = threading.Lock()

# 存储播放视频的等待事件
play_video_events: dict[str, threading.Event] = {}
play_video_results: dict[str, dict] = {}
play_video_lock = threading.Lock()

# 存储查看图片的等待事件
view_image_events: dict[str, threading.Event] = {}
view_image_results: dict[str, dict] = {}
view_image_lock = threading.Lock()

# 存储主事件循环引用
main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop):
    """设置主事件循环引用"""
    global main_loop
    main_loop = loop


@sio.event
async def input_prompt_result(sid, data):
    """处理输入弹窗结果"""
    request_id = data.get('requestId')
    value = data.get('value')
    
    if request_id:
        with input_prompt_lock:
            input_prompt_results[request_id] = value
            if request_id in input_prompt_events:
                input_prompt_events[request_id].set()


@sio.event
async def tts_result(sid, data):
    """处理语音合成结果"""
    request_id = data.get('requestId')
    success = data.get('success', False)
    
    if request_id:
        with tts_lock:
            tts_results[request_id] = success
            if request_id in tts_events:
                tts_events[request_id].set()


@sio.event
async def js_script_result(sid, data):
    """处理JS脚本执行结果"""
    request_id = data.get('requestId')
    
    if request_id:
        with js_script_lock:
            js_script_results[request_id] = {
                'success': data.get('success', False),
                'result': data.get('result'),
                'error': data.get('error'),
            }
            if request_id in js_script_events:
                js_script_events[request_id].set()


@sio.event
async def play_music_result(sid, data):
    """处理播放音乐结果"""
    request_id = data.get('requestId')
    
    if request_id:
        with play_music_lock:
            play_music_results[request_id] = {
                'success': data.get('success', False),
                'error': data.get('error'),
            }
            if request_id in play_music_events:
                play_music_events[request_id].set()


@sio.event
async def play_video_result(sid, data):
    """处理播放视频结果"""
    request_id = data.get('requestId')
    
    if request_id:
        with play_video_lock:
            play_video_results[request_id] = {
                'success': data.get('success', False),
                'error': data.get('error'),
            }
            if request_id in play_video_events:
                play_video_events[request_id].set()


@sio.event
async def view_image_result(sid, data):
    """处理查看图片结果"""
    request_id = data.get('requestId')
    
    if request_id:
        with view_image_lock:
            view_image_results[request_id] = {
                'success': data.get('success', False),
                'error': data.get('error'),
            }
            if request_id in view_image_events:
                view_image_events[request_id].set()


def request_input_prompt_sync(
    variable_name: str, 
    title: str, 
    message: str, 
    default_value: str, 
    input_mode: str = 'single',
    min_value: float | None = None,
    max_value: float | None = None,
    max_length: int | None = None,
    required: bool = True,
    select_options: list | None = None,
    timeout: float = 300
) -> str | None:
    """同步请求前端弹出输入框并等待结果（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with input_prompt_lock:
        input_prompt_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:input_prompt', {
                'requestId': request_id,
                'variableName': variable_name,
                'title': title,
                'message': message,
                'defaultValue': default_value,
                'inputMode': input_mode,
                'minValue': min_value,
                'maxValue': max_value,
                'maxLength': max_length,
                'required': required,
                'selectOptions': select_options,
            }),
            main_loop
        )
    
    try:
        # 等待用户输入（带超时）
        if event.wait(timeout=timeout):
            with input_prompt_lock:
                result = input_prompt_results.get(request_id)
            return result
        return None
    finally:
        # 清理
        with input_prompt_lock:
            input_prompt_events.pop(request_id, None)
            input_prompt_results.pop(request_id, None)


def request_tts_sync(text: str, lang: str, rate: float, pitch: float, volume: float, timeout: float = 60) -> bool:
    """同步请求前端执行语音合成并等待完成（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with tts_lock:
        tts_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:tts_request', {
                'requestId': request_id,
                'text': text,
                'lang': lang,
                'rate': rate,
                'pitch': pitch,
                'volume': volume,
            }),
            main_loop
        )
    
    try:
        # 等待语音合成完成（带超时）
        if event.wait(timeout=timeout):
            with tts_lock:
                result = tts_results.get(request_id, False)
            return result
        return False
    finally:
        # 清理
        with tts_lock:
            tts_events.pop(request_id, None)
            tts_results.pop(request_id, None)


def request_js_script_sync(code: str, variables: dict, timeout: float = 30) -> dict:
    """同步请求前端执行JS脚本并等待结果（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with js_script_lock:
        js_script_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:js_script', {
                'requestId': request_id,
                'code': code,
                'variables': variables,
            }),
            main_loop
        )
    
    try:
        # 等待脚本执行完成（带超时）
        if event.wait(timeout=timeout):
            with js_script_lock:
                result = js_script_results.get(request_id, {'success': False, 'error': '未知错误'})
            return result
        return {'success': False, 'error': f'脚本执行超时 ({timeout}秒)'}
    finally:
        # 清理
        with js_script_lock:
            js_script_events.pop(request_id, None)
            js_script_results.pop(request_id, None)


def request_play_music_sync(audio_url: str, wait_for_end: bool, timeout: float = 600) -> dict:
    """同步请求前端播放音乐（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with play_music_lock:
        play_music_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:play_music', {
                'requestId': request_id,
                'audioUrl': audio_url,
                'waitForEnd': wait_for_end,
            }),
            main_loop
        )
    
    try:
        # 等待播放完成（带超时）
        if event.wait(timeout=timeout):
            with play_music_lock:
                result = play_music_results.get(request_id, {'success': False, 'error': '未知错误'})
            return result
        return {'success': False, 'error': f'播放超时 ({timeout}秒)'}
    finally:
        # 清理
        with play_music_lock:
            play_music_events.pop(request_id, None)
            play_music_results.pop(request_id, None)


def request_play_video_sync(video_url: str, wait_for_end: bool, timeout: float = 600) -> dict:
    """同步请求前端播放视频（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with play_video_lock:
        play_video_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:play_video', {
                'requestId': request_id,
                'videoUrl': video_url,
                'waitForEnd': wait_for_end,
            }),
            main_loop
        )
    
    try:
        # 等待播放完成（带超时）
        if event.wait(timeout=timeout):
            with play_video_lock:
                result = play_video_results.get(request_id, {'success': False, 'error': '未知错误'})
            return result
        return {'success': False, 'error': f'播放超时 ({timeout}秒)'}
    finally:
        # 清理
        with play_video_lock:
            play_video_events.pop(request_id, None)
            play_video_results.pop(request_id, None)


def request_view_image_sync(image_url: str, auto_close: bool, display_time: int, timeout: float = 300) -> dict:
    """同步请求前端查看图片（可在工作线程中调用）"""
    request_id = str(uuid.uuid4())
    
    # 创建线程安全的等待事件
    event = threading.Event()
    with view_image_lock:
        view_image_events[request_id] = event
    
    # 在主事件循环中发送WebSocket消息
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            sio.emit('execution:view_image', {
                'requestId': request_id,
                'imageUrl': image_url,
                'autoClose': auto_close,
                'displayTime': display_time,
            }),
            main_loop
        )
    
    try:
        # 等待查看完成（带超时）
        if event.wait(timeout=timeout):
            with view_image_lock:
                result = view_image_results.get(request_id, {'success': False, 'error': '未知错误'})
            return result
        return {'success': False, 'error': f'查看超时 ({timeout}秒)'}
    finally:
        # 清理
        with view_image_lock:
            view_image_events.pop(request_id, None)
            view_image_results.pop(request_id, None)


# 导出socket_app作为ASGI应用
def get_app():
    return socket_app
