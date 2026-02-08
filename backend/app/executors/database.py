"""数据库操作执行器"""
import pymysql
from pymysql.cursors import DictCursor
from typing import Dict, Any, Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)
from .type_utils import to_int


# 全局数据库连接池（存储在context中）
def get_db_connections(context: ExecutionContext) -> Dict[str, pymysql.Connection]:
    """获取数据库连接池"""
    if not hasattr(context, '_db_connections'):
        context._db_connections = {}
    return context._db_connections


@register_executor
class DbConnectExecutor(ModuleExecutor):
    """连接数据库"""
    
    @property
    def module_type(self) -> str:
        return "db_connect"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        host = context.resolve_value(config.get('host', 'localhost'))
        port = to_int(config.get('port', 3306), 3306, context)
        user = context.resolve_value(config.get('user', 'root'))
        password = context.resolve_value(config.get('password', ''))
        database = context.resolve_value(config.get('database', ''))
        charset = context.resolve_value(config.get('charset', 'utf8mb4'))
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        
        connections = get_db_connections(context)
        
        try:
            # 如果已有同名连接，先关闭
            if connection_name in connections:
                try:
                    connections[connection_name].close()
                except:
                    pass
                del connections[connection_name]
            
            # 创建新连接
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database if database else None,
                charset=charset,
                cursorclass=DictCursor,
                autocommit=True
            )
            
            connections[connection_name] = conn
            
            db_info = f"{host}:{port}"
            if database:
                db_info += f"/{database}"
            
            return ModuleResult(
                success=True,
                message=f"成功连接到数据库 {db_info}",
                data={"connectionName": connection_name}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"连接数据库失败: {str(e)}")


@register_executor
class DbQueryExecutor(ModuleExecutor):
    """查询数据（SELECT）"""
    
    @property
    def module_type(self) -> str:
        return "db_query"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        sql = context.resolve_value(config.get('sql', ''))
        variable_name = context.resolve_value(config.get('variableName', ''))
        single_row_raw = config.get('singleRow', False)
        # 支持变量引用
        if isinstance(single_row_raw, str):
            single_row_raw = context.resolve_value(single_row_raw)
        single_row = single_row_raw in [True, 'true', 'True', '1', 1]
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(
                success=False, 
                error=f"数据库连接 '{connection_name}' 不存在，请先使用「连接数据库」模块"
            )
        
        if not sql:
            return ModuleResult(success=False, error="SQL语句不能为空")
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                if single_row:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            
            # 保存到变量
            if variable_name:
                context.variables[variable_name] = result
            
            row_count = 1 if single_row and result else len(result) if result else 0
            
            return ModuleResult(
                success=True,
                message=f"查询成功，返回 {row_count} 条记录",
                data={"rowCount": row_count, "data": result}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"查询失败: {str(e)}")


@register_executor
class DbExecuteExecutor(ModuleExecutor):
    """执行SQL（通用）"""
    
    @property
    def module_type(self) -> str:
        return "db_execute"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        sql = context.resolve_value(config.get('sql', ''))
        variable_name = context.resolve_value(config.get('variableName', ''))
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(
                success=False, 
                error=f"数据库连接 '{connection_name}' 不存在，请先使用「连接数据库」模块"
            )
        
        if not sql:
            return ModuleResult(success=False, error="SQL语句不能为空")
        
        try:
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql)
                
                # 尝试获取结果（如果是SELECT语句）
                try:
                    result = cursor.fetchall()
                except:
                    result = None
            
            # 保存影响行数到变量
            if variable_name:
                context.variables[variable_name] = affected_rows
            
            return ModuleResult(
                success=True,
                message=f"SQL执行成功，影响 {affected_rows} 行",
                data={"affectedRows": affected_rows, "data": result}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"SQL执行失败: {str(e)}")


