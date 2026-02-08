"""高级模块执行器 - advanced_clipboard"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from pathlib import Path
import asyncio
import ctypes
import os
import re
import subprocess
import tempfile
import time


@register_executor
class SetClipboardExecutor(ModuleExecutor):
    """设置剪贴板模块执行器"""

    @property
    def module_type(self) -> str:
        return "set_clipboard"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        import subprocess
        import ctypes
        from ctypes import wintypes
        
        content_type = context.resolve_value(config.get("contentType", "text"))  # 支持变量引用
        text_content = context.resolve_value(config.get("textContent", ""))
        image_path = context.resolve_value(config.get("imagePath", ""))

        try:
            if content_type == "image":
                if not image_path:
                    return ModuleResult(success=False, error="图片路径不能为空")

                if not Path(image_path).exists():
                    return ModuleResult(success=False, error=f"图片文件不存在: {image_path}")

                try:
                    from PIL import Image
                    import tempfile

                    img = Image.open(image_path)
                    if img.mode == "RGBA":
                        img = img.convert("RGB")
                    
                    with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as tmp:
                        tmp_path = tmp.name
                        img.save(tmp_path, "BMP")
                    
                    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$image = [System.Drawing.Image]::FromFile("{tmp_path.replace(chr(92), '/')}")
[System.Windows.Forms.Clipboard]::SetImage($image)
$image.Dispose()
'''
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None, 
                        lambda: subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
                    )
                    
                    try:
                        Path(tmp_path).unlink()
                    except:
                        pass
                    
                    if result.returncode != 0:
                        return ModuleResult(success=False, error=f"设置剪贴板失败: {result.stderr}")

                    return ModuleResult(success=True, message=f"已将图片复制到剪贴板: {image_path}")

                except ImportError:
                    return ModuleResult(success=False, error="需要安装 Pillow 库")

            else:
                if not text_content:
                    return ModuleResult(success=False, error="文本内容不能为空")

                # 使用 Windows API 直接操作剪贴板（更稳定）
                def set_clipboard_text(text: str) -> tuple[bool, str]:
                    """使用 Windows API 设置剪贴板文本，返回 (成功, 错误信息)"""
                    import ctypes
                    from ctypes import wintypes
                    
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    
                    # 使用 HANDLE 类型（64位兼容）
                    HANDLE = ctypes.c_void_p
                    LPVOID = ctypes.c_void_p
                    
                    # 设置正确的参数和返回类型
                    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
                    kernel32.GlobalAlloc.restype = HANDLE
                    kernel32.GlobalLock.argtypes = [HANDLE]
                    kernel32.GlobalLock.restype = LPVOID
                    kernel32.GlobalUnlock.argtypes = [HANDLE]
                    kernel32.GlobalUnlock.restype = wintypes.BOOL
                    kernel32.GlobalFree.argtypes = [HANDLE]
                    kernel32.GlobalFree.restype = HANDLE
                    user32.SetClipboardData.argtypes = [wintypes.UINT, HANDLE]
                    user32.SetClipboardData.restype = HANDLE
                    
                    CF_UNICODETEXT = 13
                    GMEM_MOVEABLE = 0x0002
                    
                    # 尝试多次打开剪贴板（处理被占用的情况）
                    max_retries = 10
                    for i in range(max_retries):
                        if user32.OpenClipboard(0):
                            break
                        import time
                        time.sleep(0.1)
                    else:
                        return False, "无法打开剪贴板，可能被其他程序占用"
                    
                    try:
                        user32.EmptyClipboard()
                        
                        # 转换为 UTF-16 编码（包含终止符）
                        text_bytes = text.encode('utf-16-le') + b'\x00\x00'
                        
                        # 分配全局内存
                        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes))
                        if not h_mem:
                            return False, "内存分配失败"
                        
                        # 锁定内存并复制数据
                        p_mem = kernel32.GlobalLock(h_mem)
                        if not p_mem:
                            kernel32.GlobalFree(h_mem)
                            return False, "内存锁定失败"
                        
                        try:
                            ctypes.memmove(p_mem, text_bytes, len(text_bytes))
                        finally:
                            kernel32.GlobalUnlock(h_mem)
                        
                        # 设置剪贴板数据
                        if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                            kernel32.GlobalFree(h_mem)
                            return False, "设置剪贴板数据失败"
                        
                        return True, ""
                    finally:
                        user32.CloseClipboard()
                
                loop = asyncio.get_running_loop()
                success, error_msg = await loop.run_in_executor(None, lambda: set_clipboard_text(text_content))
                
                if not success:
                    return ModuleResult(success=False, error=f"设置剪贴板失败: {error_msg}")

                display_text = text_content[:50] + "..." if len(text_content) > 50 else text_content
                return ModuleResult(success=True, message=f"已将文本复制到剪贴板: {display_text}")

        except Exception as e:
            return ModuleResult(success=False, error=f"设置剪贴板失败: {str(e)}")

@register_executor
class GetClipboardExecutor(ModuleExecutor):
    """获取剪贴板模块执行器"""

    @property
    def module_type(self) -> str:
        return "get_clipboard"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        variable_name = config.get("variableName", "")

        if not variable_name:
            return ModuleResult(success=False, error="存储变量名不能为空")

        try:
            def get_clipboard_text() -> tuple[str | None, str]:
                """使用 Windows API 获取剪贴板文本，返回 (内容, 错误信息)"""
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                
                # 使用 HANDLE 类型（64位兼容）
                HANDLE = ctypes.c_void_p
                LPVOID = ctypes.c_void_p
                
                # 设置正确的参数和返回类型
                kernel32.GlobalLock.argtypes = [HANDLE]
                kernel32.GlobalLock.restype = LPVOID
                kernel32.GlobalUnlock.argtypes = [HANDLE]
                kernel32.GlobalUnlock.restype = wintypes.BOOL
                user32.GetClipboardData.argtypes = [wintypes.UINT]
                user32.GetClipboardData.restype = HANDLE
                
                CF_UNICODETEXT = 13
                
                # 尝试多次打开剪贴板（处理被占用的情况）
                max_retries = 10
                for i in range(max_retries):
                    if user32.OpenClipboard(0):
                        break
                    import time
                    time.sleep(0.1)
                else:
                    return None, "无法打开剪贴板，可能被其他程序占用"
                
                try:
                    # 获取剪贴板数据
                    h_data = user32.GetClipboardData(CF_UNICODETEXT)
                    if not h_data:
                        return "", ""  # 剪贴板为空
                    
                    # 锁定内存并读取数据
                    p_data = kernel32.GlobalLock(h_data)
                    if not p_data:
                        return "", ""
                    
                    try:
                        # 读取 Unicode 字符串
                        text = ctypes.wstring_at(p_data)
                        return text, ""
                    finally:
                        kernel32.GlobalUnlock(h_data)
                finally:
                    user32.CloseClipboard()
            
            loop = asyncio.get_running_loop()
            clipboard_content, error_msg = await loop.run_in_executor(None, get_clipboard_text)
            
            if clipboard_content is None:
                return ModuleResult(success=False, error=f"获取剪贴板失败: {error_msg}")
            
            context.set_variable(variable_name, clipboard_content)

            if not clipboard_content:
                return ModuleResult(
                    success=True,
                    message=f"剪贴板为空，已设置变量 {variable_name} 为空字符串",
                    data=clipboard_content
                )

            display_text = clipboard_content[:50] + "..." if len(clipboard_content) > 50 else clipboard_content
            return ModuleResult(
                success=True,
                message=f"已获取剪贴板内容: {display_text}",
                data=clipboard_content
            )

        except Exception as e:
            return ModuleResult(success=False, error=f"获取剪贴板失败: {str(e)}")