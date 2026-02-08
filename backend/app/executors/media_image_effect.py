"""媒体处理模块 - 图片效果（去色、圆角）"""
import os

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int


@register_executor
class ImageGrayscaleExecutor(ModuleExecutor):
    """图片去色模块执行器 - 将彩色图片转换为灰度图"""
    
    @property
    def module_type(self) -> str:
        return "image_grayscale"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'grayscale_image')
        
        if not input_path:
            return ModuleResult(success=False, error="输入图片路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入图片不存在: {input_path}")
        
        try:
            from PIL import Image
            
            img = Image.open(input_path)
            grayscale_img = img.convert('L')
            
            if not output_path:
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_grayscale{ext}"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            grayscale_img.save(output_path)
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"图片去色完成: {output_path}",
                              data={'output_path': output_path})
        except Exception as e:
            return ModuleResult(success=False, error=f"图片去色失败: {str(e)}")


@register_executor
class ImageRoundCornersExecutor(ModuleExecutor):
    """图片圆角化模块执行器 - 为图片添加圆角效果"""
    
    @property
    def module_type(self) -> str:
        return "image_round_corners"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        radius = to_int(config.get('radius', 20), 20, context)
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', 'rounded_image')
        
        if not input_path:
            return ModuleResult(success=False, error="输入图片路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入图片不存在: {input_path}")
        
        try:
            from PIL import Image, ImageDraw
            
            img = Image.open(input_path).convert('RGBA')
            width, height = img.size
            
            mask = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), (width, height)], radius=radius, fill=255)
            
            output = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            output.paste(img, mask=mask)
            
            if not output_path:
                base, _ = os.path.splitext(input_path)
                output_path = f"{base}_rounded.png"
            
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            output.save(output_path, 'PNG')
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(success=True, message=f"图片圆角化完成，圆角半径: {radius}px",
                              data={'output_path': output_path, 'radius': radius})
        except Exception as e:
            return ModuleResult(success=False, error=f"图片圆角化失败: {str(e)}")
