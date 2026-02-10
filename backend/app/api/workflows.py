"""工作流API路由"""
import asyncio
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.workflow import Workflow, ExecutionResult, ExecutionStatus, LogEntry
from app.services.workflow_executor import WorkflowExecutor
from app.services.data_collector import DataExporter
from app.main import sio


router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# 存储工作流和执行状态
workflows_store: dict[str, Workflow] = {}
executions_store: dict[str, WorkflowExecutor] = {}
execution_results: dict[str, ExecutionResult] = {}
execution_data: dict[str, list[dict]] = {}

# 全局变量存储（在工作流执行之间持久化）
global_variables: dict[str, any] = {}


class WorkflowCreate(BaseModel):
    name: str
    nodes: list[dict]
    edges: list[dict]
    variables: list[dict] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    nodes: Optional[list[dict]] = None
    edges: Optional[list[dict]] = None
    variables: Optional[list[dict]] = None


class BrowserConfig(BaseModel):
    type: str = 'msedge'
    executablePath: Optional[str] = None
    userDataDir: Optional[str] = None
    fullscreen: bool = False
    autoCloseBrowser: bool = False
    launchArgs: Optional[str] = None


class ExecuteOptions(BaseModel):
    headless: bool = False
    browserConfig: Optional[BrowserConfig] = None


