"""基础模块执行器 - 媒体播放相关"""
import asyncio

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float


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
            
            return ModuleResult(success=True, message=f"已播放 {beep_count} 次提示音", data={'count': beep_count})
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
        duration = to_int(config.get('duration', 5), 5, context)
        
        if not message:
            return ModuleResult(success=False, error="通知消息不能为空")
        
        try:
            loop = asyncio.get_running_loop()
            
            def show_notification():
                try:
                    from plyer import notification
                    notification.notify(title=title, message=message, timeout=duration, app_name='WebRPA')
                    return True, None
                except Exception as e:
                    return False, str(e)
            
            success, error = await loop.run_in_executor(None, show_notification)
            
            if not success:
                return ModuleResult(success=False, error=f"显示通知失败: {error}")
            
            return ModuleResult(success=True, message=f"已显示系统通知: {title}",
                              data={'title': title, 'message': message})
            
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
        if isinstance(wait_for_end_raw, str):
            wait_for_end_raw = context.resolve_value(wait_for_end_raw)
        wait_for_end = wait_for_end_raw in [True, 'true', 'True', '1', 1]

        if not audio_url:
            return ModuleResult(success=False, error="音频URL不能为空")

        try:
            url = audio_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_play_music_sync(audio_url=url, wait_for_end=wait_for_end, timeout=600)
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"播放音乐失败: {error_msg}")

            source_display = audio_url[:50] + "..." if len(audio_url) > 50 else audio_url
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
        if isinstance(wait_for_end_raw, str):
            wait_for_end_raw = context.resolve_value(wait_for_end_raw)
        wait_for_end = wait_for_end_raw in [True, 'true', 'True', '1', 1]

        if not video_url:
            return ModuleResult(success=False, error="视频URL不能为空")

        try:
            url = video_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_play_video_sync(video_url=url, wait_for_end=wait_for_end, timeout=3600)
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"播放视频失败: {error_msg}")

            source_display = video_url[:50] + "..." if len(video_url) > 50 else video_url
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
        if isinstance(auto_close_raw, str):
            auto_close_raw = context.resolve_value(auto_close_raw)
        auto_close = auto_close_raw in [True, 'true', 'True', '1', 1]
        display_time = to_int(config.get("displayTime", 5000), 5000, context)

        if not image_url:
            return ModuleResult(success=False, error="图片URL不能为空")

        try:
            url = image_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: request_view_image_sync(image_url=url, auto_close=auto_close, display_time=display_time, timeout=300)
            )

            if not result.get("success"):
                error_msg = result.get("error", "未知错误")
                return ModuleResult(success=False, error=f"查看图片失败: {error_msg}")

            source_display = image_url[:50] + "..." if len(image_url) > 50 else image_url
            return ModuleResult(success=True, message=f"图片查看完成: {source_display}")

        except Exception as e:
            return ModuleResult(success=False, error=f"查看图片失败: {str(e)}")


@register_executor
class TextToSpeechExecutor(ModuleExecutor):
    """文本朗读模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "text_to_speech"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.main import request_tts_sync
        
        text = context.resolve_value(config.get('text', ''))
        lang = context.resolve_value(config.get('lang', 'zh-CN'))
        rate = to_float(config.get('rate', 1), 1.0, context)
        pitch = to_float(config.get('pitch', 1), 1.0, context)
        volume = to_float(config.get('volume', 1), 1.0, context)
        
        if not text:
            return ModuleResult(success=False, error="朗读文本不能为空")
        
        try:
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None,
                lambda: request_tts_sync(text=text, lang=lang, rate=rate, pitch=pitch, volume=volume, timeout=60)
            )
            
            if success:
                return ModuleResult(success=True, message=f"已朗读文本: {text[:50]}{'...' if len(text) > 50 else ''}",
                                  data={'text': text, 'lang': lang})
            else:
                return ModuleResult(success=False, error="语音合成超时或失败")
        except Exception as e:
            return ModuleResult(success=False, error=f"文本朗读失败: {str(e)}")
