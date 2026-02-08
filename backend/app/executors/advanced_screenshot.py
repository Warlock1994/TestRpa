"""高级模块执行器 - 屏幕截图"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int
from pathlib import Path
import datetime


@register_executor
class ScreenshotScreenExecutor(ModuleExecutor):
    """屏幕截图模块执行器"""

    @property
    def module_type(self) -> str:
        return "screenshot_screen"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        save_path = context.resolve_value(config.get("savePath", ""))
        file_name = context.resolve_value(config.get("fileName", ""))
        region = context.resolve_value(config.get("region", "full"))
        variable_name = config.get("variableName", "")

        try:
            from PIL import ImageGrab

            # 生成文件名
            if not file_name:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"screenshot_{timestamp}.png"
            elif not file_name.lower().endswith('.png'):
                file_name += '.png'

            # 确定保存路径
            if save_path:
                Path(save_path).mkdir(parents=True, exist_ok=True)
                full_path = Path(save_path) / file_name
            else:
                screenshots_dir = Path("screenshots")
                screenshots_dir.mkdir(exist_ok=True)
                full_path = screenshots_dir / file_name

            # 截图
            if region == "custom":
                x1 = to_int(config.get("x1", 0), 0, context)
                y1 = to_int(config.get("y1", 0), 0, context)
                x2 = to_int(config.get("x2", 800), 800, context)
                y2 = to_int(config.get("y2", 600), 600, context)
                
                left, top = min(x1, x2), min(y1, y2)
                right, bottom = max(x1, x2), max(y1, y2)
                
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                message = f"屏幕截图已保存: {full_path} (区域: {right-left}×{bottom-top})"
            else:
                screenshot = ImageGrab.grab()
                message = f"屏幕截图已保存: {full_path}"

            screenshot.save(str(full_path), "PNG")

            if variable_name:
                context.set_variable(variable_name, str(full_path))

            return ModuleResult(success=True, message=message, data=str(full_path))

        except ImportError:
            return ModuleResult(success=False, error="需要安装 Pillow 库: pip install Pillow")
        except Exception as e:
            return ModuleResult(success=False, error=f"屏幕截图失败: {str(e)}")
