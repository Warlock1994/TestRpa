"""媒体处理模块 - 音频处理"""
import asyncio
import os

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float
from .media_utils import get_media_duration, run_ffmpeg_with_progress


@register_executor
class AdjustVolumeExecutor(ModuleExecutor):
    """音频调节音量模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "adjust_volume"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        volume = to_float(config.get('volume', 1.0), 1.0, context)
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'adjusted_audio')
        
        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")
        
        if volume < 0 or volume > 10:
            return ModuleResult(success=False, error="音量倍数必须在 0-10 之间")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_vol{volume}x{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path, '-af', f'volume={volume}', output_path]

            if duration:
                await context.send_progress(f"🎬 开始调整音量（{volume}x），预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始调整音量（{volume}x）...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=3600, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"音量调整失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"音量调整完成（{volume}x）: {output_path}",
                              data={'output_path': output_path, 'volume': volume})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="音量调整已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"音量调整失败: {str(e)}")


@register_executor
class AudioToTextExecutor(ModuleExecutor):
    """音频转文本模块执行器 - 使用本地 Whisper 模型进行语音识别"""
    
    _model_cache = {}  # 缓存已加载的模型
    
    @property
    def module_type(self) -> str:
        return "audio_to_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        language = context.resolve_value(config.get('language', 'zh'))
        model_size = config.get('modelSize', 'base')
        result_variable = config.get('resultVariable', 'transcribed_text')
        
        if not input_path:
            return ModuleResult(success=False, error="输入音频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入音频不存在: {input_path}")
        
        try:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                return ModuleResult(
                    success=False, 
                    error="请安装 faster-whisper: pip install faster-whisper"
                )
            
            import os as os_module
            os_module.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            models_dir = os.path.join(app_dir, 'data', 'whisper_models')
            os.makedirs(models_dir, exist_ok=True)
            
            local_model_path = os.path.join(models_dir, model_size)
            
            if os.path.exists(local_model_path) and os.path.isdir(local_model_path) and os.listdir(local_model_path):
                model_path = local_model_path
                print(f"[音频转文本] 使用本地模型: {model_path}")
            else:
                model_path = f"Systran/faster-whisper-{model_size}"
                print(f"[音频转文本] 从镜像下载模型: {model_path}")
            
            cache_key = f"{model_path}"
            if cache_key not in self._model_cache:
                print(f"[音频转文本] 加载 Whisper 模型: {model_path}")
                try:
                    self._model_cache[cache_key] = WhisperModel(
                        model_path, device="cpu", compute_type="int8", download_root=models_dir
                    )
                except Exception as e:
                    error_msg = str(e)
                    if "internet" in error_msg.lower() or "hub" in error_msg.lower() or "connection" in error_msg.lower() or "ssl" in error_msg.lower():
                        return ModuleResult(
                            success=False,
                            error=f"模型下载失败，请检查网络连接。\n\n手动下载方法：\n1. 访问 https://hf-mirror.com/Systran/faster-whisper-{model_size}/tree/main\n2. 下载所有文件到目录: {local_model_path}"
                        )
                    raise
            
            model = self._model_cache[cache_key]
            
            print(f"[音频转文本] 开始识别: {input_path}")
            
            segments, info = model.transcribe(
                input_path, 
                language=language if language != 'auto' else None,
                beam_size=5
            )
            
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            text = ''.join(text_parts)
            
            if not text:
                return ModuleResult(success=False, error="无法识别音频内容")
            
            if result_variable:
                context.set_variable(result_variable, text)
            
            detected_lang = info.language if hasattr(info, 'language') else language
            
            return ModuleResult(
                success=True,
                message=f"音频转文本完成，识别到 {len(text)} 个字符，语言: {detected_lang}",
                data={'text': text, 'length': len(text), 'language': detected_lang}
            )
                    
        except Exception as e:
            return ModuleResult(success=False, error=f"音频转文本失败: {str(e)}")
