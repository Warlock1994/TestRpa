"""媒体处理模块 - 桌面录屏"""
import asyncio
import os
import time
import threading

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int


# 全局摄像头录制管理器
class CameraRecordManager:
    """摄像头录制管理器 - 管理后台录制任务"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recordings: dict[str, dict] = {}
        return cls._instance
    
    async def start_recording(self, recording_id: str, output_path: str, duration: int,
                              camera_index: int = 0, fps: int = 30, resolution: str = ''):
        """开始录制摄像头"""
        async with self._lock:
            if recording_id in self._recordings:
                return False, "录制任务已存在"
            
            self._recordings[recording_id] = {
                'output_path': output_path,
                'duration': duration,
                'camera_index': camera_index,
                'fps': fps,
                'resolution': resolution,
                'status': 'recording',
                'start_time': time.time(),
                'thread': None,
                'stop_event': threading.Event()
            }
        
        def record_thread():
            try:
                self._do_recording(recording_id, output_path, duration, camera_index, fps, resolution)
            except Exception as e:
                print(f"[CameraRecord] 录制异常: {e}")
                self._recordings[recording_id]['status'] = 'error'
                self._recordings[recording_id]['error'] = str(e)
        
        thread = threading.Thread(target=record_thread, daemon=True)
        self._recordings[recording_id]['thread'] = thread
        thread.start()
        
        return True, "摄像头录制已开始"
    
    def _do_recording(self, recording_id: str, output_path: str, duration: int,
                      camera_index: int, fps: int, resolution: str):
        """执行实际的录制操作"""
        import cv2
        
        try:
            # 打开摄像头
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                self._recordings[recording_id]['status'] = 'error'
                self._recordings[recording_id]['error'] = f'无法打开摄像头 {camera_index}'
                return
            
            # 设置分辨率（如果指定）
            if resolution:
                try:
                    width, height = map(int, resolution.split('x'))
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                except:
                    pass
            
            # 获取实际分辨率
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 确保宽高是偶数（MP4编码要求）
            width = width - (width % 2)
            height = height - (height % 2)
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            frames = []
            stop_event = self._recordings[recording_id]['stop_event']
            start_time = time.time()
            target_interval = 1.0 / fps
            next_frame_time = start_time
            
            print(f"[CameraRecord] 开始录制，摄像头: {camera_index}, 目标帧率: {fps}, 时长: {duration}秒")
            
            try:
                # 收集所有帧
                while time.time() - start_time < duration:
                    if stop_event.is_set():
                        break
                    
                    current_time = time.time()
                    
                    # 如果还没到下一帧的时间，等待
                    if current_time < next_frame_time:
                        time.sleep(max(0.001, next_frame_time - current_time))
                        continue
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 调整帧大小（如果需要）
                    if frame.shape[1] != width or frame.shape[0] != height:
                        frame = cv2.resize(frame, (width, height))
                    
                    frames.append(frame)
                    
                    # 计算下一帧的时间
                    next_frame_time += target_interval
                
                actual_duration = time.time() - start_time
                frame_count = len(frames)
                
                if frame_count == 0:
                    self._recordings[recording_id]['status'] = 'error'
                    self._recordings[recording_id]['error'] = '未捕获到任何帧'
                    cap.release()
                    return
                
                # 计算实际帧率
                actual_fps = frame_count / actual_duration
                print(f"[CameraRecord] 实际捕获: {frame_count}帧, 时长: {actual_duration:.2f}秒, 实际帧率: {actual_fps:.2f}")
                
                # 使用实际帧率创建视频写入器
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, actual_fps, (width, height))
                
                # 写入所有帧
                for frame in frames:
                    out.write(frame)
                
                out.release()
                cap.release()
                
                self._recordings[recording_id]['status'] = 'completed'
                self._recordings[recording_id]['frame_count'] = frame_count
                self._recordings[recording_id]['actual_fps'] = actual_fps
                self._recordings[recording_id]['actual_duration'] = actual_duration
                print(f"[CameraRecord] 录制完成: {output_path}, 帧数: {frame_count}, 帧率: {actual_fps:.2f}")
                
            except Exception as e:
                self._recordings[recording_id]['status'] = 'error'
                self._recordings[recording_id]['error'] = str(e)
                print(f"[CameraRecord] 录制异常: {e}")
                cap.release()
        
        except Exception as e:
            self._recordings[recording_id]['status'] = 'error'
            self._recordings[recording_id]['error'] = str(e)
            print(f"[CameraRecord] 初始化异常: {e}")
    
    async def stop_recording(self, recording_id: str):
        """停止录制"""
        async with self._lock:
            if recording_id not in self._recordings:
                return False, "录制任务不存在"
            
            self._recordings[recording_id]['stop_event'].set()
            return True, "已发送停止信号"
    
    def get_status(self, recording_id: str) -> dict:
        """获取录制状态"""
        return self._recordings.get(recording_id, {})


# 全局录屏管理器
class ScreenRecordManager:
    """屏幕录制管理器 - 管理后台录屏任务"""
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recordings: dict[str, dict] = {}
        return cls._instance
    
    async def start_recording(self, recording_id: str, output_path: str, duration: int, 
                              fps: int = 30, quality: str = 'medium'):
        """开始录屏"""
        async with self._lock:
            if recording_id in self._recordings:
                return False, "录屏任务已存在"
            
            self._recordings[recording_id] = {
                'output_path': output_path,
                'duration': duration,
                'status': 'recording',
                'start_time': time.time(),
                'thread': None,
                'stop_event': threading.Event()
            }
        
        def record_thread():
            try:
                self._do_recording(recording_id, output_path, duration, fps, quality)
            except Exception as e:
                print(f"[ScreenRecord] 录屏异常: {e}")
                self._recordings[recording_id]['status'] = 'error'
                self._recordings[recording_id]['error'] = str(e)
        
        thread = threading.Thread(target=record_thread, daemon=True)
        self._recordings[recording_id]['thread'] = thread
        thread.start()
        
        return True, "录屏已开始"

    def _do_recording(self, recording_id: str, output_path: str, duration: int, 
                      fps: int, quality: str):
        """执行实际的录屏操作"""
        import cv2
        import numpy as np
        from PIL import ImageGrab
        import ctypes
        
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass
        
        screen = ImageGrab.grab()
        width, height = screen.size
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        
        scale = {'low': 0.5, 'medium': 0.75, 'high': 1.0}.get(quality, 0.75)
        out_width = int(width * scale)
        out_height = int(height * scale)
        
        out_width = out_width - (out_width % 2)
        out_height = out_height - (out_height % 2)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        frames = []
        timestamps = []
        
        stop_event = self._recordings[recording_id]['stop_event']
        start_time = time.time()
        target_interval = 1.0 / fps
        
        print(f"[ScreenRecord] 开始录制，目标帧率: {fps}, 时长: {duration}秒")
        
        try:
            while time.time() - start_time < duration:
                if stop_event.is_set():
                    break
                
                frame_start = time.time()
                
                screen = ImageGrab.grab()
                frame = np.array(screen)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                if scale != 1.0:
                    frame = cv2.resize(frame, (out_width, out_height))
                
                frames.append(frame)
                timestamps.append(time.time() - start_time)
                
                elapsed = time.time() - frame_start
                if elapsed < target_interval:
                    time.sleep(target_interval - elapsed)
            
            actual_duration = time.time() - start_time
            actual_frame_count = len(frames)
            
            if actual_frame_count == 0:
                self._recordings[recording_id]['status'] = 'error'
                self._recordings[recording_id]['error'] = '未捕获到任何帧'
                return
            
            actual_fps = actual_frame_count / actual_duration
            print(f"[ScreenRecord] 实际捕获: {actual_frame_count}帧, 时长: {actual_duration:.2f}秒, 实际帧率: {actual_fps:.2f}")
            
            out = cv2.VideoWriter(output_path, fourcc, actual_fps, (out_width, out_height))
            
            for frame in frames:
                out.write(frame)
            
            out.release()
            
            self._recordings[recording_id]['status'] = 'completed'
            print(f"[ScreenRecord] 录屏完成: {output_path}, 帧数: {actual_frame_count}, 帧率: {actual_fps:.2f}")
            
        except Exception as e:
            self._recordings[recording_id]['status'] = 'error'
            self._recordings[recording_id]['error'] = str(e)
            print(f"[ScreenRecord] 录屏异常: {e}")
    
    async def stop_recording(self, recording_id: str):
        """停止录屏"""
        async with self._lock:
            if recording_id not in self._recordings:
                return False, "录屏任务不存在"
            
            self._recordings[recording_id]['stop_event'].set()
            return True, "已发送停止信号"
    
    def get_status(self, recording_id: str) -> dict:
        """获取录屏状态"""
        return self._recordings.get(recording_id, {})


# 全局录屏管理器实例
screen_record_manager = ScreenRecordManager()

# 全局摄像头录制管理器实例
camera_record_manager = CameraRecordManager()


@register_executor
class ScreenRecordExecutor(ModuleExecutor):
    """桌面录屏模块执行器 - 非阻塞式录屏"""
    
    @property
    def module_type(self) -> str:
        return "screen_record"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        duration = to_int(config.get('duration', 30), 30, context)
        output_folder = context.resolve_value(config.get('outputFolder', ''))
        filename = context.resolve_value(config.get('filename', ''))
        fps = to_int(config.get('fps', 30), 30, context)
        quality = context.resolve_value(config.get('quality', 'medium'))
        result_variable = config.get('resultVariable', 'recording_path')
        
        try:
            if not output_folder:
                output_folder = os.path.join(os.path.expanduser('~'), 'Videos', 'WebRPA')
            
            os.makedirs(output_folder, exist_ok=True)
            
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"screen_record_{timestamp}.mp4"
            
            if not filename.endswith('.mp4'):
                filename += '.mp4'
            
            output_path = os.path.join(output_folder, filename)
            recording_id = f"rec_{int(time.time() * 1000)}"
            
            success, message = await screen_record_manager.start_recording(
                recording_id, output_path, duration, fps, quality
            )
            
            if not success:
                return ModuleResult(success=False, error=message)
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"录屏已开始，时长: {duration}秒，保存到: {output_path}",
                data={
                    'recording_id': recording_id,
                    'output_path': output_path,
                    'duration': duration,
                    'fps': fps,
                    'quality': quality
                }
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"启动录屏失败: {str(e)}")


@register_executor
class CameraCaptureExecutor(ModuleExecutor):
    """摄像头拍照模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "camera_capture"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        摄像头拍照 - 拍摄摄像头画面并保存
        配置项：
        - cameraIndex: 摄像头索引（默认0）
        - outputFolder: 输出文件夹
        - filename: 文件名（可选）
        - saveToVariable: 保存文件路径的变量名
        """
        camera_index = to_int(config.get('cameraIndex', 0), 0, context)
        output_folder = context.resolve_value(config.get('outputFolder', ''))
        filename = context.resolve_value(config.get('filename', ''))
        save_to_variable = config.get('saveToVariable', 'camera_photo')
        
        try:
            import cv2
            
            # 设置输出路径
            if not output_folder:
                output_folder = os.path.join(os.path.expanduser('~'), 'Pictures', 'WebRPA')
            
            os.makedirs(output_folder, exist_ok=True)
            
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"camera_{timestamp}.jpg"
            
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename += '.jpg'
            
            output_path = os.path.join(output_folder, filename)
            
            context.add_log('info', f"📷 正在打开摄像头 {camera_index}...", None)
            await context.send_progress(f"📷 正在打开摄像头...")
            
            # 打开摄像头
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return ModuleResult(success=False, error=f"无法打开摄像头 {camera_index}")
            
            # 等待摄像头稳定
            await asyncio.sleep(0.5)
            
            # 读取帧
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return ModuleResult(success=False, error="无法从摄像头读取画面")
            
            # 保存图片
            cv2.imwrite(output_path, frame)
            
            context.add_log('info', f"✅ 照片已保存: {output_path}", None)
            
            # 保存路径到变量
            if save_to_variable:
                context.set_variable(save_to_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"摄像头拍照完成: {output_path}",
                data={'output_path': output_path}
            )
        
        except ImportError:
            return ModuleResult(
                success=False,
                error="摄像头拍照失败，请检查摄像头连接"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"摄像头拍照失败: {str(e)}")


@register_executor
class CameraRecordExecutor(ModuleExecutor):
    """摄像头录像模块执行器 - 非阻塞式录制"""
    
    @property
    def module_type(self) -> str:
        return "camera_record"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        摄像头录像 - 录制摄像头视频（非阻塞）
        配置项：
        - cameraIndex: 摄像头索引（默认0）
        - duration: 录制时长（秒）
        - outputFolder: 输出文件夹
        - filename: 文件名（可选）
        - fps: 帧率（默认30）
        - resolution: 分辨率（可选，如 1280x720）
        - saveToVariable: 保存文件路径的变量名
        """
        camera_index = to_int(config.get('cameraIndex', 0), 0, context)
        duration = to_int(config.get('duration', 10), 10, context)
        output_folder = context.resolve_value(config.get('outputFolder', ''))
        filename = context.resolve_value(config.get('filename', ''))
        fps = to_int(config.get('fps', 30), 30, context)
        resolution = context.resolve_value(config.get('resolution', ''))
        save_to_variable = config.get('saveToVariable', 'camera_video')
        
        try:
            # 设置输出路径
            if not output_folder:
                output_folder = os.path.join(os.path.expanduser('~'), 'Videos', 'WebRPA')
            
            os.makedirs(output_folder, exist_ok=True)
            
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"camera_{timestamp}.mp4"
            
            if not filename.endswith('.mp4'):
                filename += '.mp4'
            
            output_path = os.path.join(output_folder, filename)
            recording_id = f"cam_{int(time.time() * 1000)}"
            
            success, message = await camera_record_manager.start_recording(
                recording_id, output_path, duration, camera_index, fps, resolution
            )
            
            if not success:
                return ModuleResult(success=False, error=message)
            
            # 保存路径到变量
            if save_to_variable:
                context.set_variable(save_to_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"摄像头录制已开始，时长: {duration}秒，保存到: {output_path}",
                data={
                    'recording_id': recording_id,
                    'output_path': output_path,
                    'duration': duration,
                    'camera_index': camera_index,
                    'fps': fps,
                    'resolution': resolution
                }
            )
        
        except ImportError:
            return ModuleResult(
                success=False,
                error="摄像头录像失败，请检查摄像头连接"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"启动摄像头录制失败: {str(e)}")