@router.post("", response_model=dict)
async def create_workflow(data: WorkflowCreate):
    """创建工作流"""
    workflow_id = str(uuid4())
    
    workflow = Workflow(
        id=workflow_id,
        name=data.name,
        nodes=[],
        edges=[],
        variables=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    # 转换节点和边
    from app.models.workflow import WorkflowNode, WorkflowEdge, Variable, Position
    
    for node_data in data.nodes:
        node = WorkflowNode(
            id=node_data['id'],
            type=node_data['type'],
            position=Position(**node_data['position']),
            data=node_data.get('data', {}),
            style=node_data.get('style'),
        )
        workflow.nodes.append(node)
    
    for edge_data in data.edges:
        edge = WorkflowEdge(
            id=edge_data['id'],
            source=edge_data['source'],
            target=edge_data['target'],
            sourceHandle=edge_data.get('sourceHandle'),
            targetHandle=edge_data.get('targetHandle'),
        )
        workflow.edges.append(edge)
    
    for var_data in data.variables:
        var = Variable(**var_data)
        workflow.variables.append(var)
    
    workflows_store[workflow_id] = workflow
    
    return {"id": workflow_id, "message": "工作流创建成功"}


@router.get("", response_model=list[dict])
async def list_workflows():
    """获取工作流列表"""
    return [
        {
            "id": w.id,
            "name": w.name,
            "nodeCount": len(w.nodes),
            "createdAt": w.created_at.isoformat(),
            "updatedAt": w.updated_at.isoformat(),
        }
        for w in workflows_store.values()
    ]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """获取单个工作流"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "position": {"x": n.position.x, "y": n.position.y},
                "data": n.data,
                "style": n.style,
            }
            for n in workflow.nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                "sourceHandle": e.sourceHandle,
                "targetHandle": e.targetHandle,
            }
            for e in workflow.edges
        ],
        "variables": [
            {
                "name": v.name,
                "value": v.value,
                "type": v.type.value,
                "scope": v.scope,
            }
            for v in workflow.variables
        ],
        "createdAt": workflow.created_at.isoformat(),
        "updatedAt": workflow.updated_at.isoformat(),
    }


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    """更新工作流"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    from app.models.workflow import WorkflowNode, WorkflowEdge, Variable, Position
    
    if data.name is not None:
        workflow.name = data.name
    
    if data.nodes is not None:
        workflow.nodes = []
        for node_data in data.nodes:
            node = WorkflowNode(
                id=node_data['id'],
                type=node_data['type'],
                position=Position(**node_data['position']),
                data=node_data.get('data', {}),
                style=node_data.get('style'),
            )
            workflow.nodes.append(node)
    
    if data.edges is not None:
        workflow.edges = []
        for edge_data in data.edges:
            edge = WorkflowEdge(
                id=edge_data['id'],
                source=edge_data['source'],
                target=edge_data['target'],
                sourceHandle=edge_data.get('sourceHandle'),
                targetHandle=edge_data.get('targetHandle'),
            )
            workflow.edges.append(edge)
    
    if data.variables is not None:
        workflow.variables = []
        for var_data in data.variables:
            var = Variable(**var_data)
            workflow.variables.append(var)
    
    workflow.updated_at = datetime.now()
    
    return {"message": "工作流更新成功"}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    if workflow_id not in workflows_store:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    del workflows_store[workflow_id]
    return {"message": "工作流删除成功"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, background_tasks: BackgroundTasks, options: ExecuteOptions = ExecuteOptions()):
    """执行工作流"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    # 检查是否已在执行
    if workflow_id in executions_store:
        executor = executions_store[workflow_id]
        if executor.is_running:
            raise HTTPException(status_code=400, detail="工作流正在执行中")
    
    # 创建执行器
    async def on_log(log: LogEntry):
        # 检查是否有客户端启用了日志接收（延迟导入避免循环依赖）
        from app.main import is_log_enabled
        if not is_log_enabled():
            return
        
        # 判断是否是用户日志（打印日志模块）或系统日志（流程开始/结束）
        is_user_log = log.details.get('is_user_log', False) if log.details else False
        is_system_log = log.details.get('is_system_log', False) if log.details else False
        
        # 调试：打印日志详情
        print(f"[LOG] message={log.message}, is_user_log={is_user_log}, is_system_log={is_system_log}, details={log.details}")
        
        await sio.emit('execution:log', {
            'workflowId': workflow_id,
            'log': {
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'level': log.level.value,
                'nodeId': log.node_id,
                'message': log.message,
                'duration': log.duration,
                'isUserLog': is_user_log,
                'isSystemLog': is_system_log,
            }
        })
    
    async def on_node_start(node_id: str):
        await sio.emit('execution:node_start', {
            'workflowId': workflow_id,
            'nodeId': node_id,
        })
    
    async def on_node_complete(node_id: str, result):
        await sio.emit('execution:node_complete', {
            'workflowId': workflow_id,
            'nodeId': node_id,
            'success': result.success,
            'duration': result.duration,
            'error': result.error,
            # 注意：不发送 input 和 output，因为数据量可能很大
        })
    
    async def on_variable_update(name: str, value):
        # 发送变量更新事件到前端
        # 获取变量类型
        var_type = 'null'
        if value is not None:
            if isinstance(value, bool):
                var_type = 'boolean'
            elif isinstance(value, int) or isinstance(value, float):
                var_type = 'number'
            elif isinstance(value, str):
                var_type = 'string'
            elif isinstance(value, list):
                var_type = 'array'
            elif isinstance(value, dict):
                var_type = 'object'
            else:
                var_type = 'unknown'
        
        await sio.emit('execution:variable_update', {
            'workflowId': workflow_id,
            'name': name,
            'value': value,
            'type': var_type,
        })
    
    async def on_data_row(row: dict):
        await sio.emit('execution:data_row', {
            'workflowId': workflow_id,
            'row': row,
        })
    
    executor = WorkflowExecutor(
        workflow=workflow,
        on_log=on_log,
        on_node_start=on_node_start,
        on_node_complete=on_node_complete,
        on_variable_update=on_variable_update,
        on_data_row=on_data_row,
        headless=options.headless,
        browser_config={
            'type': options.browserConfig.type if options.browserConfig else 'msedge',
            'executablePath': options.browserConfig.executablePath if options.browserConfig else None,
            'userDataDir': options.browserConfig.userDataDir if options.browserConfig else None,
            'fullscreen': options.browserConfig.fullscreen if options.browserConfig else False,
            'launchArgs': options.browserConfig.launchArgs if options.browserConfig else None,
        } if options.browserConfig else None,
    )
    
    # 从全局变量存储中恢复变量
    executor.context.variables.update(global_variables)
    
    executions_store[workflow_id] = executor
    
    # 在后台执行
    async def run_execution():
        await sio.emit('execution:started', {'workflowId': workflow_id})
        
        print(f"[run_execution] 开始执行工作流: {workflow_id}")
        result = await executor.execute()
        print(f"[run_execution] 执行完成，结果: {result.status.value}")
        
        execution_results[workflow_id] = result
        execution_data[workflow_id] = executor.get_collected_data()
        
        # 导出数据
        if execution_data[workflow_id]:
            exporter = DataExporter()
            data_file = exporter.export_to_excel(execution_data[workflow_id])
            result.data_file = data_file
        
        # 如果配置了自动关闭浏览器，则关闭
        print(f"[run_execution] browserConfig: {options.browserConfig}")
        if options.browserConfig:
            print(f"[run_execution] autoCloseBrowser: {options.browserConfig.autoCloseBrowser}")
        
        if options.browserConfig and options.browserConfig.autoCloseBrowser:
            try:
                print(f"[run_execution] 自动关闭浏览器（配置已启用）")
                await executor.cleanup()
            except Exception as e:
                print(f"[run_execution] 关闭浏览器失败: {e}")
        else:
            print(f"[run_execution] 保持浏览器打开（配置已禁用或未配置）")
        
        print(f"[run_execution] 发送 execution:completed 事件")
        # 限制发送的数据量，避免消息过大导致传输失败
        collected_data_to_send = execution_data.get(workflow_id, [])
        if len(collected_data_to_send) > 20:
            collected_data_to_send = collected_data_to_send[:20]  # 只发送前20条
        
        await sio.emit('execution:completed', {
            'workflowId': workflow_id,
            'result': {
                'status': result.status.value,
                'executedNodes': result.executed_nodes,
                'failedNodes': result.failed_nodes,
                'dataFile': result.data_file,
            },
            'collectedData': collected_data_to_send,
        })
        print(f"[run_execution] execution:completed 事件已发送")
        
        # 等待一小段时间确保事件被传输
        await asyncio.sleep(0.1)
        
        # 保存全局变量到持久化存储（在清理执行器之前）
        if workflow_id in executions_store:
            global_variables.update(executions_store[workflow_id].context.variables)
            print(f"[run_execution] 已保存 {len(global_variables)} 个全局变量")
        
        # 清理执行器和临时数据，防止内存泄漏
        if workflow_id in executions_store:
            del executions_store[workflow_id]
        if workflow_id in execution_data:
            del execution_data[workflow_id]
        # 保留 execution_results 一段时间供查询，但限制数量
        if len(execution_results) > 10:
            # 删除最旧的结果
            oldest_key = next(iter(execution_results))
            del execution_results[oldest_key]
    
    background_tasks.add_task(run_execution)
    
    return {"message": "工作流开始执行"}


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    """停止工作流执行"""
    executor = executions_store.get(workflow_id)
    if not executor:
        raise HTTPException(status_code=404, detail="没有正在执行的工作流")
    
    if not executor.is_running:
        raise HTTPException(status_code=400, detail="工作流未在执行")
    
    await executor.stop()
    
    await sio.emit('execution:stopped', {'workflowId': workflow_id})
    
    return {"message": "工作流已停止"}


@router.get("/{workflow_id}/status")
async def get_execution_status(workflow_id: str):
    """获取执行状态"""
    executor = executions_store.get(workflow_id)
    result = execution_results.get(workflow_id)
    
    if executor and executor.is_running:
        return {
            "status": "running",
            "executedNodes": executor.executed_nodes,
            "failedNodes": executor.failed_nodes,
        }
    elif result:
        return {
            "status": result.status.value,
            "executedNodes": result.executed_nodes,
            "failedNodes": result.failed_nodes,
            "dataFile": result.data_file,
        }
    else:
        return {"status": "idle"}


@router.get("/{workflow_id}/data")
async def download_data(workflow_id: str):
    """下载提取的数据"""
    result = execution_results.get(workflow_id)
    
    if not result or not result.data_file:
        raise HTTPException(status_code=404, detail="没有可下载的数据")
    
    file_path = Path(result.data_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="数据文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/import")
async def import_workflow(data: dict):
    """导入工作流"""
    try:
        workflow_id = data.get('id') or str(uuid4())
        
        from app.models.workflow import WorkflowNode, WorkflowEdge, Variable, Position
        
        workflow = Workflow(
            id=workflow_id,
            name=data.get('name', '导入的工作流'),
            nodes=[],
            edges=[],
            variables=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        for node_data in data.get('nodes', []):
            node = WorkflowNode(
                id=node_data['id'],
                type=node_data['type'],
                position=Position(**node_data['position']),
                data=node_data.get('data', {}),
                style=node_data.get('style'),
            )
            workflow.nodes.append(node)
        
        for edge_data in data.get('edges', []):
            edge = WorkflowEdge(
                id=edge_data['id'],
                source=edge_data['source'],
                target=edge_data['target'],
                sourceHandle=edge_data.get('sourceHandle'),
                targetHandle=edge_data.get('targetHandle'),
            )
            workflow.edges.append(edge)
        
        # 导入变量（如果有）
        for var_data in data.get('variables', []):
            var = Variable(**var_data)
            workflow.variables.append(var)
            # 如果是全局变量，同时添加到全局变量存储中
            if var.scope == 'global':
                global_variables[var.name] = var.value
                print(f"[import_workflow] 导入全局变量: {var.name} = {var.value}")
        
        workflows_store[workflow_id] = workflow
        
        return {"id": workflow_id, "message": "工作流导入成功"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.get("/{workflow_id}/export")
async def export_workflow(workflow_id: str):
    """导出工作流"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "position": {"x": n.position.x, "y": n.position.y},
                "data": n.data,
                "style": n.style,
            }
            for n in workflow.nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                "sourceHandle": e.sourceHandle,
                "targetHandle": e.targetHandle,
            }
            for e in workflow.edges
        ],
        "variables": [
            {
                "name": v.name,
                "value": v.value,
                "type": v.type.value,
                "scope": v.scope,
            }
            for v in workflow.variables
        ],
        "createdAt": workflow.created_at.isoformat(),
        "updatedAt": workflow.updated_at.isoformat(),
    }


