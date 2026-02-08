"""高级模块执行器 - advanced_share"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from .type_utils import to_int, to_float, parse_search_region
from pathlib import Path
import re


@register_executor
class ShareFolderExecutor(ModuleExecutor):
    """文件夹网络共享模块执行器 - 将指定文件夹通过HTTP共享到局域网"""

    @property
    def module_type(self) -> str:
        return "share_folder"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.services.file_share import start_file_share, get_local_ip
        
        folder_path = context.resolve_value(config.get("folderPath", ""))
        port = to_int(config.get("port", 8080), 8080, context)
        share_name = context.resolve_value(config.get("shareName", "")) or "共享文件夹"
        result_variable = config.get("resultVariable", "share_url")
        allow_write = config.get("allowWrite", True)  # 默认允许写操作
        
        if not folder_path:
            return ModuleResult(success=False, error="文件夹路径不能为空")
        
        folder = Path(folder_path)
        if not folder.exists():
            return ModuleResult(success=False, error=f"文件夹不存在: {folder_path}")
        
        if not folder.is_dir():
            return ModuleResult(success=False, error=f"路径不是文件夹: {folder_path}")
        
        try:
            result = start_file_share(
                path=str(folder.resolve()),
                port=port,
                share_type='folder',
                name=share_name,
                allow_write=allow_write
            )
            
            if not result['success']:
                return ModuleResult(success=False, error=result.get('error', '启动共享服务失败'))
            
            share_url = result['url']
            local_ip = result['ip']
            
            if result_variable:
                context.set_variable(result_variable, share_url)
            
            write_mode = "可上传/删除" if allow_write else "仅下载"
            message = f"📂 文件夹共享已启动！\n" \
                      f"共享名称: {share_name}\n" \
                      f"共享路径: {folder_path}\n" \
                      f"访问地址: {share_url}\n" \
                      f"权限模式: {write_mode}\n" \
                      f"💡 同局域网的设备可以使用浏览器访问上述地址来浏览和下载文件"
            
            return ModuleResult(
                success=True,
                message=message,
                data={
                    'url': share_url,
                    'ip': local_ip,
                    'port': port,
                    'path': str(folder.resolve()),
                    'name': share_name,
                    'allowWrite': allow_write
                }
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"启动文件夹共享失败: {str(e)}")

@register_executor
class ShareFileExecutor(ModuleExecutor):
    """文件网络共享模块执行器 - 将指定文件通过HTTP共享到局域网"""

    @property
    def module_type(self) -> str:
        return "share_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.services.file_share import start_file_share, get_local_ip
        
        file_path = context.resolve_value(config.get("filePath", ""))
        port = to_int(config.get("port", 8080), 8080, context)
        result_variable = config.get("resultVariable", "share_url")
        
        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")
        
        file = Path(file_path)
        if not file.exists():
            return ModuleResult(success=False, error=f"文件不存在: {file_path}")
        
        if not file.is_file():
            return ModuleResult(success=False, error=f"路径不是文件: {file_path}")
        
        try:
            result = start_file_share(
                path=str(file.resolve()),
                port=port,
                share_type='file',
                name=file.name
            )
            
            if not result['success']:
                return ModuleResult(success=False, error=result.get('error', '启动共享服务失败'))
            
            share_url = result['url']
            local_ip = result['ip']
            file_size = file.stat().st_size
            
            # 格式化文件大小
            size_str = self._format_size(file_size)
            
            if result_variable:
                context.set_variable(result_variable, share_url)
            
            message = f"📄 文件共享已启动！\n" \
                      f"文件名: {file.name}\n" \
                      f"文件大小: {size_str}\n" \
                      f"访问地址: {share_url}\n" \
                      f"💡 同局域网的设备可以使用浏览器访问上述地址来下载此文件"
            
            return ModuleResult(
                success=True,
                message=message,
                data={
                    'url': share_url,
                    'ip': local_ip,
                    'port': port,
                    'path': str(file.resolve()),
                    'name': file.name,
                    'size': file_size
                }
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"启动文件共享失败: {str(e)}")
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

@register_executor
class StopShareExecutor(ModuleExecutor):
    """停止网络共享模块执行器"""

    @property
    def module_type(self) -> str:
        return "stop_share"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        from app.services.file_share import stop_file_share
        
        port = to_int(config.get("port", 8080), 8080, context)
        
        try:
            result = stop_file_share(port)
            
            if not result['success']:
                return ModuleResult(success=False, error=result.get('error', '停止共享服务失败'))
            
            return ModuleResult(
                success=True,
                message=f"端口 {port} 的共享服务已停止",
                data={'port': port}
            )
            
        except Exception as e:
            return ModuleResult(success=False, error=f"停止共享服务失败: {str(e)}")