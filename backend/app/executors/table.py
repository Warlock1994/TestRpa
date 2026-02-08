"""数据表格操作模块执行器 - 异步版本"""
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


@register_executor
class TableAddRowExecutor(ModuleExecutor):
    """添加数据行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_add_row"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_data_str = context.resolve_value(config.get('rowData', ''))
        
        if not row_data_str:
            return ModuleResult(success=False, error="行数据不能为空")
        
        try:
            row_data = json.loads(row_data_str)
            
            if not isinstance(row_data, dict):
                return ModuleResult(success=False, error="行数据必须是JSON对象格式")
            
            context.data_rows.append(row_data)
            
            return ModuleResult(
                success=True,
                message=f"已添加数据行，当前共 {len(context.data_rows)} 行",
                data={'row': row_data, 'total_rows': len(context.data_rows)}
            )
        
        except json.JSONDecodeError as e:
            return ModuleResult(success=False, error=f"JSON解析失败: {str(e)}")
        except Exception as e:
            return ModuleResult(success=False, error=f"添加数据行失败: {str(e)}")


@register_executor
class TableAddColumnExecutor(ModuleExecutor):
    """添加数据列模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_add_column"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        column_name = context.resolve_value(config.get('columnName', ''))
        default_value = context.resolve_value(config.get('defaultValue', ''))
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        
        try:
            for row in context.data_rows:
                if column_name not in row:
                    row[column_name] = default_value
            
            if not context.data_rows:
                context.data_rows.append({column_name: default_value})
            
            return ModuleResult(
                success=True,
                message=f"已添加列 '{column_name}'",
                data={'column': column_name, 'default': default_value}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"添加数据列失败: {str(e)}")


@register_executor
class TableSetCellExecutor(ModuleExecutor):
    """设置单元格模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_set_cell"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        column_name = context.resolve_value(config.get('columnName', ''))
        cell_value = context.resolve_value(config.get('cellValue', ''))
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {row_index} 超出范围")
        
        try:
            context.data_rows[row_index][column_name] = cell_value
            
            return ModuleResult(
                success=True,
                message=f"已设置 [{row_index}][{column_name}] = {cell_value}",
                data={'row': row_index, 'column': column_name, 'value': cell_value}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"设置单元格失败: {str(e)}")


@register_executor
class TableGetCellExecutor(ModuleExecutor):
    """获取单元格模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_get_cell"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        column_name = context.resolve_value(config.get('columnName', ''))
        variable_name = config.get('variableName', '')
        
        if not column_name:
            return ModuleResult(success=False, error="列名不能为空")
        if not variable_name:
            return ModuleResult(success=False, error="存储变量名不能为空")
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {row_index} 超出范围")
        
        row = context.data_rows[row_index]
        
        if column_name not in row:
            return ModuleResult(success=False, error=f"列 '{column_name}' 不存在")
        
        value = row[column_name]
        context.set_variable(variable_name, value)
        
        return ModuleResult(
            success=True,
            message=f"获取 [{row_index}][{column_name}] = {value}",
            data=value
        )


@register_executor
class TableDeleteRowExecutor(ModuleExecutor):
    """删除数据行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_delete_row"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        row_index_str = context.resolve_value(str(config.get('rowIndex', '0')))
        
        try:
            row_index = int(row_index_str)
        except ValueError:
            return ModuleResult(success=False, error=f"无效的行索引: {row_index_str}")
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空")
        
        original_index = row_index
        if row_index < 0:
            row_index = len(context.data_rows) + row_index
        
        if row_index < 0 or row_index >= len(context.data_rows):
            return ModuleResult(success=False, error=f"行索引 {original_index} 超出范围")
        
        try:
            deleted_row = context.data_rows.pop(row_index)
            
            return ModuleResult(
                success=True,
                message=f"已删除第 {row_index} 行，剩余 {len(context.data_rows)} 行",
                data={'deleted': deleted_row, 'remaining': len(context.data_rows)}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"删除数据行失败: {str(e)}")


@register_executor
class TableClearExecutor(ModuleExecutor):
    """清空数据表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_clear"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        try:
            row_count = len(context.data_rows)
            context.data_rows.clear()
            context.current_row.clear()
            
            return ModuleResult(
                success=True,
                message=f"已清空数据表格 (原有 {row_count} 行)",
                data={'cleared_rows': row_count}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"清空数据表失败: {str(e)}")


@register_executor
class TableExportExecutor(ModuleExecutor):
    """导出数据表模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "table_export"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        export_format = context.resolve_value(config.get('exportFormat', 'excel'))  # 支持变量引用
        save_path = context.resolve_value(config.get('savePath', ''))
        file_name_pattern = context.resolve_value(config.get('fileNamePattern', ''))
        variable_name = config.get('variableName', '')
        
        if not context.data_rows:
            return ModuleResult(success=False, error="数据表格为空，无法导出")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if file_name_pattern:
                file_name = file_name_pattern.replace('{时间戳}', timestamp)
            else:
                file_name = f"data_{timestamp}"
            
            ext = '.xlsx' if export_format == 'excel' else '.csv'
            if not file_name.endswith(ext):
                file_name += ext
            
            if save_path:
                if save_path.endswith(ext):
                    final_path = save_path
                else:
                    os.makedirs(save_path, exist_ok=True)
                    final_path = os.path.join(save_path, file_name)
            else:
                data_dir = Path(__file__).parent.parent.parent / 'data'
                data_dir.mkdir(parents=True, exist_ok=True)
                final_path = str(data_dir / file_name)
            
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            from app.services.data_collector import DataCollector
            
            collector = DataCollector()
            for row in context.data_rows:
                collector.add_row(row)
            
            # 使用线程池执行同步导出操作
            loop = asyncio.get_running_loop()
            if export_format == 'excel':
                await loop.run_in_executor(None, collector.to_excel, final_path)
            else:
                await loop.run_in_executor(None, collector.to_csv, final_path)
            
            if variable_name:
                context.set_variable(variable_name, final_path)
            
            return ModuleResult(
                success=True,
                message=f"已导出 {len(context.data_rows)} 行数据到: {final_path}",
                data={'path': final_path, 'rows': len(context.data_rows), 'format': export_format}
            )
        
        except Exception as e:
            return ModuleResult(success=False, error=f"导出数据表失败: {str(e)}")
