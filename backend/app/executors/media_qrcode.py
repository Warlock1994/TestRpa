"""媒体处理模块 - 二维码生成和解码"""
import os
import time
import tempfile

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int


@register_executor
class QRGenerateExecutor(ModuleExecutor):
    """二维码生成器模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "qr_generate"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        content = context.resolve_value(config.get('content', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        size = to_int(config.get('size', 300), 300, context)
        error_correction = config.get('errorCorrection', 'M')
        result_variable = config.get('resultVariable', 'qr_image')
        
        if not content:
            return ModuleResult(success=False, error="二维码内容不能为空")
        
        try:
            import qrcode
            from PIL import Image
            
            error_levels = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }
            error_level = error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
            
            qr = qrcode.QRCode(
                version=1, error_correction=error_level, box_size=10, border=4,
            )
            qr.add_data(content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            filename = f"qrcode_{int(time.time())}.png"
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
            else:
                output_path = os.path.join(tempfile.gettempdir(), filename)
            
            img.save(output_path)
            
            if result_variable:
                context.set_variable(result_variable, output_path)
            
            return ModuleResult(
                success=True,
                message=f"二维码生成完成: {output_path}",
                data={'output_path': output_path, 'content': content[:50] + '...' if len(content) > 50 else content}
            )
        except ImportError:
            return ModuleResult(success=False, error="请安装 qrcode: pip install qrcode[pil]")
        except Exception as e:
            return ModuleResult(success=False, error=f"二维码生成失败: {str(e)}")


@register_executor
class QRDecodeExecutor(ModuleExecutor):
    """二维码解码器模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "qr_decode"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get('inputPath', ''))
        result_variable = config.get('resultVariable', 'qr_content')
        
        if not input_path:
            return ModuleResult(success=False, error="输入图片路径不能为空")
        
        if not os.path.exists(input_path):
            return ModuleResult(success=False, error=f"输入图片不存在: {input_path}")
        
        try:
            from pyzbar import pyzbar
            from PIL import Image
            
            img = Image.open(input_path)
            decoded_objects = pyzbar.decode(img)
            
            if not decoded_objects:
                return ModuleResult(success=False, error="未在图片中检测到二维码")
            
            qr_data = decoded_objects[0].data.decode('utf-8')
            qr_type = decoded_objects[0].type
            
            if result_variable:
                context.set_variable(result_variable, qr_data)
            
            return ModuleResult(
                success=True,
                message=f"二维码解码成功，类型: {qr_type}",
                data={'content': qr_data, 'type': qr_type, 'count': len(decoded_objects)}
            )
        except ImportError:
            return ModuleResult(success=False, error="请安装 pyzbar: pip install pyzbar")
        except Exception as e:
            return ModuleResult(success=False, error=f"二维码解码失败: {str(e)}")
