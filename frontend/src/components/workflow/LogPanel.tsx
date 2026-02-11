import { useWorkflowStore, type DataRow } from '@/store/workflowStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { 
  Trash2, 
  Download, 
  ChevronUp, 
  ChevronDown, 
  Plus, 
  X, 
  FileSpreadsheet,
  Edit2,
  Check,
  FileText,
  Variable,
  Search,
  Filter,
  ImageIcon,
  Database,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import type { LogLevel, VariableType } from '@/types'
import { ExcelAssetsPanel } from './ExcelAssetsPanel'
import { ImageAssetsPanel } from './ImageAssetsPanel'

type LogFilterType = 'all' | LogLevel

interface LogPanelProps {
  onLogClick?: (nodeId: string) => void
}

export function LogPanel({ onLogClick }: LogPanelProps) {
  const logs = useWorkflowStore((state) => state.logs)
  const clearLogs = useWorkflowStore((state) => state.clearLogs)
  const selectNode = useWorkflowStore((state) => state.selectNode)
  const variables = useWorkflowStore((state) => state.variables)
  const addVariable = useWorkflowStore((state) => state.addVariable)
  const updateVariable = useWorkflowStore((state) => state.updateVariable)
  const deleteVariable = useWorkflowStore((state) => state.deleteVariable)
  const renameVariable = useWorkflowStore((state) => state.renameVariable)
  const findVariableUsages = useWorkflowStore((state) => state.findVariableUsages)
  const replaceVariableReferences = useWorkflowStore((state) => state.replaceVariableReferences)
  const { 
    collectedData, 
    setCollectedData,
    updateDataRow, 
    deleteDataRow, 
    addDataRow,
    clearCollectedData,
    name: workflowName,
    dataAssets,
    bottomPanelTab: activeTab,
    setBottomPanelTab: setActiveTab,
    verboseLog,
    setVerboseLog,
    maxLogCount,
    setMaxLogCount,
  } = useWorkflowStore()

  const { alert, ConfirmDialog } = useConfirm()
  const logEndRef = useRef<HTMLDivElement>(null)

  const [isCollapsed, setIsCollapsed] = useState(false)
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [newColumnName, setNewColumnName] = useState('')
  const [isAddingColumn, setIsAddingColumn] = useState(false)
  
  // 日志搜索和筛选
  const [logSearchQuery, setLogSearchQuery] = useState('')
  const [logLevelFilter, setLogLevelFilter] = useState<LogFilterType>('all')
  
  // 变量相关状态
  const [isAddingVar, setIsAddingVar] = useState(false)
  const [newVarName, setNewVarName] = useState('')
  const [newVarValue, setNewVarValue] = useState('')
  const [newVarType, setNewVarType] = useState<VariableType>('string')
  const [editingVar, setEditingVar] = useState<string | null>(null)
  const [editVarValue, setEditVarValue] = useState('')
  
  // 变量名编辑状态
  const [editingVarName, setEditingVarName] = useState<string | null>(null)
  const [editVarNameValue, setEditVarNameValue] = useState('')
  const [renameDialog, setRenameDialog] = useState<{
    oldName: string
    newName: string
    usageCount: number
  } | null>(null)

  // 过滤后的日志
  const filteredLogs = useMemo(() => {
    const filtered = logs.filter(log => {
      // 类型筛选
      if (logLevelFilter !== 'all' && log.level !== logLevelFilter) {
        return false
      }
      // 搜索筛选
      if (logSearchQuery.trim()) {
        const query = logSearchQuery.toLowerCase()
        return log.message.toLowerCase().includes(query)
      }
      return true
    })
    // 只显示最近的日志，避免渲染过多DOM
    return filtered.slice(-maxLogCount)
  }, [logs, logLevelFilter, logSearchQuery, maxLogCount])

  // 自动滚动到最新日志
  useEffect(() => {
    // 每次 filteredLogs 变化都滚动到底部
    if (logEndRef.current && activeTab === 'logs' && filteredLogs.length > 0) {
      requestAnimationFrame(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'auto' })
      })
    }
  }, [filteredLogs, activeTab])

  // 获取所有列名
  const columns = Array.from(
    new Set(collectedData.flatMap(row => Object.keys(row)))
  )

  const handleExportLogs = () => {
    const logText = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`)
      .join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-logs-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleLogClick = (nodeId?: string) => {
    if (nodeId) {
      // 选中节点
      selectNode(nodeId)
      
      // 调用父组件传入的回调函数来定位节点
      if (onLogClick) {
        onLogClick(nodeId)
      }
    }
  }

  // 数据表格相关方法
  const formatCellValue = (value: unknown): string => {
    if (value === null || value === undefined) return ''
    if (typeof value === 'object') {
      try {
        return JSON.stringify(value)
      } catch {
        return String(value)
      }
    }
    return String(value)
  }

  const startEdit = (rowIndex: number, colName: string, value: unknown) => {
    setEditingCell({ row: rowIndex, col: colName })
    setEditValue(formatCellValue(value))
  }

  const saveEdit = () => {
    if (editingCell) {
      const row = { ...collectedData[editingCell.row] }
      row[editingCell.col] = editValue
      updateDataRow(editingCell.row, row)
      setEditingCell(null)
      setEditValue('')
    }
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setEditValue('')
  }

  const handleAddRow = () => {
    const newRow: DataRow = {}
    columns.forEach(col => { newRow[col] = '' })
    if (columns.length === 0) {
      newRow['列1'] = ''
    }
    addDataRow(newRow)
  }

  const handleAddColumn = () => {
    if (!newColumnName.trim()) return
    const updatedData = collectedData.map(row => ({
      ...row,
      [newColumnName]: ''
    }))
    setCollectedData(updatedData.length > 0 ? updatedData : [{ [newColumnName]: '' }])
    setNewColumnName('')
    setIsAddingColumn(false)
  }

  const handleDeleteColumn = (colName: string) => {
    const updatedData = collectedData.map(row => {
      const newRow = { ...row }
      delete newRow[colName]
      return newRow
    })
    setCollectedData(updatedData)
  }

  const handleDownloadCSV = useCallback(async () => {
    if (collectedData.length === 0) {
      await alert('暂无数据可下载')
      return
    }
    const headers = columns.join(',')
    const rows = collectedData.map(row => 
      columns.map(col => {
        const value = String(row[col] ?? '')
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value
      }).join(',')
    )
    const BOM = '\uFEFF'
    const csvContent = BOM + [headers, ...rows].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${workflowName || '数据'}_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [collectedData, columns, workflowName])

  // 变量相关方法
  const parseVariableValue = (value: string, type: VariableType): unknown => {
    try {
      switch (type) {
        case 'number':
          const num = parseFloat(value)
          return isNaN(num) ? 0 : num
        case 'boolean':
          return value.toLowerCase() === 'true' || value === '1'
        case 'array':
          if (!value.trim()) return []
          return JSON.parse(value)
        case 'object':
          if (!value.trim()) return {}
          return JSON.parse(value)
        default:
          return value
      }
    } catch {
      if (type === 'array') return []
      if (type === 'object') return {}
      return value
    }
  }

  const handleAddVariable = () => {
    if (!newVarName.trim()) return
    const parsedValue = parseVariableValue(newVarValue, newVarType)
    addVariable({ name: newVarName.trim(), value: parsedValue, type: newVarType, scope: 'global' })
    setNewVarName('')
    setNewVarValue('')
    setNewVarType('string')
    setIsAddingVar(false)
  }

  const formatVariableValue = (value: unknown, type: VariableType): string => {
    if (value === null || value === undefined) return ''
    if (type === 'array' || type === 'object' || typeof value === 'object') {
      try {
        return JSON.stringify(value)
      } catch {
        return String(value)
      }
    }
    return String(value)
  }

  const startEditVar = (name: string, value: unknown, type: VariableType) => {
    setEditingVar(name)
    setEditVarValue(formatVariableValue(value, type))
  }

  const saveEditVar = () => {
    if (editingVar) {
      const variable = variables.find(v => v.name === editingVar)
      if (variable) {
        const parsedValue = parseVariableValue(editVarValue, variable.type)
        updateVariable(editingVar, parsedValue)
      }
      setEditingVar(null)
      setEditVarValue('')
    }
  }

  const startEditVarName = (name: string) => {
    setEditingVarName(name)
    setEditVarNameValue(name)
  }

  const saveEditVarName = () => {
    if (!editingVarName || !editVarNameValue) {
      setEditingVarName(null)
      return
    }
    
    const oldName = editingVarName
    const newName = editVarNameValue.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, '')
    
    if (!newName || oldName === newName) {
      setEditingVarName(null)
      return
    }
    
    if (variables.some(v => v.name === newName)) {
      setEditingVarName(null)
      return
    }
    
    const usages = findVariableUsages(oldName)
    
    if (usages.length > 0) {
      setRenameDialog({
        oldName,
        newName,
        usageCount: usages.length,
      })
    } else {
      renameVariable(oldName, newName)
      setEditingVarName(null)
    }
  }

  const handleConfirmRename = () => {
    if (!renameDialog) return
    replaceVariableReferences(renameDialog.oldName, renameDialog.newName)
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  const handleCancelRename = () => {
    if (!renameDialog) return
    renameVariable(renameDialog.oldName, renameDialog.newName)
    setRenameDialog(null)
    setEditingVarName(null)
  }

  const levelColors = {
    info: 'text-blue-500',
    warning: 'text-yellow-500',
    error: 'text-red-500',
    success: 'text-green-500',
  }

  // 高亮搜索关键词
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text
    const lowerText = text.toLowerCase()
    const lowerQuery = query.toLowerCase()
    const index = lowerText.indexOf(lowerQuery)
    if (index === -1) return text
    return (
      <>
        {text.slice(0, index)}
        <span className="bg-yellow-200 rounded px-0.5">{text.slice(index, index + query.length)}</span>
        {text.slice(index + query.length)}
      </>
    )
  }

  return (
    <footer className={cn(
      'border-t bg-card transition-all',
      isCollapsed ? 'h-10' : 'h-64'
    )}>
      <div className="h-10 px-4 flex items-center justify-between border-b bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-600 bg-[length:200%_100%] animate-gradient">
        <div className="flex items-center gap-4">
          {/* 分页标签 */}
          <div className="flex items-center gap-1">
            <button
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all duration-200 border',
                activeTab === 'logs' 
                  ? 'bg-white text-blue-600 border-white shadow-md' 
                  : 'text-white/90 hover:bg-white/20 border-transparent hover:scale-105'
              )}
              onClick={() => setActiveTab('logs')}
            >
              <FileText className="w-3.5 h-3.5" />
              执行日志
              <span className="text-xs opacity-70">({logs.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all duration-200 border',
                activeTab === 'data' 
                  ? 'bg-white text-blue-600 border-white shadow-md' 
                  : 'text-white/90 hover:bg-white/20 border-transparent hover:scale-105'
              )}
              onClick={() => setActiveTab('data')}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              数据表格
              <span className="text-xs opacity-70">({collectedData.length}行)</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all duration-200 border',
                activeTab === 'variables' 
                  ? 'bg-white text-blue-600 border-white shadow-md' 
                  : 'text-white/90 hover:bg-white/20 border-transparent hover:scale-105'
              )}
              onClick={() => setActiveTab('variables')}
            >
              <Variable className="w-3.5 h-3.5" />
              全局变量
              <span className="text-xs opacity-70">({variables.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all duration-200 border',
                activeTab === 'assets' 
                  ? 'bg-white text-blue-600 border-white shadow-md' 
                  : 'text-white/90 hover:bg-white/20 border-transparent hover:scale-105'
              )}
              onClick={() => setActiveTab('assets')}
            >
              <Database className="w-3.5 h-3.5" />
              Excel资源
              <span className="text-xs opacity-70">({dataAssets.length})</span>
            </button>
            <button
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 text-sm rounded-md transition-all duration-200 border',
                activeTab === 'images' 
                  ? 'bg-white text-blue-600 border-white shadow-md' 
                  : 'text-white/90 hover:bg-white/20 border-transparent hover:scale-105'
              )}
              onClick={() => setActiveTab('images')}
            >
              <ImageIcon className="w-3.5 h-3.5" />
              图像资源
              <span className="text-xs opacity-70">({useWorkflowStore.getState().imageAssets.length})</span>
            </button>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {activeTab === 'logs' && (
            <>
              {/* 详细日志开关 */}
              <button
                className={cn(
                  'h-7 px-2 text-xs rounded-md flex items-center gap-1.5 transition-colors border',
                  verboseLog 
                    ? 'bg-green-500 text-white border-green-600 hover:bg-green-600' 
                    : 'bg-white/90 text-gray-500 border-white/50 hover:bg-white'
                )}
                onClick={() => setVerboseLog(!verboseLog)}
                title={verboseLog ? '切换为简洁日志' : '切换为详细日志'}
              >
                {verboseLog ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    详细日志
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-gray-400" />
                    简洁日志
                  </>
                )}
              </button>
              <Button variant="outline" size="sm" className="h-7 text-xs bg-white/90 border-white/50 text-blue-700 hover:bg-white" onClick={handleExportLogs} title="下载日志">
                <Download className="w-3.5 h-3.5 mr-1" />
                下载
              </Button>
              <Button variant="outline" size="icon" className="h-7 w-7 bg-white/90 border-white/50 text-red-500 hover:bg-white" onClick={clearLogs} title="清空日志">
                <Trash2 className="w-4 h-4" />
              </Button>
            </>
          )}
          {activeTab === 'data' && (
            <>
              <Button variant="outline" size="sm" className="h-7 text-xs bg-white/90 border-white/50 text-cyan-600 hover:bg-white" onClick={handleAddRow}>
                <Plus className="w-3.5 h-3.5 mr-1" />行
              </Button>
              {isAddingColumn ? (
                <div className="flex items-center gap-1">
                  <Input value={newColumnName} onChange={(e) => setNewColumnName(e.target.value)}
                    placeholder="列名" className="w-20 h-7 text-xs bg-white" onKeyDown={(e) => e.key === 'Enter' && handleAddColumn()} />
                  <Button size="icon" variant="outline" className="h-7 w-7 bg-white/90 border-white/50 text-cyan-600 hover:bg-white" onClick={handleAddColumn}><Check className="w-3.5 h-3.5" /></Button>
                  <Button size="icon" variant="outline" className="h-7 w-7 bg-white/90 border-white/50 text-gray-500 hover:bg-white" onClick={() => setIsAddingColumn(false)}><X className="w-3.5 h-3.5" /></Button>
                </div>
              ) : (
                <Button variant="outline" size="sm" className="h-7 text-xs bg-white/90 border-white/50 text-cyan-600 hover:bg-white" onClick={() => setIsAddingColumn(true)}>
                  <Plus className="w-3.5 h-3.5 mr-1" />列
                </Button>
              )}
              <Button variant="outline" size="icon" className="h-7 w-7 bg-white/90 border-white/50 text-red-500 hover:bg-white" onClick={clearCollectedData} title="清空数据"><Trash2 className="w-4 h-4" /></Button>
              <Button variant="outline" size="icon" className="h-7 w-7 bg-white/90 border-white/50 text-blue-600 hover:bg-white" onClick={handleDownloadCSV} title="下载CSV"><Download className="w-4 h-4" /></Button>
            </>
          )}
          {activeTab === 'variables' && (
            <>
              {isAddingVar ? (
                <div className="flex items-center gap-1">
                  <Input value={newVarName} onChange={(e) => setNewVarName(e.target.value)}
                    placeholder="变量名" className="w-20 h-7 text-xs bg-white" />
                  <Select 
                    value={newVarType} 
                    onChange={(e) => setNewVarType(e.target.value as VariableType)}
                    className="w-16 h-7 text-xs bg-white"
                  >
                    <option value="string">字符串</option>
                    <option value="number">数字</option>
                    <option value="boolean">布尔</option>
                    <option value="array">列表</option>
                    <option value="object">字典</option>
                  </Select>
                  {newVarType === 'boolean' ? (
                    <Select 
                      value={newVarValue || 'false'} 
                      onChange={(e) => setNewVarValue(e.target.value)}
                      className="w-16 h-7 text-xs bg-white"
                    >
                      <option value="true">true</option>
                      <option value="false">false</option>
                    </Select>
                  ) : (
                    <Input value={newVarValue} onChange={(e) => setNewVarValue(e.target.value)}
                      placeholder={newVarType === 'number' ? '0' : newVarType === 'array' ? '[]' : newVarType === 'object' ? '{}' : '值'} 
                      className="w-20 h-7 text-xs bg-white" 
                      onKeyDown={(e) => e.key === 'Enter' && handleAddVariable()} />
                  )}
                  <Button size="icon" variant="outline" className="h-7 w-7 bg-white/95 border-white/50 text-emerald-600 hover:bg-white" onClick={handleAddVariable}><Check className="w-3.5 h-3.5" /></Button>
                  <Button size="icon" variant="outline" className="h-7 w-7 bg-white/95 border-white/50 text-gray-500 hover:bg-white" onClick={() => setIsAddingVar(false)}><X className="w-3.5 h-3.5" /></Button>
                </div>
              ) : (
                <Button variant="outline" size="sm" className="h-7 text-xs bg-white/95 border-white/50 text-emerald-600 hover:bg-white hover:scale-105 transition-all" onClick={() => setIsAddingVar(true)}>
                  <Plus className="w-3.5 h-3.5 mr-1" />添加变量
                </Button>
              )}
            </>
          )}
          <Button variant="outline" size="icon" className="h-7 w-7 bg-white/95 border-white/50 text-gray-600 hover:bg-white hover:scale-105 transition-all" onClick={() => setIsCollapsed(!isCollapsed)} title={isCollapsed ? '展开' : '收起'}>
            {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="h-[calc(100%-2.5rem)] animate-fade-in">
          {activeTab === 'logs' && (
            <div className="h-full flex flex-col">
              {/* 日志搜索和筛选栏 */}
              <div className="flex items-center gap-2 px-2 py-1.5 border-b bg-muted/30">
                <div className="relative flex-1 max-w-xs group">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-blue-500 transition-colors" />
                  <Input
                    value={logSearchQuery}
                    onChange={(e) => setLogSearchQuery(e.target.value)}
                    placeholder="搜索日志..."
                    className="pl-7 h-7 text-xs"
                  />
                  {logSearchQuery && (
                    <button
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded-full hover:bg-blue-100 text-muted-foreground hover:text-blue-600 transition-all"
                      onClick={() => setLogSearchQuery('')}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5 text-blue-500" />
                  <Select
                    value={logLevelFilter}
                    onChange={(e) => setLogLevelFilter(e.target.value as LogFilterType)}
                    className="h-7 text-xs w-24"
                  >
                    <option value="all">全部</option>
                    <option value="info">信息</option>
                    <option value="success">成功</option>
                    <option value="warning">警告</option>
                    <option value="error">错误</option>
                  </Select>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">显示</span>
                  <Select
                    value={String(maxLogCount)}
                    onChange={(e) => setMaxLogCount(Number(e.target.value))}
                    className="h-7 text-xs w-20"
                  >
                    <option value="100">100条</option>
                    <option value="200">200条</option>
                    <option value="300">300条</option>
                    <option value="400">400条</option>
                    <option value="500">500条</option>
                  </Select>
                </div>
                <span className="text-xs text-blue-600 font-medium">
                  {filteredLogs.length}/{logs.length}
                </span>
              </div>
              
              <ScrollArea className="flex-1 p-2">
                {filteredLogs.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center animate-fade-in">
                    {logs.length === 0 ? (
                      <>
                        <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-3">
                          <FileText className="w-8 h-8 text-blue-400" />
                        </div>
                        <p className="text-sm text-muted-foreground">暂无日志</p>
                        <p className="text-xs text-muted-foreground/70 mt-2 text-center px-4">
                          💡 提示：默认只显示"打印日志"模块的内容，开启"详细日志"可查看所有模块执行日志
                        </p>
                      </>
                    ) : (
                      <>
                        <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mb-3">
                          <Search className="w-8 h-8 text-blue-400" />
                        </div>
                        <p className="text-sm text-muted-foreground">未找到匹配的日志</p>
                        <p className="text-xs text-muted-foreground mt-1">试试其他关键词或筛选条件</p>
                      </>
                    )}
                  </div>
                ) : (
                  <div className="space-y-1">
                    {filteredLogs.map((log) => (
                      <div 
                        key={log.id} 
                        className={cn(
                          'text-xs font-mono px-3 py-1.5 rounded-lg break-words transition-all duration-200 border border-transparent',
                          log.nodeId 
                            ? 'hover:bg-blue-50 cursor-pointer hover:border-blue-300 hover:shadow-sm hover:scale-[1.01] active:scale-[0.99]' 
                            : 'hover:bg-muted/30'
                        )}
                        onClick={() => handleLogClick(log.nodeId)}
                        title={log.nodeId ? '点击定位到对应模块' : undefined}
                      >
                        <span className="text-muted-foreground">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                        <span className={cn(levelColors[log.level], 'font-semibold')}>[{log.level.toUpperCase()}]</span>{' '}
                        <span className="break-all">{logSearchQuery ? highlightText(log.message, logSearchQuery) : log.message}</span>
                        {log.duration !== undefined && <span className="text-blue-500 ml-2">({log.duration}ms)</span>}
                        {log.nodeId && (
                          <span className="ml-2 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
                            📍
                          </span>
                        )}
                      </div>
                    ))}
                    <div ref={logEndRef} />
                  </div>
                )}
              </ScrollArea>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="h-full flex flex-col">
              <ScrollArea className="flex-1 p-2">
                {collectedData.length === 0 && columns.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground animate-fade-in">
                    <div className="w-16 h-16 rounded-full bg-cyan-500/10 flex items-center justify-center mb-3">
                      <FileSpreadsheet className="w-8 h-8 text-cyan-400" />
                    </div>
                    <p className="text-sm">暂无数据</p>
                    <p className="text-xs mt-1">执行工作流后，收集的数据将显示在这里</p>
                    <p className="text-xs text-muted-foreground/70 mt-2 text-center px-4">
                      💡 提示：此处最多实时预览20条数据，完整数据请使用"导出数据表"模块导出
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-xs">
                      <thead>
                        <tr className="bg-muted/50">
                          <th className="border px-2 py-1.5 text-left font-medium w-10">#</th>
                          {columns.map(col => (
                            <th key={col} className="border px-2 py-1.5 text-left font-medium min-w-[100px]">
                              <div className="flex items-center justify-between gap-1">
                                <span>{col}</span>
                                <Button variant="ghost" size="icon" className="w-5 h-5 opacity-50 hover:opacity-100" onClick={() => handleDeleteColumn(col)}>
                                  <X className="w-3 h-3" />
                                </Button>
                              </div>
                            </th>
                          ))}
                          <th className="border px-2 py-1.5 w-12">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {collectedData.map((row, rowIndex) => (
                            <tr key={rowIndex} className="hover:bg-muted/30">
                              <td className="border px-2 py-1 text-muted-foreground">{rowIndex + 1}</td>
                              {columns.map(col => (
                                <td key={col} className="border px-2 py-1 cursor-pointer hover:bg-muted/50" onClick={() => startEdit(rowIndex, col, row[col])}>
                                  {editingCell?.row === rowIndex && editingCell?.col === col ? (
                                    <Input value={editValue} onChange={(e) => setEditValue(e.target.value)} className="h-6 text-xs" autoFocus
                                      onKeyDown={(e) => { if (e.key === 'Enter') saveEdit(); if (e.key === 'Escape') cancelEdit(); }} onBlur={saveEdit} />
                                  ) : (
                                    <div className="flex items-center justify-between group">
                                      <span className="truncate max-w-[150px]" title={formatCellValue(row[col])}>{formatCellValue(row[col])}</span>
                                      <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                                    </div>
                                  )}
                                </td>
                              ))}
                              <td className="border px-2 py-1 text-center">
                                <Button variant="ghost" size="icon" className="w-5 h-5" onClick={() => deleteDataRow(rowIndex)}>
                                  <Trash2 className="w-3 h-3 text-destructive" />
                                </Button>
                              </td>
                            </tr>
                        ))}
                      </tbody>
                    </table>
                    {collectedData.length >= 20 && (
                      <p className="mt-2 text-xs text-muted-foreground text-center">
                        ⚠️ 此处仅展示前 20 条数据用于预览，完整数据请使用"导出数据表"模块导出
                      </p>
                    )}
                  </div>
                )}
              </ScrollArea>
            </div>
          )}

          {activeTab === 'variables' && (
            <ScrollArea className="h-full p-2">
              {variables.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground animate-fade-in">
                  <div className="w-16 h-16 rounded-full bg-purple-500/10 flex items-center justify-center mb-3">
                    <Variable className="w-8 h-8 text-purple-400" />
                  </div>
                  <p className="text-sm">暂无全局变量</p>
                  <p className="text-xs mt-1">点击"添加变量"创建全局变量</p>
                  <p className="text-[10px] mt-2 text-center opacity-70">
                    引用语法：{'{变量名}'} · {'{列表[0]}'} · {'{列表[-1]}'} · {'{字典[键名]}'}
                  </p>
                </div>
              ) : (
                <div className="flex flex-col h-full">
                  <div className="overflow-x-auto flex-1">
                    <table className="w-full border-collapse text-xs">
                      <thead>
                        <tr className="bg-muted/50">
                          <th className="border px-2 py-1.5 text-left font-medium w-32">变量名</th>
                          <th className="border px-2 py-1.5 text-left font-medium">值</th>
                          <th className="border px-2 py-1.5 text-left font-medium w-20">类型</th>
                          <th className="border px-2 py-1.5 w-12">操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {variables.map((v) => (
                          <tr key={v.name} className="hover:bg-muted/30">
                            <td className="border px-2 py-1 cursor-pointer hover:bg-muted/50" onClick={() => startEditVarName(v.name)}>
                              {editingVarName === v.name ? (
                                <Input 
                                  value={editVarNameValue} 
                                  onChange={(e) => setEditVarNameValue(e.target.value.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5]/g, ''))} 
                                  className="h-6 text-xs font-mono" 
                                  autoFocus
                                  onKeyDown={(e) => { 
                                    if (e.key === 'Enter') saveEditVarName(); 
                                    if (e.key === 'Escape') setEditingVarName(null); 
                                  }} 
                                  onBlur={saveEditVarName} 
                                />
                              ) : (
                                <div className="flex items-center justify-between group">
                                  <span className="font-mono text-blue-600">{v.name}</span>
                                  <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                                </div>
                              )}
                            </td>
                            <td className="border px-2 py-1 cursor-pointer hover:bg-muted/50" onClick={() => startEditVar(v.name, v.value, v.type)}>
                              {editingVar === v.name ? (
                                <Input value={editVarValue} onChange={(e) => setEditVarValue(e.target.value)} className="h-6 text-xs" autoFocus
                                  onKeyDown={(e) => { if (e.key === 'Enter') saveEditVar(); if (e.key === 'Escape') setEditingVar(null); }} onBlur={saveEditVar} />
                              ) : (
                                <div className="flex items-center justify-between group">
                                  <span className="truncate max-w-[200px]" title={formatVariableValue(v.value, v.type)}>{formatVariableValue(v.value, v.type)}</span>
                                  <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                                </div>
                              )}
                            </td>
                            <td className="border px-2 py-1 text-muted-foreground">{v.type}</td>
                            <td className="border px-2 py-1 text-center">
                              <Button variant="ghost" size="icon" className="w-5 h-5" onClick={() => deleteVariable(v.name)}>
                                <Trash2 className="w-3 h-3 text-destructive" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="pt-2 border-t mt-2 text-[10px] text-muted-foreground">
                    <span className="font-medium">引用语法：</span>
                    {'{变量名}'} · {'{列表[0]}'} · {'{列表[-1]}'} · {'{字典[键名]}'} · {'{数据[0][name]}'}
                  </div>
                </div>
              )}
            </ScrollArea>
          )}

          {activeTab === 'assets' && <ExcelAssetsPanel />}

          {activeTab === 'images' && <ImageAssetsPanel />}
        </div>
      )}

      {/* 变量重命名确认弹窗 */}
      {renameDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-[420px] mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="h-1.5 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500" />
            <div className="p-6">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">变量重命名</h3>
                  <p className="text-xs text-gray-500">检测到变量引用需要更新</p>
                </div>
              </div>
              <div className="bg-gradient-to-r from-gray-50 to-gray-100/50 rounded-xl p-4 mb-5">
                <div className="flex items-center justify-center gap-3">
                  <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-xs text-gray-500">原名</span>
                    <code className="text-sm font-mono font-semibold text-red-600">{'{' + renameDialog.oldName + '}'}</code>
                  </div>
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 shadow-md">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-xs text-gray-500">新名</span>
                    <code className="text-sm font-mono font-semibold text-emerald-600">{'{' + renameDialog.newName + '}'}</code>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl mb-6">
                <svg className="w-5 h-5 text-amber-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-amber-800">
                  发现 <span className="font-bold text-amber-900">{renameDialog.usageCount}</span> 处引用了此变量
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCancelRename}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all duration-200 hover:shadow-md active:scale-[0.98]"
                >
                  仅改名称
                </button>
                <button
                  onClick={handleConfirmRename}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 rounded-xl transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98]"
                >
                  全部更新
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* 确认对话框 */}
      <ConfirmDialog />
    </footer>
  )
}