@register_executor
class DbInsertExecutor(ModuleExecutor):
    """插入数据"""
    
    @property
    def module_type(self) -> str:
        return "db_insert"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        table = context.resolve_value(config.get('table', ''))
        data = config.get('data', {})
        variable_name = context.resolve_value(config.get('variableName', ''))
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(
                success=False, 
                error=f"数据库连接 '{connection_name}' 不存在，请先使用「连接数据库」模块"
            )
        
        if not table:
            return ModuleResult(success=False, error="请指定表名")
        
        try:
            # 解析数据
            if isinstance(data, str):
                import json
                data = json.loads(context.resolve_value(data))
            
            # 解析数据中的变量
            resolved_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    resolved_data[key] = context.resolve_value(value)
                else:
                    resolved_data[key] = value
            
            if not resolved_data:
                return ModuleResult(success=False, error="插入数据不能为空")
            
            # 构建INSERT语句
            columns = ', '.join(f'`{k}`' for k in resolved_data.keys())
            placeholders = ', '.join(['%s'] * len(resolved_data))
            sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
            
            with conn.cursor() as cursor:
                cursor.execute(sql, list(resolved_data.values()))
                last_id = cursor.lastrowid
            
            # 保存插入ID到变量
            if variable_name:
                context.variables[variable_name] = last_id
            
            return ModuleResult(
                success=True,
                message=f"插入成功，ID: {last_id}",
                data={"lastInsertId": last_id}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"插入失败: {str(e)}")


@register_executor
class DbUpdateExecutor(ModuleExecutor):
    """更新数据"""
    
    @property
    def module_type(self) -> str:
        return "db_update"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        table = context.resolve_value(config.get('table', ''))
        data = config.get('data', {})
        where = context.resolve_value(config.get('where', ''))
        variable_name = context.resolve_value(config.get('variableName', ''))
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(
                success=False, 
                error=f"数据库连接 '{connection_name}' 不存在，请先使用「连接数据库」模块"
            )
        
        if not table:
            return ModuleResult(success=False, error="请指定表名")
        
        try:
            # 解析数据
            if isinstance(data, str):
                import json
                data = json.loads(context.resolve_value(data))
            
            # 解析数据中的变量
            resolved_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    resolved_data[key] = context.resolve_value(value)
                else:
                    resolved_data[key] = value
            
            if not resolved_data:
                return ModuleResult(success=False, error="更新数据不能为空")
            
            # 构建UPDATE语句
            set_clause = ', '.join(f'`{k}` = %s' for k in resolved_data.keys())
            sql = f"UPDATE `{table}` SET {set_clause}"
            if where:
                sql += f" WHERE {where}"
            
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql, list(resolved_data.values()))
            
            # 保存影响行数到变量
            if variable_name:
                context.variables[variable_name] = affected_rows
            
            return ModuleResult(
                success=True,
                message=f"更新成功，影响 {affected_rows} 行",
                data={"affectedRows": affected_rows}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"更新失败: {str(e)}")


@register_executor
class DbDeleteExecutor(ModuleExecutor):
    """删除数据"""
    
    @property
    def module_type(self) -> str:
        return "db_delete"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        table = context.resolve_value(config.get('table', ''))
        where = context.resolve_value(config.get('where', ''))
        variable_name = context.resolve_value(config.get('variableName', ''))
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(
                success=False, 
                error=f"数据库连接 '{connection_name}' 不存在，请先使用「连接数据库」模块"
            )
        
        if not table:
            return ModuleResult(success=False, error="请指定表名")
        
        if not where:
            return ModuleResult(success=False, error="删除操作必须指定WHERE条件，防止误删全表数据")
        
        try:
            sql = f"DELETE FROM `{table}` WHERE {where}"
            
            with conn.cursor() as cursor:
                affected_rows = cursor.execute(sql)
            
            # 保存影响行数到变量
            if variable_name:
                context.variables[variable_name] = affected_rows
            
            return ModuleResult(
                success=True,
                message=f"删除成功，影响 {affected_rows} 行",
                data={"affectedRows": affected_rows}
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"删除失败: {str(e)}")


@register_executor
class DbCloseExecutor(ModuleExecutor):
    """关闭数据库连接"""
    
    @property
    def module_type(self) -> str:
        return "db_close"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        connection_name = context.resolve_value(config.get('connectionName', 'default'))
        
        connections = get_db_connections(context)
        conn = connections.get(connection_name)
        
        if not conn:
            return ModuleResult(success=True, message=f"连接 '{connection_name}' 不存在或已关闭")
        
        try:
            conn.close()
            del connections[connection_name]
            
            return ModuleResult(
                success=True,
                message=f"数据库连接 '{connection_name}' 已关闭"
            )
        except Exception as e:
            return ModuleResult(success=False, error=f"关闭连接失败: {str(e)}")