@router.get("/{workflow_id}/export-playwright")
async def export_workflow_playwright(workflow_id: str):
    """导出工作流为 Playwright Python 代码"""
    workflow = workflows_store.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    from app.services.playwright_exporter import export_workflow_to_playwright
    
    # 构建工作流数据
    workflow_data = {
        "id": workflow.id,
        "name": workflow.name,
        "nodes": [
            {
                "id": n.id,
                "type": n.type,
                "position": {"x": n.position.x, "y": n.position.y},
                "data": n.data,
            }
            for n in workflow.nodes
        ],
        "edges": [
            {
                "id": e.id,
                "source": e.source,
                "target": e.target,
                "sourceHandle": e.sourceHandle,
                "targetHandle": e.targetHandle,
            }
            for e in workflow.edges
        ],
        "variables": [
            {
                "name": v.name,
                "value": v.value,
                "type": v.type.value,
            }
            for v in workflow.variables
        ],
    }
    
    # 生成 Python 代码
    python_code = export_workflow_to_playwright(workflow_data)
    
    return {
        "code": python_code,
        "filename": f"{workflow.name.replace(' ', '_')}_playwright.py",
    }


@router.get("/global-variables")
async def get_global_variables():
    """获取所有全局变量"""
    return {
        "variables": global_variables,
        "count": len(global_variables)
    }


@router.delete("/global-variables")
async def clear_global_variables():
    """清空所有全局变量"""
    global_variables.clear()
    return {"message": "全局变量已清空"}


@router.delete("/global-variables/{variable_name}")
async def delete_global_variable(variable_name: str):
    """删除指定的全局变量"""
    if variable_name in global_variables:
        del global_variables[variable_name]
        return {"message": f"变量 {variable_name} 已删除"}
    else:
        raise HTTPException(status_code=404, detail="变量不存在")
