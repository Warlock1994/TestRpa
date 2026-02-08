import { memo, useState, useCallback } from 'react'
import { Handle, Position, type NodeProps, useReactFlow } from '@xyflow/react'
import { Workflow, GripVertical } from 'lucide-react'
import { useGlobalConfigStore } from '@/store/globalConfigStore'

export interface SubflowHeaderNodeData {
  label: string
  moduleType: 'subflow_header'
  subflowName?: string // 子流程名称（用于调用）
  originalGroupId?: string // 原分组ID（用于转换时的引用）
}

export const SubflowHeaderNode = memo(({ id, data, selected }: NodeProps) => {
  const nodeData = data as unknown as SubflowHeaderNodeData
  const { setNodes, getNodes } = useReactFlow()
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(nodeData.label || '')
  
  // 获取全局配置的连接点尺寸
  const handleSize = useGlobalConfigStore((state) => state.config.display?.handleSize || 12)

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true)
    setEditValue(nodeData.label || '')
  }, [nodeData.label])

  const handleBlur = useCallback(() => {
    setIsEditing(false)
    const oldName = nodeData.subflowName || nodeData.label || ''
    const newName = editValue
    
    // 检查是否有重名
    if (newName) {
      const nodes = getNodes()
      const duplicates = nodes.filter(n => {
        if (n.id === id) return false
        if (n.type === 'groupNode' && n.data.isSubflow && n.data.subflowName === newName) return true
        if (n.type === 'subflowHeaderNode' && n.data.subflowName === newName) return true
        return false
      })
      
      if (duplicates.length > 0) {
        alert(`⚠️ 警告：已存在名为「${newName}」的子流程！\n\n这会导致调用时无法确定执行哪一个，请使用唯一的名称。`)
        setEditValue(oldName)
        return
      }
    }
    
    // 更新当前节点
    nodeData.label = editValue
    nodeData.subflowName = editValue
    
    // 如果名称改变了，同步更新所有引用该子流程的模块
    if (oldName && oldName !== newName) {
      setNodes((nodes) =>
        nodes.map((node) => {
          // 更新引用了旧名称的子流程模块
          if (node.data.moduleType === 'subflow' && node.data.subflowName === oldName) {
            return {
              ...node,
              data: {
                ...node.data,
                subflowName: newName,
              },
            }
          }
          return node
        })
      )
    }
  }, [editValue, nodeData, setNodes, id, getNodes])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleBlur()
    }
    if (e.key === 'Escape') {
      setIsEditing(false)
      setEditValue(nodeData.label || '')
    }
  }, [handleBlur, nodeData.label])

  return (
    <div
      className={`relative px-4 py-3 rounded-lg border-2 transition-all cursor-move ${
        selected 
          ? 'border-emerald-500 shadow-lg shadow-emerald-500/20' 
          : 'border-emerald-400 shadow-md'
      }`}
      style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%)',
        minWidth: '280px',
      }}
    >
      {/* 顶部装饰线 */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-400 via-emerald-500 to-emerald-400 rounded-t-lg" />
      
      {/* 主体内容 */}
      <div className="flex items-center gap-3">
        {/* 图标 */}
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-md">
          <Workflow className="w-5 h-5 text-white" />
        </div>
        
        {/* 标题区域 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <GripVertical className="w-3 h-3 text-emerald-600 opacity-70" />
            <span className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider">
              子流程定义
            </span>
          </div>
          
          {isEditing ? (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              className="w-full bg-white/80 border border-emerald-300 rounded px-2 py-1 text-sm font-semibold text-emerald-900 outline-none focus:ring-2 focus:ring-emerald-500"
              autoFocus
              onClick={(e) => e.stopPropagation()}
              placeholder="子流程名称"
            />
          ) : (
            <div
              className="text-sm font-semibold text-emerald-900 truncate cursor-text"
              onDoubleClick={handleDoubleClick}
            >
              📦 {nodeData.label || '未命名子流程'}
            </div>
          )}
        </div>
      </div>
      
      {/* 底部提示 */}
      <div className="mt-2 pt-2 border-t border-emerald-200/50">
        <p className="text-[10px] text-emerald-700 opacity-80">
          ⬇️ 连接到子流程的第一个模块
        </p>
      </div>
      
      {/* 连接点 - 只有底部输出，没有顶部输入 */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-emerald-500 !border-2 !border-white"
        style={{ bottom: -6, width: `${handleSize}px`, height: `${handleSize}px` }}
      />
    </div>
  )
})

SubflowHeaderNode.displayName = 'SubflowHeaderNode'
