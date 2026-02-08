"""媒体处理模块 - 水印处理"""
import asyncio
import os

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float
from .media_utils import get_media_duration, run_ffmpeg_with_progress, run_ffmpeg


@register_executor
class AddWatermarkExecutor(ModuleExecutor):
    """添加水印模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "add_watermark"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        media_type = context.resolve_value(config.get('mediaType', 'video'))
        watermark_type = context.resolve_value(config.get('watermarkType', 'image'))
        position = context.resolve_value(config.get('position', 'bottomright'))
        opacity = to_float(config.get('opacity', 0.8), 0.8, context)
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'watermarked_file')
        
        if not input_path:
            return ModuleResult(success=False, error="输入文件路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入文件不存在: {input_path}")
        
        try:
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_watermarked{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            duration = get_media_duration(input_path) if media_type == 'video' else None
            
            position_map = {
                'topleft': '10:10',
                'topright': 'W-w-10:10',
                'bottomleft': '10:H-h-10',
                'bottomright': 'W-w-10:H-h-10',
                'center': '(W-w)/2:(H-h)/2',
            }
            pos = position_map.get(position, 'W-w-10:H-h-10')
            
            args = ['-i', input_path]

            if watermark_type == 'image':
                watermark_image = context.resolve_value(config.get('watermarkImage', ''))
                if not watermark_image or not os.path.exists(watermark_image):
                    return ModuleResult(success=False, error="水印图片不存在")
                
                args.extend(['-i', watermark_image])
                filter_str = f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[wm];[0:v][wm]overlay={pos}"
                args.extend(['-filter_complex', filter_str])
                
            else:  # text watermark
                watermark_text = context.resolve_value(config.get('watermarkText', ''))
                font_size = to_int(config.get('fontSize', 24), 24, context)
                font_color = context.resolve_value(config.get('fontColor', 'white'))
                
                if not watermark_text:
                    return ModuleResult(success=False, error="水印文字不能为空")
                
                text_pos_map = {
                    'topleft': 'x=10:y=10',
                    'topright': 'x=w-tw-10:y=10',
                    'bottomleft': 'x=10:y=h-th-10',
                    'bottomright': 'x=w-tw-10:y=h-th-10',
                    'center': 'x=(w-tw)/2:y=(h-th)/2',
                }
                text_pos = text_pos_map.get(position, 'x=w-tw-10:y=h-th-10')
                
                escaped_text = watermark_text.replace("'", "\\'").replace(":", "\\:")
                filter_str = f"drawtext=text='{escaped_text}':fontsize={font_size}:fontcolor={font_color}@{opacity}:{text_pos}"
                args.extend(['-vf', filter_str])
            
            if media_type == 'video':
                args.extend(['-c:a', 'copy'])
            
            args.append(output_path)
            
            if media_type == 'video' and duration:
                await context.send_progress(f"🎬 开始添加水印，预计时长 {duration:.0f} 秒...")
                
                success, message = await run_ffmpeg_with_progress(
                    args, timeout=7200, total_duration=duration, context=context
                )
            else:
                await context.send_progress(f"🎬 开始添加水印...")
                loop = asyncio.get_running_loop()
                success, message = await loop.run_in_executor(None, lambda: run_ffmpeg(args, timeout=3600))
            
            if not success:
                return ModuleResult(success=False, error=f"添加水印失败: {message}")
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"水印添加完成: {output_path}",
                              data={'output_path': output_path})
        except asyncio.CancelledError:
            return ModuleResult(success=False, error="添加水印已取消")
        except Exception as e:
            return ModuleResult(success=False, error=f"添加水印失败: {str(e)}")
