import { useState } from 'react'
import { X, Clock, CheckCircle2, XCircle, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NodeExecution {
  nodeId: string
  nodeName: string
  nodeType: string
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  startTime?: number
  endTime?: number
  duration?: number
  input?: Record<string, unknown>
  output?: unknown
  error?: string
}

interface ExecutionDetailsPanelProps {
  isOpen: boolean
  onClose: () => void
  executions: NodeExecution[]
}

export function ExecutionDetailsPanel({ isOpen, onClose, executions }: ExecutionDetailsPanelProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [filter, setFilter] = useState<'all' | 'success' | 'error'>('all')

  // 切换节点展开状态
  const toggleExpand = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  // 过滤执行记录
  const filteredExecutions = executions.filter(exec => {
    if (filter === 'all') return true
    if (filter === 'success') return exec.status === 'success'
    if (filter === 'error') return exec.status === 'error'
    return true
  })

  // 获取状态图标
  const getStatusIcon = (status: NodeExecution['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-600" />
      case 'running':
        return <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      case 'skipped':
        return <AlertCircle className="w-4 h-4 text-gray-400" />
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
    }
  }

  // 获取状态颜色
  const getStatusColor = (status: NodeExecution['status']) => {
    switch (status) {
      case 'success': return 'bg-green-50 border-green-200'
      case 'error': return 'bg-red-50 border-red-200'
      case 'running': return 'bg-blue-50 border-blue-200'
      case 'skipped': return 'bg-gray-50 border-gray-200'
      default: return 'bg-gray-50 border-gray-200'
    }
  }

  // 格式化时间
  const formatDuration = (ms?: number) => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  // 格式化JSON
  const formatJSON = (data: unknown) => {
    try {
      return JSON.stringify(data, null, 2)
    } catch {
      return String(data)
    }
  }

  if (!isOpen) return null

  const successCount = executions.filter(e => e.status === 'success').length
  const errorCount = executions.filter(e => e.status === 'error').length
  const totalDuration = executions.reduce((sum, e) => sum + (e.duration || 0), 0)

  return (
    <div className="fixed right-0 top-0 h-full w-[600px] bg-white border-l border-gray-200 shadow-2xl z-50 flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50">
        <div>
          <h3 className="font-semibold text-gray-900">执行详情</h3>
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
            <span>总计: {executions.length}</span>
            <span className="text-green-600">成功: {successCount}</span>
            <span className="text-red-600">失败: {errorCount}</span>
            <span>耗时: {formatDuration(totalDuration)}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-white/80 rounded transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* 过滤器 */}
      <div className="p-3 border-b border-gray-200 flex gap-2 bg-gray-50">
        <button
          onClick={() => setFilter('all')}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg transition-colors',
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
          )}
        >
          全部 ({executions.length})
        </button>
        <button
          onClick={() => setFilter('success')}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg transition-colors',
            filter === 'success'
              ? 'bg-green-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
          )}
        >
          成功 ({successCount})
        </button>
        <button
          onClick={() => setFilter('error')}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg transition-colors',
            filter === 'error'
              ? 'bg-red-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
          )}
        >
          失败 ({errorCount})
        </button>
      </div>

      {/* 执行列表 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-gray-50">
        {filteredExecutions.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            暂无执行记录
          </div>
        ) : (
          filteredExecutions.map((exec) => {
            const isExpanded = expandedNodes.has(exec.nodeId)

            return (
              <div
                key={exec.nodeId}
                className={cn(
                  'rounded-lg p-3 border transition-colors',
                  getStatusColor(exec.status)
                )}
              >
                {/* 节点基本信息 */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <button
                      onClick={() => toggleExpand(exec.nodeId)}
                      className="flex-shrink-0 p-0.5 hover:bg-white/70 rounded transition-colors mt-0.5"
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-600" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-600" />
                      )}
                    </button>
                    <div className="flex-shrink-0 mt-0.5">
                      {getStatusIcon(exec.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">
                        {exec.nodeName}
                      </div>
                      <div className="text-xs text-gray-600 mt-0.5">
                        {exec.nodeType}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-600 flex-shrink-0">
                    <Clock className="w-3 h-3" />
                    {formatDuration(exec.duration)}
                  </div>
                </div>

                {/* 展开的详细信息 */}
                {isExpanded && (
                  <div className="mt-3 space-y-3 pt-3 border-t border-gray-200">
                    {/* 输入参数 */}
                    {exec.input && Object.keys(exec.input).length > 0 && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">
                          输入参数:
                        </div>
                        <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto text-gray-900">
                          {formatJSON(exec.input)}
                        </pre>
                      </div>
                    )}

                    {/* 输出结果 */}
                    {exec.output !== undefined && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">
                          输出结果:
                        </div>
                        <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto text-gray-900">
                          {formatJSON(exec.output)}
                        </pre>
                      </div>
                    )}

                    {/* 错误信息 */}
                    {exec.error && (
                      <div>
                        <div className="text-xs font-medium text-red-700 mb-1">
                          错误信息:
                        </div>
                        <div className="text-xs bg-red-50 text-red-900 p-2 rounded border border-red-200">
                          {exec.error}
                        </div>
                      </div>
                    )}

                    {/* 时间信息 */}
                    {exec.startTime && (
                      <div className="text-xs text-gray-600">
                        开始时间: {new Date(exec.startTime).toLocaleTimeString()}
                        {exec.endTime && ` | 结束时间: ${new Date(exec.endTime).toLocaleTimeString()}`}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
