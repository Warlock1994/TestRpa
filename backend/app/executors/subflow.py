"""子流程执行器 - 执行画布中定义的子流程分组"""
from typing import Any

from app.executors import ModuleExecutor, ModuleResult, ExecutionContext, registry


class SubflowExecutor(ModuleExecutor):
    """子流程执行器 - 执行画布中的子流程分组内的模块"""
    
    @property
    def module_type(self) -> str:
        return 'subflow'
    
    async def execute(self, config: dict[str, Any], context: ExecutionContext) -> ModuleResult:
        subflow_name = config.get('subflowName', '')
        subflow_group_id = config.get('subflowGroupId', '')
        
        if not subflow_name and not subflow_group_id:
            return ModuleResult(success=False, error="未选择子流程")
        
        # 子流程的实际执行由 workflow_executor 处理
        # 优先使用名称查找（因为导入后 ID 会变），ID 作为备用
        return ModuleResult(
            success=True, 
            message=f"调用子流程 [{subflow_name or subflow_group_id}]",
            data={
                'subflow_group_id': subflow_group_id,
                'subflow_name': subflow_name
            }
        )


# 注册执行器
registry.register(SubflowExecutor)
