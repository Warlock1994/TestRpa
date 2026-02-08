"""计划任务API路由"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.models.scheduled_task import (
    ScheduledTask,
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskExecutionLog
)
from app.services.scheduled_task_manager import scheduled_task_manager


router = APIRouter(prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])


@router.post("", response_model=ScheduledTask)
async def create_scheduled_task(request: ScheduledTaskCreate):
    """创建计划任务"""
    task = ScheduledTask(**request.dict())
    return scheduled_task_manager.create_task(task)


@router.get("", response_model=List[ScheduledTask])
async def list_scheduled_tasks():
    """获取所有计划任务"""
    return scheduled_task_manager.list_tasks()


@router.get("/{task_id}", response_model=ScheduledTask)
async def get_scheduled_task(task_id: str):
    """获取计划任务详情"""
    task = scheduled_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=ScheduledTask)
async def update_scheduled_task(task_id: str, request: ScheduledTaskUpdate):
    """更新计划任务"""
    updates = request.dict(exclude_unset=True)
    task = scheduled_task_manager.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/{task_id}")
async def delete_scheduled_task(task_id: str):
    """删除计划任务"""
    success = scheduled_task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": "任务已删除"}


@router.post("/{task_id}/toggle")
async def toggle_scheduled_task(task_id: str, request: dict):
    """启用/禁用计划任务"""
    enabled = request.get("enabled", False)
    task = scheduled_task_manager.toggle_task(task_id, enabled)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "enabled": task.enabled}


@router.post("/{task_id}/execute")
async def execute_scheduled_task(task_id: str):
    """手动执行计划任务"""
    task = scheduled_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 异步执行任务
    import asyncio
    asyncio.create_task(scheduled_task_manager.execute_task_manually(task_id))
    
    return {"success": True, "message": "任务已开始执行"}


@router.post("/{task_id}/stop")
async def stop_scheduled_task(task_id: str):
    """强制停止正在执行的计划任务"""
    task = scheduled_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    success = await scheduled_task_manager.stop_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="任务未在执行中")
    
    return {"success": True, "message": "任务已停止"}


@router.get("/{task_id}/logs", response_model=List[ScheduledTaskExecutionLog])
async def get_task_logs(task_id: str, limit: int = 100):
    """获取任务执行日志"""
    return scheduled_task_manager.get_task_logs(task_id, limit)


@router.get("/logs/all", response_model=List[ScheduledTaskExecutionLog])
async def get_all_logs(limit: int = 100):
    """获取所有执行日志"""
    return scheduled_task_manager.get_all_logs(limit)


@router.delete("/{task_id}/logs")
async def clear_task_logs(task_id: str):
    """清空任务执行日志"""
    scheduled_task_manager.clear_logs(task_id)
    return {"success": True, "message": "日志已清空"}


@router.delete("/logs/all")
async def clear_all_logs():
    """清空所有执行日志"""
    scheduled_task_manager.clear_logs()
    return {"success": True, "message": "所有日志已清空"}


@router.get("/statistics/summary")
async def get_statistics_summary():
    """获取统计摘要"""
    tasks = scheduled_task_manager.list_tasks()
    
    total_tasks = len(tasks)
    enabled_tasks = sum(1 for task in tasks if task.enabled)
    disabled_tasks = total_tasks - enabled_tasks
    
    total_executions = sum(task.total_executions for task in tasks)
    success_executions = sum(task.success_executions for task in tasks)
    failed_executions = sum(task.failed_executions for task in tasks)
    
    # 按触发器类型统计
    trigger_types = {}
    for task in tasks:
        trigger_type = task.trigger.type
        if trigger_type not in trigger_types:
            trigger_types[trigger_type] = 0
        trigger_types[trigger_type] += 1
    
    return {
        "total_tasks": total_tasks,
        "enabled_tasks": enabled_tasks,
        "disabled_tasks": disabled_tasks,
        "total_executions": total_executions,
        "success_executions": success_executions,
        "failed_executions": failed_executions,
        "success_rate": round(success_executions / total_executions * 100, 2) if total_executions > 0 else 0,
        "trigger_types": trigger_types
    }
