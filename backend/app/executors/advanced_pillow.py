"""Pillow图像处理模块执行器 - 高级图像处理功能"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float
from pathlib import Path
import asyncio


@register_executor
class ImageResizeExecutor(ModuleExecutor):
    """图像缩放模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_resize"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        width = to_int(config.get("width", 0), 0, context)
        height = to_int(config.get("height", 0), 0, context)
        keep_aspect = config.get("keepAspect", True)  # 保持宽高比
        resample = context.resolve_value(config.get("resample", "LANCZOS"))  # 重采样算法
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")
        
        if width <= 0 and height <= 0:
            return ModuleResult(success=False, error="宽度和高度至少需要指定一个")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_resized{input_file.suffix}")
            
            # 打开图像
            img = Image.open(input_path)
            original_size = img.size
            
            # 计算新尺寸
            if keep_aspect:
                if width > 0 and height > 0:
                    # 两者都指定，按比例缩放到适合的尺寸
                    img.thumbnail((width, height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                    new_size = img.size
                elif width > 0:
                    # 只指定宽度
                    ratio = width / original_size[0]
                    new_height = int(original_size[1] * ratio)
                    img = img.resize((width, new_height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                    new_size = (width, new_height)
                else:
                    # 只指定高度
                    ratio = height / original_size[1]
                    new_width = int(original_size[0] * ratio)
                    img = img.resize((new_width, height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                    new_size = (new_width, height)
            else:
                # 不保持宽高比，强制缩放
                new_width = width if width > 0 else original_size[0]
                new_height = height if height > 0 else original_size[1]
                img = img.resize((new_width, new_height), getattr(Image.Resampling, resample, Image.Resampling.LANCZOS))
                new_size = (new_width, new_height)
            
            # 保存图像
            img.save(output_path)
            
            result_data = {
                "output_path": output_path,
                "original_size": original_size,
                "new_size": new_size
            }
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已缩放图像: {original_size} -> {new_size}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像缩放失败: {str(e)}")


@register_executor
class ImageCropExecutor(ModuleExecutor):
    """图像裁剪模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_crop"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        left = to_int(config.get("left", 0), 0, context)
        top = to_int(config.get("top", 0), 0, context)
        right = to_int(config.get("right", 0), 0, context)
        bottom = to_int(config.get("bottom", 0), 0, context)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_cropped{input_file.suffix}")
            
            img = Image.open(input_path)
            
            # 如果right和bottom为0，使用图像尺寸
            if right == 0:
                right = img.width
            if bottom == 0:
                bottom = img.height
            
            # 裁剪图像
            cropped = img.crop((left, top, right, bottom))
            cropped.save(output_path)
            
            result_data = {
                "output_path": output_path,
                "crop_box": (left, top, right, bottom),
                "cropped_size": cropped.size
            }
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已裁剪图像: ({left}, {top}, {right}, {bottom})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像裁剪失败: {str(e)}")


@register_executor
class ImageRotateExecutor(ModuleExecutor):
    """图像旋转模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_rotate"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        angle = to_float(config.get("angle", 0), 0, context)
        expand = config.get("expand", True)  # 是否扩展画布以容纳旋转后的图像
        fill_color = context.resolve_value(config.get("fillColor", "white"))  # 填充颜色
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_rotated{input_file.suffix}")
            
            img = Image.open(input_path)
            rotated = img.rotate(angle, expand=expand, fillcolor=fill_color)
            rotated.save(output_path)
            
            result_data = {
                "output_path": output_path,
                "angle": angle,
                "new_size": rotated.size
            }
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已旋转图像 {angle} 度",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像旋转失败: {str(e)}")



@register_executor
class ImageFlipExecutor(ModuleExecutor):
    """图像翻转模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_flip"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        flip_mode = context.resolve_value(config.get("flipMode", "horizontal"))  # horizontal, vertical
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_flipped{input_file.suffix}")
            
            img = Image.open(input_path)
            
            if flip_mode == "horizontal":
                flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif flip_mode == "vertical":
                flipped = img.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                return ModuleResult(success=False, error=f"不支持的翻转模式: {flip_mode}")
            
            flipped.save(output_path)
            
            result_data = {"output_path": output_path, "flip_mode": flip_mode}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已{('水平' if flip_mode == 'horizontal' else '垂直')}翻转图像",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像翻转失败: {str(e)}")


@register_executor
class ImageBlurExecutor(ModuleExecutor):
    """图像模糊模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_blur"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        radius = to_int(config.get("radius", 2), 2, context)  # 模糊半径
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageFilter
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_blurred{input_file.suffix}")
            
            img = Image.open(input_path)
            blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
            blurred.save(output_path)
            
            result_data = {"output_path": output_path, "radius": radius}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已应用高斯模糊 (半径: {radius})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像模糊失败: {str(e)}")


@register_executor
class ImageSharpenExecutor(ModuleExecutor):
    """图像锐化模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_sharpen"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        factor = to_float(config.get("factor", 2.0), 2.0, context)  # 锐化因子
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageEnhance
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_sharpened{input_file.suffix}")
            
            img = Image.open(input_path)
            enhancer = ImageEnhance.Sharpness(img)
            sharpened = enhancer.enhance(factor)
            sharpened.save(output_path)
            
            result_data = {"output_path": output_path, "factor": factor}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已锐化图像 (因子: {factor})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像锐化失败: {str(e)}")


@register_executor
class ImageBrightnessExecutor(ModuleExecutor):
    """图像亮度调整模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_brightness"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        factor = to_float(config.get("factor", 1.0), 1.0, context)  # 亮度因子 (0.0=全黑, 1.0=原始, >1.0=更亮)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageEnhance
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_brightness{input_file.suffix}")
            
            img = Image.open(input_path)
            enhancer = ImageEnhance.Brightness(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path)
            
            result_data = {"output_path": output_path, "factor": factor}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已调整图像亮度 (因子: {factor})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"亮度调整失败: {str(e)}")



@register_executor
class ImageContrastExecutor(ModuleExecutor):
    """图像对比度调整模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_contrast"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        factor = to_float(config.get("factor", 1.0), 1.0, context)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageEnhance
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_contrast{input_file.suffix}")
            
            img = Image.open(input_path)
            enhancer = ImageEnhance.Contrast(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path)
            
            result_data = {"output_path": output_path, "factor": factor}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已调整图像对比度 (因子: {factor})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"对比度调整失败: {str(e)}")


@register_executor
class ImageColorBalanceExecutor(ModuleExecutor):
    """图像色彩平衡调整模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_color_balance"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        factor = to_float(config.get("factor", 1.0), 1.0, context)
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageEnhance
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_color{input_file.suffix}")
            
            img = Image.open(input_path)
            enhancer = ImageEnhance.Color(img)
            adjusted = enhancer.enhance(factor)
            adjusted.save(output_path)
            
            result_data = {"output_path": output_path, "factor": factor}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已调整图像色彩平衡 (因子: {factor})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"色彩平衡调整失败: {str(e)}")


@register_executor
class ImageConvertFormatExecutor(ModuleExecutor):
    """图像格式转换模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_convert_format"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        output_format = context.resolve_value(config.get("outputFormat", "PNG"))  # PNG, JPEG, BMP, GIF, TIFF, WEBP
        quality = to_int(config.get("quality", 95), 95, context)  # JPEG质量
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                ext = output_format.lower()
                if ext == "jpeg":
                    ext = "jpg"
                output_path = str(input_file.with_suffix(f'.{ext}'))
            
            img = Image.open(input_path)
            
            # 如果转换为JPEG，需要转换RGBA为RGB
            if output_format.upper() in ['JPEG', 'JPG'] and img.mode in ['RGBA', 'LA', 'P']:
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ['RGBA', 'LA'] else None)
                img = rgb_img
            
            # 保存图像
            save_kwargs = {}
            if output_format.upper() in ['JPEG', 'JPG']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            img.save(output_path, format=output_format.upper(), **save_kwargs)
            
            result_data = {"output_path": output_path, "format": output_format}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已转换图像格式为 {output_format}",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"格式转换失败: {str(e)}")


@register_executor
class ImageAddTextExecutor(ModuleExecutor):
    """图像添加文字模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_add_text"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        text = context.resolve_value(config.get("text", ""))
        position_x = to_int(config.get("positionX", 10), 10, context)
        position_y = to_int(config.get("positionY", 10), 10, context)
        font_size = to_int(config.get("fontSize", 20), 20, context)
        font_color = context.resolve_value(config.get("fontColor", "black"))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")
        
        if not text:
            return ModuleResult(success=False, error="文字内容不能为空")

        try:
            from PIL import Image, ImageDraw, ImageFont
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_text{input_file.suffix}")
            
            img = Image.open(input_path)
            draw = ImageDraw.Draw(img)
            
            # 尝试使用系统字体
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("msyh.ttc", font_size)  # 微软雅黑
                except:
                    font = ImageFont.load_default()
            
            draw.text((position_x, position_y), text, fill=font_color, font=font)
            img.save(output_path)
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已在图像上添加文字",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"添加文字失败: {str(e)}")



@register_executor
class ImageMergeExecutor(ModuleExecutor):
    """图像拼接模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_merge"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        image_paths = context.resolve_value(config.get("imagePaths", ""))  # 逗号分隔的路径
        output_path = context.resolve_value(config.get("outputPath", ""))
        direction = context.resolve_value(config.get("direction", "horizontal"))  # horizontal, vertical
        spacing = to_int(config.get("spacing", 0), 0, context)  # 图像间距
        result_variable = config.get("resultVariable", "")

        if not image_paths:
            return ModuleResult(success=False, error="图像路径列表不能为空")
        
        # 解析路径列表
        paths = [p.strip() for p in image_paths.split(',')]
        if len(paths) < 2:
            return ModuleResult(success=False, error="至少需要2张图像进行拼接")
        
        # 检查所有文件是否存在
        for path in paths:
            if not Path(path).exists():
                return ModuleResult(success=False, error=f"图像文件不存在: {path}")

        try:
            from PIL import Image
            
            if not output_path:
                output_path = str(Path(paths[0]).parent / "merged_image.png")
            
            # 打开所有图像
            images = [Image.open(path) for path in paths]
            
            if direction == "horizontal":
                # 水平拼接
                total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
                max_height = max(img.height for img in images)
                merged = Image.new('RGB', (total_width, max_height), (255, 255, 255))
                
                x_offset = 0
                for img in images:
                    merged.paste(img, (x_offset, 0))
                    x_offset += img.width + spacing
            else:
                # 垂直拼接
                max_width = max(img.width for img in images)
                total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
                merged = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                
                y_offset = 0
                for img in images:
                    merged.paste(img, (0, y_offset))
                    y_offset += img.height + spacing
            
            merged.save(output_path)
            
            result_data = {
                "output_path": output_path,
                "image_count": len(images),
                "size": merged.size
            }
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已拼接 {len(images)} 张图像",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"图像拼接失败: {str(e)}")


@register_executor
class ImageThumbnailExecutor(ModuleExecutor):
    """生成缩略图模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_thumbnail"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        max_size = to_int(config.get("maxSize", 128), 128, context)  # 最大尺寸
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_thumb{input_file.suffix}")
            
            img = Image.open(input_path)
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            img.save(output_path)
            
            result_data = {
                "output_path": output_path,
                "thumbnail_size": img.size
            }
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已生成缩略图 (最大尺寸: {max_size})",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"生成缩略图失败: {str(e)}")


@register_executor
class ImageFilterExecutor(ModuleExecutor):
    """图像滤镜模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_filter"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        filter_type = context.resolve_value(config.get("filterType", "BLUR"))  # BLUR, CONTOUR, DETAIL, EDGE_ENHANCE, EMBOSS, SMOOTH, SHARPEN
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image, ImageFilter
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_filtered{input_file.suffix}")
            
            img = Image.open(input_path)
            
            # 应用滤镜
            filter_map = {
                'BLUR': ImageFilter.BLUR,
                'CONTOUR': ImageFilter.CONTOUR,
                'DETAIL': ImageFilter.DETAIL,
                'EDGE_ENHANCE': ImageFilter.EDGE_ENHANCE,
                'EDGE_ENHANCE_MORE': ImageFilter.EDGE_ENHANCE_MORE,
                'EMBOSS': ImageFilter.EMBOSS,
                'FIND_EDGES': ImageFilter.FIND_EDGES,
                'SMOOTH': ImageFilter.SMOOTH,
                'SMOOTH_MORE': ImageFilter.SMOOTH_MORE,
                'SHARPEN': ImageFilter.SHARPEN
            }
            
            if filter_type not in filter_map:
                return ModuleResult(success=False, error=f"不支持的滤镜类型: {filter_type}")
            
            filtered = img.filter(filter_map[filter_type])
            filtered.save(output_path)
            
            result_data = {"output_path": output_path, "filter_type": filter_type}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已应用 {filter_type} 滤镜",
                data=result_data
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"应用滤镜失败: {str(e)}")


@register_executor
class ImageGetInfoExecutor(ModuleExecutor):
    """获取图像信息模块执行器"""

    @property
    def module_type(self) -> str:
        return "image_get_info"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            import os
            
            img = Image.open(input_path)
            file_stat = os.stat(input_path)
            
            info = {
                "path": input_path,
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "file_size": file_stat.st_size,
                "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2)
            }
            
            # 获取EXIF信息（如果有）
            try:
                exif = img._getexif()
                if exif:
                    info["has_exif"] = True
                else:
                    info["has_exif"] = False
            except:
                info["has_exif"] = False
            
            if result_variable:
                context.set_variable(result_variable, info)
            
            return ModuleResult(
                success=True,
                message=f"图像信息: {img.width}x{img.height}, {img.format}, {info['file_size_mb']}MB",
                data=info
            )

        except ImportError:
            return ModuleResult(success=False, error="需要安装Pillow库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"获取图像信息失败: {str(e)}")


@register_executor
class ImageRemoveBackgroundExecutor(ModuleExecutor):
    """图像去背景模块执行器（简单色彩去除）"""

    @property
    def module_type(self) -> str:
        return "image_remove_bg"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        input_path = context.resolve_value(config.get("inputPath", ""))
        output_path = context.resolve_value(config.get("outputPath", ""))
        bg_color = context.resolve_value(config.get("bgColor", "white"))  # 要移除的背景色
        tolerance = to_int(config.get("tolerance", 30), 30, context)  # 容差
        result_variable = config.get("resultVariable", "")

        if not input_path:
            return ModuleResult(success=False, error="输入图像路径不能为空")
        
        if not Path(input_path).exists():
            return ModuleResult(success=False, error=f"输入图像不存在: {input_path}")

        try:
            from PIL import Image
            import numpy as np
            
            if not output_path:
                input_file = Path(input_path)
                output_path = str(input_file.parent / f"{input_file.stem}_nobg.png")
            
            img = Image.open(input_path).convert('RGBA')
            data = np.array(img)
            
            # 解析背景色
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255)
            }
            
            if bg_color.lower() in color_map:
                target_color = color_map[bg_color.lower()]
            else:
                # 尝试解析RGB值
                try:
                    target_color = tuple(map(int, bg_color.split(',')))
                except:
                    target_color = (255, 255, 255)
            
            # 计算颜色差异
            r, g, b = target_color
            red, green, blue, alpha = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
            
            # 创建掩码
            mask = (abs(red - r) < tolerance) & (abs(green - g) < tolerance) & (abs(blue - b) < tolerance)
            data[mask, 3] = 0  # 设置为透明
            
            result_img = Image.fromarray(data)
            result_img.save(output_path, 'PNG')
            
            result_data = {"output_path": output_path}
            if result_variable:
                context.set_variable(result_variable, result_data)
            
            return ModuleResult(
                success=True,
                message=f"已移除背景色",
                data=result_data
            )

        except ImportError as e:
            missing = "numpy" if "numpy" in str(e) else "Pillow"
            return ModuleResult(success=False, error=f"需要安装库: pip install {missing}")
        except Exception as e:
            return ModuleResult(success=False, error=f"移除背景失败: {str(e)}")
