"""高级模块执行器 - 文件信息（创建文件夹、检查存在、获取信息、读写文本）"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from datetime import datetime
from pathlib import Path


@register_executor
class CreateFolderExecutor(ModuleExecutor):
    """创建文件夹模块执行器"""

    @property
    def module_type(self) -> str:
        return "create_folder"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        folder_path = context.resolve_value(config.get("folderPath", ""))
        variable_name = config.get("resultVariable", "folder_path")

        if not folder_path:
            return ModuleResult(success=False, error="文件夹路径不能为空")

        try:
            folder = Path(folder_path)
            if folder.exists():
                if folder.is_dir():
                    if variable_name:
                        context.set_variable(variable_name, str(folder))
                    return ModuleResult(success=True, message=f"文件夹已存在: {folder_path}", data=str(folder))
                return ModuleResult(success=False, error=f"路径已存在且不是文件夹: {folder_path}")
            
            folder.mkdir(parents=True, exist_ok=True)
            if variable_name:
                context.set_variable(variable_name, str(folder))
            return ModuleResult(success=True, message=f"文件夹已创建: {folder_path}", data=str(folder))
        except Exception as e:
            return ModuleResult(success=False, error=f"创建文件夹失败: {str(e)}")


@register_executor
class FileExistsExecutor(ModuleExecutor):
    """文件是否存在模块执行器"""

    @property
    def module_type(self) -> str:
        return "file_exists"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file_path = context.resolve_value(config.get("filePath", ""))
        variable_name = config.get("resultVariable", "exists")

        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")

        try:
            exists = Path(file_path).exists()
            if variable_name:
                context.set_variable(variable_name, exists)
            return ModuleResult(success=True, message=f"{'存在' if exists else '不存在'}: {file_path}", data=exists)
        except Exception as e:
            return ModuleResult(success=False, error=f"检查文件存在失败: {str(e)}")


@register_executor
class GetFileInfoExecutor(ModuleExecutor):
    """获取文件信息模块执行器"""

    @property
    def module_type(self) -> str:
        return "get_file_info"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file_path = context.resolve_value(config.get("filePath", ""))
        variable_name = config.get("resultVariable", "file_info")

        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")

        try:
            path = Path(file_path)
            if not path.exists():
                return ModuleResult(success=False, error=f"文件不存在: {file_path}")
            
            stat = path.stat()
            file_info = {
                "name": path.name,
                "path": str(path.absolute()),
                "size": stat.st_size,
                "extension": path.suffix.lower() if path.is_file() else "",
                "created_time": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_file": path.is_file(),
                "is_folder": path.is_dir(),
            }
            
            if variable_name:
                context.set_variable(variable_name, file_info)
            
            size_str = self._format_size(stat.st_size)
            return ModuleResult(success=True, message=f"{path.name} ({size_str})", data=file_info)
        except Exception as e:
            return ModuleResult(success=False, error=f"获取文件信息失败: {str(e)}")
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@register_executor
class ReadTextFileExecutor(ModuleExecutor):
    """读取文本文件模块执行器"""

    @property
    def module_type(self) -> str:
        return "read_text_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file_path = context.resolve_value(config.get("filePath", ""))
        encoding = context.resolve_value(config.get("encoding", "utf-8"))
        variable_name = config.get("resultVariable", "file_content")

        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")

        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return ModuleResult(success=False, error=f"文件不存在: {file_path}")
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            if variable_name:
                context.set_variable(variable_name, content)
            
            preview = (content[:100] + "...").replace('\n', '\\n') if len(content) > 100 else content.replace('\n', '\\n')
            return ModuleResult(success=True, message=f"已读取 {len(content)} 字符: {preview}", data=content)
        except UnicodeDecodeError:
            return ModuleResult(success=False, error=f"文件编码错误，请尝试其他编码格式（当前: {encoding}）")
        except Exception as e:
            return ModuleResult(success=False, error=f"读取文件失败: {str(e)}")


@register_executor
class WriteTextFileExecutor(ModuleExecutor):
    """写入文本文件模块执行器"""

    @property
    def module_type(self) -> str:
        return "write_text_file"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        file_path = context.resolve_value(config.get("filePath", ""))
        content = context.resolve_value(config.get("content", ""))
        encoding = context.resolve_value(config.get("encoding", "utf-8"))
        write_mode = context.resolve_value(config.get("writeMode", "overwrite"))
        variable_name = config.get("resultVariable", "write_path")

        if not file_path:
            return ModuleResult(success=False, error="文件路径不能为空")

        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = 'a' if write_mode == 'append' else 'w'
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            if variable_name:
                context.set_variable(variable_name, str(path))
            
            action = "追加" if write_mode == 'append' else "写入"
            return ModuleResult(success=True, message=f"已{action} {len(content)} 字符到: {path.name}", data=str(path))
        except Exception as e:
            return ModuleResult(success=False, error=f"写入文件失败: {str(e)}")


@register_executor
class RenameFolderExecutor(ModuleExecutor):
    """文件夹重命名模块执行器"""

    @property
    def module_type(self) -> str:
        return "rename_folder"

    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        source_path = context.resolve_value(config.get("sourcePath", ""))
        new_name = context.resolve_value(config.get("newName", ""))
        variable_name = config.get("resultVariable", "new_folder_path")

        if not source_path or not new_name:
            return ModuleResult(success=False, error="源文件夹路径和新文件夹名不能为空")

        try:
            source = Path(source_path)
            if not source.exists() or not source.is_dir():
                return ModuleResult(success=False, error=f"源文件夹不存在: {source_path}")
            
            new_path = source.parent / new_name
            if new_path.exists():
                return ModuleResult(success=False, error=f"目标文件夹已存在: {new_path}")
            
            source.rename(new_path)
            if variable_name:
                context.set_variable(variable_name, str(new_path))
            return ModuleResult(success=True, message=f"文件夹已重命名: {source.name} → {new_name}", data=str(new_path))
        except Exception as e:
            return ModuleResult(success=False, error=f"文件夹重命名失败: {str(e)}")
