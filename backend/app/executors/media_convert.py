"""媒体处理模块 - 格式转换和压缩"""
import asyncio
import os
from pathlib import Path

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float
from .media_utils import get_media_duration, run_ffmpeg_with_progress, run_ffmpeg


@register_executor
class FormatConvertExecutor(ModuleExecutor):
    """格式转换模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "format_convert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_format = context.resolve_value(config.get('outputFormat', 'mp4'))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'converted_path')
        
        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")
        
        try:
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_converted.{output_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path]
            
            if output_format == 'gif':
                args.extend(['-vf', 'fps=10,scale=480:-1:flags=lanczos'])
            elif output_format in ['mp3', 'aac', 'ogg', 'flac', 'wav', 'm4a']:
                args.extend(['-vn'])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始格式转换，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始格式转换...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=3600, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"格式转换失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"格式转换完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="格式转换已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"格式转换失败: {str(e)}")


@register_executor
class CompressImageExecutor(ModuleExecutor):
    """图片压缩模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "compress_image"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        quality = to_int(config.get('quality', 80), 80, context)
        max_width = config.get('maxWidth', '')
        max_height = config.get('maxHeight', '')
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'compressed_image')
        
        if not input_path:
            return ModuleResult(success=False, error="输入图片路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入图片不存在: {input_path}")
        
        try:
            if max_width:
                max_width = to_int(max_width, 0, context)
            if max_height:
                max_height = to_int(max_height, 0, context)
            
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_compressed{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            args = ['-i', input_path]
            
            scale_filter = []
            if max_width and max_height:
                scale_filter.append(f"scale='min({max_width},iw)':min'({max_height},ih)':force_original_aspect_ratio=decrease")
            elif max_width:
                scale_filter.append(f"scale='min({max_width},iw)':-1")
            elif max_height:
                scale_filter.append(f"scale=-1:'min({max_height},ih)'")
            
            if scale_filter:
                args.extend(['-vf', scale_filter[0]])
            
            ext = os.path.splitext(output_path)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                args.extend(['-q:v', str(int((100 - quality) / 100 * 31))])
            elif ext == '.png':
                args.extend(['-compression_level', str(int((100 - quality) / 10))])
            elif ext == '.webp':
                args.extend(['-quality', str(quality)])
            
            args.append(output_path)
            
            await context.send_progress(f"🖼️ 开始压缩图片...")
            
            loop = asyncio.get_running_loop()
            success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args))
            
            if not success:
                return ModuleResult(success=False, error=f"图片压缩失败: {message}")
            
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            ratio = (1 - compressed_size / original_size) * 100
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"图片压缩完成，压缩率: {ratio:.1f}%",
                              data={'output_path': output_path, 'original_size': original_size, 'compressed_size': compressed_size})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="图片压缩已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"图片压缩失败: {str(e)}")


@register_executor
class CompressVideoExecutor(ModuleExecutor):
    """视频压缩模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "compress_video"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        preset = context.resolve_value(config.get('preset', 'medium'))
        crf = to_int(config.get('crf', 23), 23, context)
        resolution = context.resolve_value(config.get('resolution', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'compressed_video')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_compressed{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            duration = get_media_duration(input_path)
            original_size = os.path.getsize(input_path)
            
            args = ['-i', input_path]
            args.extend(['-c:v', 'libx264'])
            args.extend(['-preset', preset])
            args.extend(['-crf', str(crf)])
            args.extend(['-c:a', 'aac'])
            args.extend(['-b:a', '128k'])
            
            if resolution:
                args.extend(['-s', resolution])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始压缩视频，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始压缩视频...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=7200, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"视频压缩失败: {message}")
            
            compressed_size = os.path.getsize(output_path)
            ratio = (1 - compressed_size / original_size) * 100
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"视频压缩完成，压缩率: {ratio:.1f}%",
                              data={'output_path': output_path, 'original_size': original_size, 'compressed_size': compressed_size})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="视频压缩已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"视频压缩失败: {str(e)}")


@register_executor
class ExtractAudioExecutor(ModuleExecutor):
    """提取音频模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "extract_audio"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        audio_format = context.resolve_value(config.get('audioFormat', 'mp3'))
        audio_bitrate = context.resolve_value(config.get('audioBitrate', '192k'))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'extracted_audio')
        
        if not input_path:
            return ModuleResult(success=False, error="输入视频路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入视频不存在: {input_path}")
        
        try:
            if not output_path:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.{audio_format}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path)
            
            args = ['-i', input_path]
            args.extend(['-vn'])
            args.extend(['-b:a', audio_bitrate])
            
            if audio_format == 'mp3':
                args.extend(['-c:a', 'libmp3lame'])
            elif audio_format == 'aac':
                args.extend(['-c:a', 'aac'])
            elif audio_format == 'flac':
                args.extend(['-c:a', 'flac'])
            elif audio_format == 'ogg':
                args.extend(['-c:a', 'libvorbis'])
            
            args.append(output_path)
            
            if duration:
                await context.send_progress(f"🎬 开始提取音频，预计时长 {duration:.0f} 秒...")
            else:
                await context.send_progress(f"🎬 开始提取音频...")
            
            success, message = await run_ffmpeg_with_progress(
                args, timeout=3600, total_duration=duration, context=context
            )
            
            if not success:
                return ModuleResult(success=False, error=f"提取音频失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"音频提取完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="提取音频已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"提取音频失败: {str(e)}")
