"""PDF文件处理模块 - 转换相关执行器

包含：
- PDF转图片
- 图片转PDF
- PDF转Word
- Word转PDF
"""
import asyncio
import os
from typing import List

from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


def ensure_pdf_libs():
    """确保PDF处理库已安装"""
    try:
        import fitz
        return True
    except ImportError:
        raise ImportError("请安装 PyMuPDF: pip install PyMuPDF")


@register_executor
class PDFToImagesExecutor(ModuleExecutor):
    """PDF转图片模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_to_images"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        dpi = int(config.get('dpi', 150))
        image_format = config.get('imageFormat', 'png')
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert, pdf_path, output_dir, dpi, image_format, page_range
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已将PDF转换为 {len(result['images'])} 张图片", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF转图片失败: {str(e)}")
    
    def _convert(self, pdf_path: str, output_dir: str, dpi: int, image_format: str, page_range: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_convert = self._parse_page_range(page_range, total_pages)
        
        images = []
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for page_num in pages_to_convert:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            output_path = os.path.join(output_dir, f"{base_name}_page_{page_num + 1}.{image_format}")
            pix.save(output_path)
            images.append(output_path)
        
        doc.close()
        return {"images": images, "total_pages": total_pages, "converted_pages": len(images), "output_dir": output_dir}
    
    def _parse_page_range(self, page_range: str, total_pages: int) -> List[int]:
        if not page_range:
            return list(range(total_pages))
        
        pages = set()
        parts = page_range.replace(' ', '').split(',')
        
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                start = int(start) - 1 if start else 0
                end = int(end) if end else total_pages
                pages.update(range(max(0, start), min(end, total_pages)))
            else:
                page = int(part) - 1
                if 0 <= page < total_pages:
                    pages.add(page)
        
        return sorted(pages)


@register_executor
class ImagesToPDFExecutor(ModuleExecutor):
    """图片转PDF模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "images_to_pdf"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        
        images_input = context.resolve_value(config.get('images', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_size = config.get('pageSize', 'A4')
        result_variable = config.get('resultVariable', '')
        
        if isinstance(images_input, str):
            image_paths = [p.strip() for p in images_input.split(',') if p.strip()]
        elif isinstance(images_input, list):
            image_paths = images_input
        else:
            return ModuleResult(success=False, error="图片路径格式错误")
        
        if not image_paths:
            return ModuleResult(success=False, error="图片列表不能为空")
        if not output_path:
            return ModuleResult(success=False, error="输出PDF路径不能为空")
        
        for img_path in image_paths:
            if not os.path.exists(img_path):
                return ModuleResult(success=False, error=f"图片不存在: {img_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert, image_paths, output_path, page_size)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"已将 {len(image_paths)} 张图片转换为PDF", data=result)
        except Exception as e:
            return ModuleResult(success=False, error=f"图片转PDF失败: {str(e)}")
    
    def _convert(self, image_paths: List[str], output_path: str, page_size: str) -> dict:
        import fitz
        from PIL import Image
        
        page_sizes = {'A4': (595, 842), 'A3': (842, 1191), 'Letter': (612, 792), 'Legal': (612, 1008)}
        doc = fitz.open()
        
        for img_path in image_paths:
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            if page_size == 'original':
                page_width = img_width * 72 / 96
                page_height = img_height * 72 / 96
            else:
                page_width, page_height = page_sizes.get(page_size, page_sizes['A4'])
                if img_width > img_height and page_width < page_height:
                    page_width, page_height = page_height, page_width
            
            page = doc.new_page(width=page_width, height=page_height)
            
            scale_x = page_width / img_width
            scale_y = page_height / img_height
            scale = min(scale_x, scale_y) * 0.95
            
            new_width = img_width * scale
            new_height = img_height * scale
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2
            
            rect = fitz.Rect(x, y, x + new_width, y + new_height)
            page.insert_image(rect, filename=img_path)
            img.close()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        doc.close()
        
        return {"output_path": output_path, "page_count": len(image_paths), "file_size": os.path.getsize(output_path)}


@register_executor
class PDFToWordExecutor(ModuleExecutor):
    """PDF转Word模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_to_word"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_path:
            output_path = os.path.splitext(pdf_path)[0] + '.docx'
        
        try:
            from pdf2docx import Converter
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert, pdf_path, output_path)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(success=True, message=f"PDF已转换为Word: {output_path}", data=result)
        except ImportError:
            return ModuleResult(success=False, error="请安装 pdf2docx: pip install pdf2docx")
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF转Word失败: {str(e)}")
    
    def _convert(self, pdf_path: str, output_path: str) -> dict:
        from pdf2docx import Converter
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()
        
        return {"output_path": output_path, "file_size": os.path.getsize(output_path)}
