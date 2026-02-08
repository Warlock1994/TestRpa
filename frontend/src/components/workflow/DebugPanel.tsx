import { useState } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import { X, Search, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DebugPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function DebugPanel({ isOpen, onClose }: DebugPanelProps) {
  const variables = useWorkflowStore((state) => state.variables)
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedVars, setExpandedVars] = useState<Set<string>>(new Set())
  const [copiedVar, setCopiedVar] = useState<string | null>(null)

  // 过滤变量
  const filteredVariables = variables.filter(v =>
    v.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 切换变量展开状态
  const toggleExpand = (varName: string) => {
    const newExpanded = new Set(expandedVars)
    if (newExpanded.has(varName)) {
      newExpanded.delete(varName)
    } else {
      newExpanded.add(varName)
    }
    setExpandedVars(newExpanded)
  }

  // 复制变量值
  const copyValue = (varName: string, value: unknown) => {
    const text = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
    navigator.clipboard.writeText(text)
    setCopiedVar(varName)
    setTimeout(() => setCopiedVar(null), 2000)
  }

  // 格式化变量值显示
  const formatValue = (value: unknown, isExpanded: boolean): string => {
    if (value === null) return 'null'
    if (value === undefined) return 'undefined'
    
    const type = typeof value
    
    if (type === 'string') {
      const strValue = value as string
      if (isExpanded) return strValue
      return strValue.length > 50 ? `"${strValue.substring(0, 50)}..."` : `"${strValue}"`
    }
    
    if (type === 'number' || type === 'boolean') {
      return String(value)
    }
    
    if (Array.isArray(value)) {
      if (isExpanded) {
        return JSON.stringify(value, null, 2)
      }
      return `Array(${value.length})`
    }
    
    if (type === 'object') {
      if (isExpanded) {
        return JSON.stringify(value, null, 2)
      }
      const keys = Object.keys(value as Record<string, unknown>)
      return `Object {${keys.slice(0, 3).join(', ')}${keys.length > 3 ? '...' : ''}}`
    }
    
    return String(value)
  }

  // 获取类型颜色
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'string': return 'text-green-600 dark:text-green-400'
      case 'number': return 'text-blue-600 dark:text-blue-400'
      case 'boolean': return 'text-purple-600 dark:text-purple-400'
      case 'array': return 'text-orange-600 dark:text-orange-400'
      case 'object': return 'text-cyan-600 dark:text-cyan-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-200 shadow-2xl z-50 flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <h3 className="font-semibold text-gray-900">变量监控</h3>
          <span className="text-xs text-gray-500">
            ({filteredVariables.length})
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* 搜索框 */}
      <div className="p-3 border-b border-gray-200 bg-gray-50">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索变量名..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* 变量列表 */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 bg-white">
        {filteredVariables.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            {searchTerm ? '无搜索结果' : '暂无变量'}
          </div>
        ) : (
          filteredVariables.map((variable) => {
            const isExpanded = expandedVars.has(variable.name)
            const isComplex = typeof variable.value === 'object' && variable.value !== null
            const isCopied = copiedVar === variable.name

            return (
              <div
                key={variable.name}
                className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:border-blue-300 transition-colors"
              >
                {/* 变量名和类型 */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    {isComplex && (
                      <button
                        onClick={() => toggleExpand(variable.name)}
                        className="flex-shrink-0 p-0.5 hover:bg-gray-200 rounded transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-600" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-600" />
                        )}
                      </button>
                    )}
                    <span className="font-mono text-sm font-semibold text-gray-900 truncate">
                      {variable.name}
                    </span>
                    <span className={cn('text-xs font-medium', getTypeColor(variable.type))}>
                      {variable.type}
                    </span>
                  </div>
                  <button
                    onClick={() => copyValue(variable.name, variable.value)}
                    className="flex-shrink-0 p-1 hover:bg-gray-200 rounded transition-colors"
                    title="复制变量值"
                  >
                    {isCopied ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                </div>

                {/* 变量值 */}
                <div className={cn(
                  'text-sm font-mono break-all',
                  isExpanded ? 'whitespace-pre-wrap' : 'truncate',
                  'text-gray-700'
                )}>
                  {formatValue(variable.value, isExpanded)}
                </div>

                {/* 作用域标签 */}
                {variable.scope && (
                  <div className="mt-2 flex items-center gap-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                      {variable.scope === 'global' ? '全局' : '局部'}
                    </span>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* 底部统计 */}
      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <div className="text-gray-500">字符串</div>
            <div className="font-semibold text-green-600">
              {variables.filter(v => v.type === 'string').length}
            </div>
          </div>
          <div>
            <div className="text-gray-500">数字</div>
            <div className="font-semibold text-blue-600">
              {variables.filter(v => v.type === 'number').length}
            </div>
          </div>
          <div>
            <div className="text-gray-500">对象</div>
            <div className="font-semibold text-cyan-600">
              {variables.filter(v => v.type === 'object' || v.type === 'array').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
