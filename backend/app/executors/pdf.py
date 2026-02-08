"""PDF文件处理模块执行器

提供全面的PDF文件处理功能，包括：
- PDF转图片
- 图片转PDF
- PDF合并
- PDF拆分
- PDF提取文本
- PDF提取图片
- PDF加密/解密
- PDF添加水印
- PDF旋转页面
- PDF删除页面
- PDF获取信息

依赖库：
- PyMuPDF (fitz): PDF处理核心库
- Pillow: 图片处理
- reportlab: PDF生成
"""
import asyncio
import os
import time
from typing import Optional, List

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


def ensure_pdf_libs():
    """确保PDF处理库已安装"""
    try:
        import fitz  # PyMuPDF
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
        page_range = context.resolve_value(config.get('pageRange', ''))  # 如 "1-5" 或 "1,3,5"
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        # 默认输出目录为PDF所在目录
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
            
            return ModuleResult(
                success=True,
                message=f"已将PDF转换为 {len(result['images'])} 张图片",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF转图片失败: {str(e)}")
    
    def _convert(self, pdf_path: str, output_dir: str, dpi: int, image_format: str, page_range: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 解析页面范围
        pages_to_convert = self._parse_page_range(page_range, total_pages)
        
        images = []
        zoom = dpi / 72  # 72是PDF默认DPI
        matrix = fitz.Matrix(zoom, zoom)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for page_num in pages_to_convert:
            page = doc[page_num]
            pix = page.get_pixmap(matrix=matrix)
            
            output_path = os.path.join(output_dir, f"{base_name}_page_{page_num + 1}.{image_format}")
            pix.save(output_path)
            images.append(output_path)
        
        doc.close()
        
        return {
            "images": images,
            "total_pages": total_pages,
            "converted_pages": len(images),
            "output_dir": output_dir
        }
    
    def _parse_page_range(self, page_range: str, total_pages: int) -> List[int]:
        """解析页面范围字符串"""
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
        import fitz
        from PIL import Image
        
        images_input = context.resolve_value(config.get('images', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_size = config.get('pageSize', 'A4')  # A4, Letter, 或 original
        result_variable = config.get('resultVariable', '')
        
        # 处理图片输入（可以是列表或逗号分隔的字符串）
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
        
        # 验证所有图片存在
        for img_path in image_paths:
            if not os.path.exists(img_path):
                return ModuleResult(success=False, error=f"图片不存在: {img_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert, image_paths, output_path, page_size
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已将 {len(image_paths)} 张图片转换为PDF",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"图片转PDF失败: {str(e)}")
    
    def _convert(self, image_paths: List[str], output_path: str, page_size: str) -> dict:
        import fitz
        from PIL import Image
        
        # 页面尺寸（点，1英寸=72点）
        page_sizes = {
            'A4': (595, 842),
            'A3': (842, 1191),
            'Letter': (612, 792),
            'Legal': (612, 1008),
        }
        
        doc = fitz.open()
        
        for img_path in image_paths:
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            if page_size == 'original':
                # 使用图片原始尺寸
                page_width = img_width * 72 / 96  # 假设图片96 DPI
                page_height = img_height * 72 / 96
            else:
                page_width, page_height = page_sizes.get(page_size, page_sizes['A4'])
                # 如果图片是横向的，旋转页面
                if img_width > img_height and page_width < page_height:
                    page_width, page_height = page_height, page_width
            
            page = doc.new_page(width=page_width, height=page_height)
            
            # 计算图片在页面中的位置（居中并保持比例）
            scale_x = page_width / img_width
            scale_y = page_height / img_height
            scale = min(scale_x, scale_y) * 0.95  # 留5%边距
            
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
        
        return {
            "output_path": output_path,
            "page_count": len(image_paths),
            "file_size": os.path.getsize(output_path)
        }



@register_executor
class PDFMergeExecutor(ModuleExecutor):
    """PDF合并模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_merge"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdfs_input = context.resolve_value(config.get('pdfFiles', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        # 处理PDF输入
        if isinstance(pdfs_input, str):
            pdf_paths = [p.strip() for p in pdfs_input.split(',') if p.strip()]
        elif isinstance(pdfs_input, list):
            pdf_paths = pdfs_input
        else:
            return ModuleResult(success=False, error="PDF文件路径格式错误")
        
        if len(pdf_paths) < 2:
            return ModuleResult(success=False, error="至少需要2个PDF文件进行合并")
        if not output_path:
            return ModuleResult(success=False, error="输出PDF路径不能为空")
        
        # 验证所有PDF存在
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._merge, pdf_paths, output_path)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已合并 {len(pdf_paths)} 个PDF文件",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF合并失败: {str(e)}")
    
    def _merge(self, pdf_paths: List[str], output_path: str) -> dict:
        import fitz
        
        merged_doc = fitz.open()
        total_pages = 0
        
        for pdf_path in pdf_paths:
            doc = fitz.open(pdf_path)
            merged_doc.insert_pdf(doc)
            total_pages += len(doc)
            doc.close()
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        merged_doc.save(output_path)
        merged_doc.close()
        
        return {
            "output_path": output_path,
            "merged_files": len(pdf_paths),
            "total_pages": total_pages,
            "file_size": os.path.getsize(output_path)
        }


@register_executor
class PDFSplitExecutor(ModuleExecutor):
    """PDF拆分模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_split"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        split_mode = config.get('splitMode', 'single')  # single: 每页一个, range: 按范围
        page_ranges = context.resolve_value(config.get('pageRanges', ''))  # 如 "1-3,4-6,7-10"
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
                None, self._split, pdf_path, output_dir, split_mode, page_ranges
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已拆分为 {len(result['output_files'])} 个PDF文件",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF拆分失败: {str(e)}")
    
    def _split(self, pdf_path: str, output_dir: str, split_mode: str, page_ranges: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_files = []
        
        if split_mode == 'single':
            # 每页拆分为一个PDF
            for i in range(total_pages):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=i, to_page=i)
                output_path = os.path.join(output_dir, f"{base_name}_page_{i + 1}.pdf")
                new_doc.save(output_path)
                new_doc.close()
                output_files.append(output_path)
        else:
            # 按范围拆分
            ranges = self._parse_ranges(page_ranges, total_pages)
            for idx, (start, end) in enumerate(ranges):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
                output_path = os.path.join(output_dir, f"{base_name}_part_{idx + 1}.pdf")
                new_doc.save(output_path)
                new_doc.close()
                output_files.append(output_path)
        
        doc.close()
        
        return {
            "output_files": output_files,
            "total_pages": total_pages,
            "split_count": len(output_files)
        }
    
    def _parse_ranges(self, page_ranges: str, total_pages: int) -> List[tuple]:
        """解析页面范围"""
        if not page_ranges:
            return [(0, total_pages)]
        
        ranges = []
        parts = page_ranges.replace(' ', '').split(',')
        
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                start = int(start) - 1 if start else 0
                end = int(end) if end else total_pages
                ranges.append((max(0, start), min(end, total_pages)))
            else:
                page = int(part) - 1
                if 0 <= page < total_pages:
                    ranges.append((page, page + 1))
        
        return ranges



@register_executor
class PDFExtractTextExecutor(ModuleExecutor):
    """PDF提取文本模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_extract_text"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))  # 可选，保存到文件
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._extract, pdf_path, page_range, output_path
            )
            
            if result_variable:
                context.set_variable(result_variable, result['text'])
            
            return ModuleResult(
                success=True,
                message=f"已从 {result['extracted_pages']} 页中提取文本",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF提取文本失败: {str(e)}")
    
    def _extract(self, pdf_path: str, page_range: str, output_path: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 解析页面范围
        pages = self._parse_page_range(page_range, total_pages)
        
        text_parts = []
        for page_num in pages:
            page = doc[page_num]
            text = page.get_text()
            text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
        
        doc.close()
        
        full_text = "\n\n".join(text_parts)
        
        # 如果指定了输出路径，保存到文件
        if output_path:
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return {
            "text": full_text,
            "total_pages": total_pages,
            "extracted_pages": len(pages),
            "char_count": len(full_text),
            "output_path": output_path if output_path else None
        }
    
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
class PDFExtractImagesExecutor(ModuleExecutor):
    """PDF提取图片模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_extract_images"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        min_size = int(config.get('minSize', 100))  # 最小图片尺寸（像素）
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
                None, self._extract, pdf_path, output_dir, min_size
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已提取 {len(result['images'])} 张图片",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF提取图片失败: {str(e)}")
    
    def _extract(self, pdf_path: str, output_dir: str, min_size: int) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        images = []
        img_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)
                    
                    # 过滤小图片
                    if width >= min_size and height >= min_size:
                        img_count += 1
                        output_path = os.path.join(
                            output_dir, 
                            f"{base_name}_page{page_num + 1}_img{img_count}.{image_ext}"
                        )
                        
                        with open(output_path, "wb") as f:
                            f.write(image_bytes)
                        
                        images.append({
                            "path": output_path,
                            "page": page_num + 1,
                            "width": width,
                            "height": height,
                            "format": image_ext
                        })
        
        doc.close()
        
        return {
            "images": images,
            "image_count": len(images),
            "output_dir": output_dir
        }



@register_executor
class PDFEncryptExecutor(ModuleExecutor):
    """PDF加密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_encrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        user_password = context.resolve_value(config.get('userPassword', ''))  # 打开密码
        owner_password = context.resolve_value(config.get('ownerPassword', ''))  # 权限密码
        permissions = config.get('permissions', {})  # 权限设置
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not user_password and not owner_password:
            return ModuleResult(success=False, error="至少需要设置一个密码")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_encrypted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._encrypt, pdf_path, output_path, user_password, owner_password, permissions
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message="PDF加密成功",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF加密失败: {str(e)}")
    
    def _encrypt(self, pdf_path: str, output_path: str, user_password: str, 
                 owner_password: str, permissions: dict) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        
        # 构建权限标志
        perm = fitz.PDF_PERM_ACCESSIBILITY  # 始终允许辅助功能
        
        if permissions.get('print', True):
            perm |= fitz.PDF_PERM_PRINT | fitz.PDF_PERM_PRINT_HQ
        if permissions.get('copy', True):
            perm |= fitz.PDF_PERM_COPY
        if permissions.get('modify', False):
            perm |= fitz.PDF_PERM_MODIFY
        if permissions.get('annotate', True):
            perm |= fitz.PDF_PERM_ANNOTATE
        if permissions.get('form', True):
            perm |= fitz.PDF_PERM_FORM
        
        # 加密保存
        encrypt_meth = fitz.PDF_ENCRYPT_AES_256  # 使用AES-256加密
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(
            output_path,
            encryption=encrypt_meth,
            user_pw=user_password if user_password else None,
            owner_pw=owner_password if owner_password else user_password,
            permissions=perm
        )
        doc.close()
        
        return {
            "output_path": output_path,
            "has_user_password": bool(user_password),
            "has_owner_password": bool(owner_password),
            "encryption": "AES-256"
        }


@register_executor
class PDFDecryptExecutor(ModuleExecutor):
    """PDF解密模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_decrypt"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        password = context.resolve_value(config.get('password', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_decrypted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._decrypt, pdf_path, password, output_path
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message="PDF解密成功",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF解密失败: {str(e)}")
    
    def _decrypt(self, pdf_path: str, password: str, output_path: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        
        if doc.is_encrypted:
            if not doc.authenticate(password):
                doc.close()
                raise Exception("密码错误")
        
        # 保存为无加密的PDF
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        doc.close()
        
        return {
            "output_path": output_path,
            "page_count": doc.page_count if hasattr(doc, 'page_count') else 0
        }



@register_executor
class PDFAddWatermarkExecutor(ModuleExecutor):
    """PDF添加水印模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_add_watermark"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        watermark_type = config.get('watermarkType', 'text')  # text 或 image
        watermark_text = context.resolve_value(config.get('watermarkText', ''))
        watermark_image = context.resolve_value(config.get('watermarkImage', ''))
        opacity = float(config.get('opacity', 0.3))
        position = config.get('position', 'center')  # center, diagonal, tile
        font_size = int(config.get('fontSize', 48))
        color = config.get('color', '#888888')
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if watermark_type == 'text' and not watermark_text:
            return ModuleResult(success=False, error="水印文字不能为空")
        if watermark_type == 'image' and not watermark_image:
            return ModuleResult(success=False, error="水印图片路径不能为空")
        if watermark_type == 'image' and not os.path.exists(watermark_image):
            return ModuleResult(success=False, error=f"水印图片不存在: {watermark_image}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_watermarked{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._add_watermark, pdf_path, output_path, watermark_type,
                watermark_text, watermark_image, opacity, position, font_size, color
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message="PDF水印添加成功",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF添加水印失败: {str(e)}")
    
    def _add_watermark(self, pdf_path: str, output_path: str, watermark_type: str,
                       watermark_text: str, watermark_image: str, opacity: float,
                       position: str, font_size: int, color: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        
        # 解析颜色
        color_rgb = self._hex_to_rgb(color)
        
        for page in doc:
            rect = page.rect
            
            if watermark_type == 'text':
                if position == 'diagonal':
                    # 对角线水印
                    text_length = fitz.get_text_length(watermark_text, fontsize=font_size)
                    # 计算旋转角度
                    import math
                    angle = math.degrees(math.atan2(rect.height, rect.width))
                    
                    # 在页面中心添加旋转文字
                    center = fitz.Point(rect.width / 2, rect.height / 2)
                    page.insert_text(
                        center,
                        watermark_text,
                        fontsize=font_size,
                        color=color_rgb,
                        rotate=angle,
                        overlay=True
                    )
                elif position == 'tile':
                    # 平铺水印
                    y = 50
                    while y < rect.height:
                        x = 50
                        while x < rect.width:
                            page.insert_text(
                                fitz.Point(x, y),
                                watermark_text,
                                fontsize=font_size,
                                color=color_rgb,
                                overlay=True
                            )
                            x += font_size * len(watermark_text) + 100
                        y += font_size + 100
                else:
                    # 居中水印
                    text_length = fitz.get_text_length(watermark_text, fontsize=font_size)
                    x = (rect.width - text_length) / 2
                    y = rect.height / 2
                    page.insert_text(
                        fitz.Point(x, y),
                        watermark_text,
                        fontsize=font_size,
                        color=color_rgb,
                        overlay=True
                    )
            else:
                # 图片水印
                img_rect = fitz.Rect(0, 0, 200, 200)  # 默认水印大小
                
                if position == 'center':
                    # 居中
                    x = (rect.width - img_rect.width) / 2
                    y = (rect.height - img_rect.height) / 2
                    img_rect = fitz.Rect(x, y, x + img_rect.width, y + img_rect.height)
                elif position == 'tile':
                    # 平铺 - 添加多个水印
                    y = 50
                    while y < rect.height:
                        x = 50
                        while x < rect.width:
                            tile_rect = fitz.Rect(x, y, x + 150, y + 150)
                            page.insert_image(tile_rect, filename=watermark_image, overlay=True)
                            x += 200
                        y += 200
                    continue
                
                page.insert_image(img_rect, filename=watermark_image, overlay=True)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        doc.close()
        
        return {
            "output_path": output_path,
            "watermark_type": watermark_type,
            "position": position
        }
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGB元组（0-1范围）"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b)



@register_executor
class PDFRotateExecutor(ModuleExecutor):
    """PDF旋转页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_rotate"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        rotation = int(config.get('rotation', 90))  # 90, 180, 270
        page_range = context.resolve_value(config.get('pageRange', ''))  # 空表示所有页
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if rotation not in [90, 180, 270, -90, -180, -270]:
            return ModuleResult(success=False, error="旋转角度必须是90、180或270度")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_rotated{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._rotate, pdf_path, output_path, rotation, page_range
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已旋转 {result['rotated_pages']} 页",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF旋转失败: {str(e)}")
    
    def _rotate(self, pdf_path: str, output_path: str, rotation: int, page_range: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 解析页面范围
        pages = self._parse_page_range(page_range, total_pages)
        
        for page_num in pages:
            page = doc[page_num]
            page.set_rotation(page.rotation + rotation)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        doc.close()
        
        return {
            "output_path": output_path,
            "rotation": rotation,
            "rotated_pages": len(pages),
            "total_pages": total_pages
        }
    
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
class PDFDeletePagesExecutor(ModuleExecutor):
    """PDF删除页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_delete_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))  # 要删除的页面
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not page_range:
            return ModuleResult(success=False, error="请指定要删除的页面")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_modified{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._delete, pdf_path, output_path, page_range
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已删除 {result['deleted_pages']} 页",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF删除页面失败: {str(e)}")
    
    def _delete(self, pdf_path: str, output_path: str, page_range: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 解析要删除的页面
        pages_to_delete = self._parse_page_range(page_range, total_pages)
        
        # 从后往前删除，避免索引变化
        for page_num in sorted(pages_to_delete, reverse=True):
            doc.delete_page(page_num)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        
        new_page_count = len(doc)
        doc.close()
        
        return {
            "output_path": output_path,
            "original_pages": total_pages,
            "deleted_pages": len(pages_to_delete),
            "remaining_pages": new_page_count
        }
    
    def _parse_page_range(self, page_range: str, total_pages: int) -> List[int]:
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
class PDFGetInfoExecutor(ModuleExecutor):
    """PDF获取信息模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_get_info"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        password = context.resolve_value(config.get('password', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_info, pdf_path, password)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"PDF共 {result['page_count']} 页",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"获取PDF信息失败: {str(e)}")
    
    def _get_info(self, pdf_path: str, password: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        
        # 如果加密，尝试解密
        if doc.is_encrypted:
            if password:
                if not doc.authenticate(password):
                    doc.close()
                    raise Exception("密码错误")
            else:
                doc.close()
                raise Exception("PDF已加密，请提供密码")
        
        # 获取元数据
        metadata = doc.metadata or {}
        
        # 获取页面信息
        pages_info = []
        for i, page in enumerate(doc):
            rect = page.rect
            pages_info.append({
                "page_number": i + 1,
                "width": rect.width,
                "height": rect.height,
                "rotation": page.rotation
            })
        
        # 获取文件大小
        file_size = os.path.getsize(pdf_path)
        
        result = {
            "file_path": pdf_path,
            "file_size": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "page_count": len(doc),
            "is_encrypted": doc.is_encrypted,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
            },
            "pages": pages_info
        }
        
        doc.close()
        return result


@register_executor
class PDFCompressExecutor(ModuleExecutor):
    """PDF压缩模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_compress"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        image_quality = int(config.get('imageQuality', 80))  # 图片质量 1-100
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_compressed{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._compress, pdf_path, output_path, image_quality
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"PDF压缩完成，压缩率 {result['compression_ratio']}%",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF压缩失败: {str(e)}")
    
    def _compress(self, pdf_path: str, output_path: str, image_quality: int) -> dict:
        import fitz
        
        original_size = os.path.getsize(pdf_path)
        
        doc = fitz.open(pdf_path)
        
        # 压缩选项
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(
            output_path,
            garbage=4,  # 最大垃圾回收
            deflate=True,  # 压缩流
            clean=True,  # 清理冗余
            linear=True,  # 线性化（优化网络加载）
        )
        doc.close()
        
        new_size = os.path.getsize(output_path)
        compression_ratio = round((1 - new_size / original_size) * 100, 1)
        
        return {
            "output_path": output_path,
            "original_size": original_size,
            "compressed_size": new_size,
            "original_size_mb": round(original_size / 1024 / 1024, 2),
            "compressed_size_mb": round(new_size / 1024 / 1024, 2),
            "compression_ratio": compression_ratio
        }



@register_executor
class PDFInsertPagesExecutor(ModuleExecutor):
    """PDF插入页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_insert_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        insert_pdf = context.resolve_value(config.get('insertPdf', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        insert_position = int(config.get('insertPosition', 0))  # 0表示开头，-1表示末尾
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not insert_pdf:
            return ModuleResult(success=False, error="要插入的PDF路径不能为空")
        if not os.path.exists(insert_pdf):
            return ModuleResult(success=False, error=f"要插入的PDF不存在: {insert_pdf}")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_inserted{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._insert, pdf_path, insert_pdf, output_path, insert_position
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已插入 {result['inserted_pages']} 页",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF插入页面失败: {str(e)}")
    
    def _insert(self, pdf_path: str, insert_pdf: str, output_path: str, insert_position: int) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        insert_doc = fitz.open(insert_pdf)
        
        original_pages = len(doc)
        insert_pages = len(insert_doc)
        
        # 确定插入位置
        if insert_position == -1 or insert_position >= original_pages:
            position = original_pages
        else:
            position = max(0, insert_position)
        
        # 插入页面
        doc.insert_pdf(insert_doc, start_at=position)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        doc.save(output_path)
        
        total_pages = len(doc)
        doc.close()
        insert_doc.close()
        
        return {
            "output_path": output_path,
            "original_pages": original_pages,
            "inserted_pages": insert_pages,
            "total_pages": total_pages,
            "insert_position": position
        }


@register_executor
class PDFReorderPagesExecutor(ModuleExecutor):
    """PDF重排页面模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_reorder_pages"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        ensure_pdf_libs()
        import fitz
        
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_path = context.resolve_value(config.get('outputPath', ''))
        page_order = context.resolve_value(config.get('pageOrder', ''))  # 如 "3,1,2,5,4"
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        if not page_order:
            return ModuleResult(success=False, error="请指定页面顺序")
        
        if not output_path:
            base, ext = os.path.splitext(pdf_path)
            output_path = f"{base}_reordered{ext}"
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._reorder, pdf_path, output_path, page_order
            )
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message="PDF页面重排完成",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF重排页面失败: {str(e)}")
    
    def _reorder(self, pdf_path: str, output_path: str, page_order: str) -> dict:
        import fitz
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # 解析页面顺序
        if isinstance(page_order, str):
            order = [int(p.strip()) - 1 for p in page_order.split(',') if p.strip()]
        else:
            order = [int(p) - 1 for p in page_order]
        
        # 验证页面索引
        for idx in order:
            if idx < 0 or idx >= total_pages:
                raise Exception(f"页面索引 {idx + 1} 超出范围 (1-{total_pages})")
        
        # 创建新文档并按顺序添加页面
        new_doc = fitz.open()
        for idx in order:
            new_doc.insert_pdf(doc, from_page=idx, to_page=idx)
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        
        return {
            "output_path": output_path,
            "original_pages": total_pages,
            "new_page_count": len(order),
            "page_order": [i + 1 for i in order]
        }


@register_executor
class PDFToWordExecutor(ModuleExecutor):
    """PDF转Word模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "pdf_to_word"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        pdf_path = context.resolve_value(config.get('pdfPath', ''))
        output_dir = context.resolve_value(config.get('outputDir', ''))
        page_range = context.resolve_value(config.get('pageRange', ''))
        result_variable = config.get('resultVariable', '')
        
        if not pdf_path:
            return ModuleResult(success=False, error="PDF文件路径不能为空")
        if not os.path.exists(pdf_path):
            return ModuleResult(success=False, error=f"PDF文件不存在: {pdf_path}")
        
        # 确定输出路径
        if not output_dir:
            output_dir = os.path.dirname(pdf_path)
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.docx")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._convert, pdf_path, output_path, page_range
            )
            
            if result_variable:
                context.set_variable(result_variable, result['output_path'])
            
            return ModuleResult(
                success=True,
                message=f"PDF转Word完成: {result['output_path']}",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"PDF转Word失败: {str(e)}")
    
    def _convert(self, pdf_path: str, output_path: str, page_range: str) -> dict:
        try:
            from pdf2docx import Converter
        except ImportError:
            raise ImportError("请安装 pdf2docx: pip install pdf2docx")
        
        cv = Converter(pdf_path)
        
        # 解析页面范围
        pages = None
        if page_range:
            pages = parse_page_range(page_range)
        
        if pages:
            cv.convert(output_path, pages=pages)
        else:
            cv.convert(output_path)
        
        cv.close()
        
        return {
            "output_path": output_path,
            "pages_converted": len(pages) if pages else "all"
        }
