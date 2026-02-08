"""验证码处理模块执行器实现 - 异步版本"""
import asyncio
import base64
import random

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


def _patch_pil_antialias():
    """修复 Pillow 10.0+ 移除 ANTIALIAS 的兼容性问题"""
    try:
        from PIL import Image
        if not hasattr(Image, 'ANTIALIAS'):
            Image.ANTIALIAS = Image.Resampling.LANCZOS
    except Exception:
        pass


_patch_pil_antialias()


@register_executor
class OCRCaptchaExecutor(ModuleExecutor):
    """文本验证码识别模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "ocr_captcha"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        image_selector = context.resolve_value(config.get('imageSelector', ''))
        input_selector = context.resolve_value(config.get('inputSelector', ''))
        variable_name = config.get('variableName', '')
        auto_submit_raw = config.get('autoSubmit', False)
        # 支持变量引用
        if isinstance(auto_submit_raw, str):
            auto_submit_raw = context.resolve_value(auto_submit_raw)
        auto_submit = auto_submit_raw in [True, 'true', 'True', '1', 1]
        submit_selector = context.resolve_value(config.get('submitSelector', ''))
        
        if not image_selector:
            return ModuleResult(success=False, error="验证码图片选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            import ddddocr
            # ddddocr 1.0.6+ (Python 3.13) 不支持 show_ad 等参数
            ocr = ddddocr.DdddOcr()
            
            element = context.page.locator(image_selector)
            src = await element.get_attribute('src')
            
            if src and src.startswith('data:'):
                header, data = src.split(',', 1)
                image_bytes = base64.b64decode(data)
            else:
                image_bytes = await element.screenshot()
            
            # 使用线程池执行同步OCR操作
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, ocr.classification, image_bytes)
            
            if variable_name:
                context.set_variable(variable_name, result)
            
            if input_selector:
                await context.page.fill(input_selector, result)
            
            if auto_submit and submit_selector:
                await context.page.click(submit_selector)
            
            return ModuleResult(success=True, message=f"验证码识别结果: {result}", data=result)
        except ImportError:
            return ModuleResult(success=False, error="验证码识别功能初始化失败")
        except Exception as e:
            return ModuleResult(success=False, error=f"验证码识别失败: {str(e)}")


@register_executor
class SliderCaptchaExecutor(ModuleExecutor):
    """滑块验证码模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "slider_captcha"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        slider_selector = context.resolve_value(config.get('sliderSelector', ''))
        background_selector = context.resolve_value(config.get('backgroundSelector', ''))
        gap_selector = context.resolve_value(config.get('gapSelector', ''))
        
        if not slider_selector:
            return ModuleResult(success=False, error="滑块选择器不能为空")
        
        if context.page is None:
            return ModuleResult(success=False, error="没有打开的页面")
        
        try:
            slider = context.page.locator(slider_selector)
            slider_box = await slider.bounding_box()
            
            if not slider_box:
                return ModuleResult(success=False, error="无法获取滑块位置")
            
            slide_distance = 200  # 默认滑动距离
            
            # 使用 OpenCV 进行滑块缺口匹配
            if background_selector and gap_selector:
                try:
                    import cv2
                    import numpy as np
                    
                    bg_element = context.page.locator(background_selector)
                    gap_element = context.page.locator(gap_selector)
                    
                    bg_bytes = await bg_element.screenshot()
                    gap_bytes = await gap_element.screenshot()
                    
                    loop = asyncio.get_running_loop()
                    
                    def find_gap_position():
                        # 将字节转换为图像
                        bg_img = cv2.imdecode(np.frombuffer(bg_bytes, np.uint8), cv2.IMREAD_COLOR)
                        gap_img = cv2.imdecode(np.frombuffer(gap_bytes, np.uint8), cv2.IMREAD_COLOR)
                        
                        if bg_img is None or gap_img is None:
                            return None
                        
                        # 转换为灰度图
                        bg_gray = cv2.cvtColor(bg_img, cv2.COLOR_BGR2GRAY)
                        gap_gray = cv2.cvtColor(gap_img, cv2.COLOR_BGR2GRAY)
                        
                        # 边缘检测
                        bg_edge = cv2.Canny(bg_gray, 100, 200)
                        gap_edge = cv2.Canny(gap_gray, 100, 200)
                        
                        # 模板匹配
                        result = cv2.matchTemplate(bg_edge, gap_edge, cv2.TM_CCOEFF_NORMED)
                        _, _, _, max_loc = cv2.minMaxLoc(result)
                        
                        return max_loc[0]  # 返回X坐标
                    
                    gap_x = await loop.run_in_executor(None, find_gap_position)
                    if gap_x is not None:
                        slide_distance = gap_x
                except Exception:
                    pass  # 匹配失败时使用默认距离
            
            start_x = slider_box['x'] + slider_box['width'] / 2
            start_y = slider_box['y'] + slider_box['height'] / 2
            
            await context.page.mouse.move(start_x, start_y)
            await context.page.mouse.down()
            
            current_x = start_x
            target_x = start_x + slide_distance
            
            while current_x < target_x:
                step = random.randint(5, 20)
                current_x = min(current_x + step, target_x)
                y_offset = random.randint(-2, 2)
                await context.page.mouse.move(current_x, start_y + y_offset)
                await asyncio.sleep(random.uniform(0.01, 0.03))
            
            await context.page.mouse.up()
            await asyncio.sleep(1)
            
            return ModuleResult(success=True, message=f"滑块验证完成，滑动距离: {slide_distance}px")
        
        except Exception as e:
            return ModuleResult(success=False, error=f"滑块验证失败: {str(e)}")
