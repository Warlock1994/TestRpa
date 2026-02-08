"""高级模块执行器 - advanced_log"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor
from datetime import datetime
from pathlib import Path
import json
import re
import time


@register_executor
class ExportLogExecutor(ModuleExecutor):
    """导出日志模块执行器 - 将工作流执行日志导出到文件"""
    
    @property
    def module_type(self) -> str:
        return "export_log"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        output_path = context.resolve_value(config.get('outputPath', ''))
        log_format = config.get('logFormat', 'txt')  # txt, json, csv
        include_timestamp = config.get('includeTimestamp', True)
        include_level = config.get('includeLevel', True)
        include_duration = config.get('includeDuration', True)
        result_variable = config.get('resultVariable', '')
        
        if not output_path:
            # 默认保存到项目根目录的logs文件夹
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(__file__).parent.parent.parent.parent / 'logs'
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f'workflow_log_{timestamp}.{log_format}')
        
        try:
            # 获取日志数据
            logs = context.get_logs() if hasattr(context, 'get_logs') else []
            
            # 如果context没有get_logs方法，尝试从其他地方获取
            if not logs and hasattr(context, '_logs'):
                logs = context._logs
            
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if log_format == 'json':
                result = self._export_json(logs, output_path, include_timestamp, include_level, include_duration)
            elif log_format == 'csv':
                result = self._export_csv(logs, output_path, include_timestamp, include_level, include_duration)
            else:
                result = self._export_txt(logs, output_path, include_timestamp, include_level, include_duration)
            
            if result_variable:
                context.set_variable(result_variable, result)
            
            return ModuleResult(
                success=True,
                message=f"已导出 {result['log_count']} 条日志到 {output_path}",
                data=result
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"导出日志失败: {str(e)}")
    
    def _export_txt(self, logs: list, output_path: str, include_timestamp: bool, 
                    include_level: bool, include_duration: bool) -> dict:
        """导出为TXT格式"""
        lines = []
        for log in logs:
            parts = []
            if include_timestamp and 'timestamp' in log:
                parts.append(f"[{log['timestamp']}]")
            if include_level and 'level' in log:
                parts.append(f"[{log['level'].upper()}]")
            parts.append(log.get('message', ''))
            if include_duration and 'duration' in log and log['duration']:
                parts.append(f"({log['duration']:.2f}ms)")
            lines.append(' '.join(parts))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return {
            "output_path": output_path,
            "log_count": len(logs),
            "format": "txt",
            "file_size": Path(output_path).stat().st_size
        }
    
    def _export_json(self, logs: list, output_path: str, include_timestamp: bool,
                     include_level: bool, include_duration: bool) -> dict:
        """导出为JSON格式"""
        export_logs = []
        for log in logs:
            export_log = {"message": log.get('message', '')}
            if include_timestamp and 'timestamp' in log:
                export_log['timestamp'] = log['timestamp']
            if include_level and 'level' in log:
                export_log['level'] = log['level']
            if include_duration and 'duration' in log:
                export_log['duration'] = log['duration']
            if 'nodeId' in log:
                export_log['nodeId'] = log['nodeId']
            export_logs.append(export_log)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_logs, f, ensure_ascii=False, indent=2)
        
        return {
            "output_path": output_path,
            "log_count": len(logs),
            "format": "json",
            "file_size": Path(output_path).stat().st_size
        }
    
    def _export_csv(self, logs: list, output_path: str, include_timestamp: bool,
                    include_level: bool, include_duration: bool) -> dict:
        """导出为CSV格式"""
        import csv
        
        # 确定列
        columns = []
        if include_timestamp:
            columns.append('timestamp')
        if include_level:
            columns.append('level')
        columns.append('message')
        if include_duration:
            columns.append('duration')
        columns.append('nodeId')
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for log in logs:
                row = {
                    'timestamp': log.get('timestamp', ''),
                    'level': log.get('level', ''),
                    'message': log.get('message', ''),
                    'duration': log.get('duration', ''),
                    'nodeId': log.get('nodeId', '')
                }
                writer.writerow(row)
        
        return {
            "output_path": output_path,
            "log_count": len(logs),
            "format": "csv",
            "file_size": Path(output_path).stat().st_size
        }