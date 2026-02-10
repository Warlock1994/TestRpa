import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { cn } from '@/lib/utils'
import type { NodeData } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { Globe } from 'lucide-react'
// 从 ModuleSidebar 导入统一的图标映射
import { moduleIcons } from './ModuleSidebar'
// 导入统一的颜色映射
import { moduleColors } from './moduleColors'

function ModuleNodeComponent({ data, selected }: NodeProps) {
  const nodeData = data as NodeData
  // 移除执行动画以提升性能
  const isDisabled = nodeData.disabled === true
  const isHighlighted = nodeData.isHighlighted === true
  
  // 获取全局配置的连接点尺寸
  const handleSize = useGlobalConfigStore((state) => state.config.display?.handleSize || 12)
  
  const Icon = moduleIcons[nodeData.moduleType] || Globe
  const colorClass = moduleColors[nodeData.moduleType] || 'border-gray-500 bg-gray-50'
  
  // 获取配置摘要
  const getSummary = () => {
    if (nodeData.url) return nodeData.url as string
    if (nodeData.selector) return nodeData.selector as string
    if (nodeData.text) return nodeData.text as string
    if (nodeData.logMessage) return nodeData.logMessage as string
    if (nodeData.variableName) return `→ ${nodeData.variableName}`
    if (nodeData.userPrompt) return nodeData.userPrompt as string
    if (nodeData.requestUrl) return nodeData.requestUrl as string
    return ''
  }
  
  // 截断文本
  const truncateText = (text: string, maxLen: number) => {
    if (text.length <= maxLen) return text
    return text.slice(0, maxLen) + '...'
  }
  
  const summary = truncateText(getSummary(), 30)
  const customName = nodeData.name as string | undefined

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-sm min-w-[180px] max-w-[280px] transition-all duration-200 hover:shadow-lg',
        isDisabled ? 'border-gray-300 bg-gray-100 dark:bg-gray-800 opacity-50' : colorClass,
        selected && 'ring-2 ring-primary ring-offset-2 shadow-lg scale-[1.02]',
        isHighlighted && 'ring-4 ring-amber-500 ring-offset-2 shadow-2xl scale-105 animate-pulse border-amber-500'
      )}
    >
      {/* 禁用标记 */}
      {isDisabled && (
        <div className="absolute -top-2 -right-2 bg-gray-500 text-white text-[10px] px-1.5 py-0.5 rounded-full animate-pulse">
          已禁用
        </div>
      )}
      
      {/* 输入连接点 */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-400 !border-2 !border-white"
        style={{ width: `${handleSize}px`, height: `${handleSize}px` }}
      />
      
      {/* 节点内容 */}
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5" />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate">
            {nodeData.label}
            {customName && (
              <span className="text-amber-600 dark:text-amber-400 font-normal ml-1">
                ({customName})
              </span>
            )}
          </div>
          {summary && (
            <div className="text-xs opacity-75 truncate mt-0.5">
              {summary}
            </div>
          )}
        </div>
      </div>
      
      {/* 输出连接点 */}
      {nodeData.moduleType === 'condition' || nodeData.moduleType === 'face_recognition' ? (
        // 条件判断/人脸识别：绿色=true/匹配，红色=false/不匹配，右侧=异常
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            className="!bg-green-500 !border-2 !border-white"
            style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'face_recognition' ? '匹配' : '是'}
          </div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            className="!bg-red-500 !border-2 !border-white"
            style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>
            {nodeData.moduleType === 'face_recognition' ? '不匹配' : '否'}
          </div>
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      ) : nodeData.moduleType === 'loop' || nodeData.moduleType === 'foreach' ? (
        // 循环模块：绿色=循环体，红色=循环结束后，右侧=异常
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="loop"
            className="!bg-green-500 !border-2 !border-white"
            style={{ left: '30%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-green-600 font-medium" style={{ left: '30%', transform: 'translateX(-50%)' }}>循环</div>
          <Handle
            type="source"
            position={Position.Bottom}
            id="done"
            className="!bg-red-500 !border-2 !border-white"
            style={{ left: '70%', width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          <div className="absolute -bottom-5 text-[10px] text-red-600 font-medium" style={{ left: '70%', transform: 'translateX(-50%)' }}>完成</div>
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      ) : (
        // 普通模块：底部=正常流程，右侧=异常处理
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            className="!bg-gray-400 !border-2 !border-white"
            style={{ width: `${handleSize}px`, height: `${handleSize}px` }}
          />
          {/* 异常处理连接点 */}
          <Handle
            type="source"
            position={Position.Right}
            id="error"
            className="!bg-orange-500 !border-2 !border-white"
            style={{ top: '50%', width: `${handleSize * 0.83}px`, height: `${handleSize * 0.83}px` }}
          />
        </>
      )}
    </div>
  )
}

export const ModuleNode = memo(ModuleNodeComponent)
