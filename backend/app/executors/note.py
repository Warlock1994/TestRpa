"""便签模块执行器 - 画布上的注释/便签"""
from .base import ModuleExecutor, ExecutionContext, ModuleResult, register_executor


@register_executor
class NoteExecutor(ModuleExecutor):
    """便签模块执行器 - 仅用于画布上的注释，不执行任何操作"""
    
    @property
    def module_type(self) -> str:
        return 'note'
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        # 便签模块不执行任何操作，仅作为画布上的注释
        return ModuleResult(success=True, message="便签（跳过）")
