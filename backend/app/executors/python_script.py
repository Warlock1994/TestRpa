"""Python脚本执行模块"""
import asyncio
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import (
    ModuleExecutor,
    ExecutionContext,
    ModuleResult,
    register_executor,
)


@register_executor
class PythonScriptExecutor(ModuleExecutor):
    """Python脚本执行模块执行器"""
    
    @property
    def module_type(self) -> str:
        return "python_script"
    
    async def execute(self, config: dict, context: ExecutionContext) -> ModuleResult:
        """
        执行Python脚本
        
        配置参数:
        - scriptContent: 脚本内容（直接输入）
        - scriptPath: 脚本文件路径（从文件读取）
        - scriptMode: 脚本模式 ('content' 或 'file')
        - pythonPath: Python解释器路径（可选，默认使用内置Python3.13）
        - useBuiltinPython: 是否使用内置Python（默认True）
        - scriptArgs: 脚本参数（可选）
        - workingDir: 工作目录（可选）
        - timeout: 超时时间（秒，默认60）
        - captureOutput: 是否捕获输出（默认True）
        - resultVariable: 结果变量名（可选）
        - stdoutVariable: 标准输出变量名（可选）
        - stderrVariable: 标准错误变量名（可选）
        - returnCodeVariable: 返回码变量名（可选）
        """
        
        script_mode = config.get('scriptMode', 'content')
        script_content = context.resolve_value(config.get('scriptContent', ''))
        script_path = context.resolve_value(config.get('scriptPath', ''))
        use_builtin_python = config.get('useBuiltinPython', True)
        python_path = context.resolve_value(config.get('pythonPath', ''))
        script_args = context.resolve_value(config.get('scriptArgs', ''))
        working_dir = context.resolve_value(config.get('workingDir', ''))
        timeout = int(config.get('timeout', 60))
        capture_output = config.get('captureOutput', True)
        
        result_variable = config.get('resultVariable', '')
        stdout_variable = config.get('stdoutVariable', '')
        stderr_variable = config.get('stderrVariable', '')
        return_code_variable = config.get('returnCodeVariable', '')
        
        try:
            # 确定Python解释器路径
            if use_builtin_python:
                # 使用内置Python3.13
                project_root = Path(__file__).parent.parent.parent.parent
                builtin_python = project_root / 'Python313' / 'python.exe'
                if not builtin_python.exists():
                    return ModuleResult(
                        success=False,
                        error=f"内置Python不存在: {builtin_python}"
                    )
                python_executable = str(builtin_python)
            elif python_path:
                # 使用用户指定的Python
                if not os.path.exists(python_path):
                    return ModuleResult(
                        success=False,
                        error=f"指定的Python路径不存在: {python_path}"
                    )
                python_executable = python_path
            else:
                # 使用系统Python
                python_executable = sys.executable
            
            # 准备脚本文件
            temp_script = None
            if script_mode == 'content':
                # 从内容创建临时脚本文件
                if not script_content:
                    return ModuleResult(success=False, error="脚本内容不能为空")
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.py',
                    delete=False,
                    encoding='utf-8'
                ) as f:
                    f.write(script_content)
                    temp_script = f.name
                    script_file = temp_script
            else:
                # 从文件读取
                if not script_path:
                    return ModuleResult(success=False, error="脚本文件路径不能为空")
                
                if not os.path.exists(script_path):
                    return ModuleResult(
                        success=False,
                        error=f"脚本文件不存在: {script_path}"
                    )
                script_file = script_path
            
            # 准备命令
            cmd = [python_executable, script_file]
            
            # 添加脚本参数
            if script_args:
                # 支持空格分隔的参数
                args_list = script_args.split()
                cmd.extend(args_list)
            
            # 准备工作目录
            cwd = working_dir if working_dir and os.path.exists(working_dir) else None
            
            # 执行脚本
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    cwd=cwd,
                    env=os.environ.copy()
                )
                
                # 等待执行完成（带超时）
                try:
                    stdout_data, stderr_data = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    return_code = process.returncode
                except asyncio.TimeoutError:
                    # 超时，终止进程
                    try:
                        process.kill()
                        await process.wait()
                    except:
                        pass
                    
                    return ModuleResult(
                        success=False,
                        error=f"脚本执行超时（{timeout}秒）"
                    )
                
                # 解码输出
                stdout_text = stdout_data.decode('utf-8', errors='ignore') if stdout_data else ''
                stderr_text = stderr_data.decode('utf-8', errors='ignore') if stderr_data else ''
                
                # 保存到变量
                if stdout_variable:
                    context.set_variable(stdout_variable, stdout_text)
                if stderr_variable:
                    context.set_variable(stderr_variable, stderr_text)
                if return_code_variable:
                    context.set_variable(return_code_variable, return_code)
                if result_variable:
                    result_data = {
                        'stdout': stdout_text,
                        'stderr': stderr_text,
                        'returnCode': return_code,
                        'success': return_code == 0
                    }
                    context.set_variable(result_variable, result_data)
                
                # 判断执行结果
                if return_code == 0:
                    return ModuleResult(
                        success=True,
                        message=f"脚本执行成功（返回码: {return_code}）",
                        data={
                            'stdout': stdout_text,
                            'stderr': stderr_text,
                            'returnCode': return_code
                        }
                    )
                else:
                    return ModuleResult(
                        success=False,
                        error=f"脚本执行失败（返回码: {return_code}）",
                        data={
                            'stdout': stdout_text,
                            'stderr': stderr_text,
                            'returnCode': return_code
                        }
                    )
                
            finally:
                # 清理临时文件
                if temp_script and os.path.exists(temp_script):
                    try:
                        os.unlink(temp_script)
                    except:
                        pass
        
        except Exception as e:
            return ModuleResult(success=False, error=f"执行失败: {str(e)}")
