import { useState, useCallback } from 'react'
import { useWorkflowStore, type DataRow } from '@/store/workflowStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { 
  Table, 
  Download, 
  Plus, 
  Trash2, 
  X, 
  FileSpreadsheet,
  Edit2,
  Check
} from 'lucide-react'

interface DataPreviewPanelProps {
  isOpen: boolean
  onClose: () => void
}

export function DataPreviewPanel({ isOpen, onClose }: DataPreviewPanelProps) {
  const { 
    collectedData, 
    setCollectedData,
    updateDataRow, 
    deleteDataRow, 
    addDataRow,
    clearCollectedData,
    name: workflowName 
  } = useWorkflowStore()
  
  const { alert, ConfirmDialog } = useConfirm()
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [newColumnName, setNewColumnName] = useState('')
  const [isAddingColumn, setIsAddingColumn] = useState(false)

  const columns = Array.from(
    new Set(collectedData.flatMap(row => Object.keys(row)))
  )

  const startEdit = (rowIndex: number, colName: string, value: unknown) => {
    setEditingCell({ row: rowIndex, col: colName })
    setEditValue(String(value ?? ''))
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

  const handleDownload = useCallback(async () => {
    if (collectedData.length === 0) {
      await alert('没有数据可下载')
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

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[80vh] flex flex-col overflow-hidden animate-scale-in">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">数据预览</h2>
            <span className="text-sm text-muted-foreground">
              ({collectedData.length} 行, {columns.length} 列)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="border-green-200 text-green-600 hover:bg-green-50" onClick={handleAddRow}>
              <Plus className="w-4 h-4 mr-1" />添加行
            </Button>
            {isAddingColumn ? (
              <div className="flex items-center gap-1">
                <Input value={newColumnName} onChange={(e) => setNewColumnName(e.target.value)}
                  placeholder="列名" className="w-24 h-8" onKeyDown={(e) => e.key === 'Enter' && handleAddColumn()} />
                <Button size="sm" variant="outline" className="border-green-200 text-green-600 hover:bg-green-50" onClick={handleAddColumn}><Check className="w-4 h-4" /></Button>
                <Button size="sm" variant="outline" className="border-gray-200 text-gray-500 hover:bg-gray-50" onClick={() => setIsAddingColumn(false)}><X className="w-4 h-4" /></Button>
              </div>
            ) : (
              <Button variant="outline" size="sm" className="border-green-200 text-green-600 hover:bg-green-50" onClick={() => setIsAddingColumn(true)}>
                <Plus className="w-4 h-4 mr-1" />添加列
              </Button>
            )}
            <Button variant="outline" size="sm" className="border-red-200 text-red-600 hover:bg-red-50" onClick={clearCollectedData}>
              <Trash2 className="w-4 h-4 mr-1" />清空
            </Button>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white" onClick={handleDownload}>
              <Download className="w-4 h-4 mr-1" />下载CSV
            </Button>
            <Button variant="outline" size="icon" className="border-gray-200 text-gray-500 hover:bg-gray-50" onClick={onClose}><X className="w-4 h-4" /></Button>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          {collectedData.length === 0 && columns.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Table className="w-12 h-12 mb-4 opacity-50" />
              <p>暂无数据</p>
              <p className="text-sm mt-1">执行工作流后，收集的数据将显示在这里</p>
              <Button variant="outline" size="sm" className="mt-4 border-green-200 text-green-600 hover:bg-green-50" onClick={handleAddRow}>
                <Plus className="w-4 h-4 mr-1" />手动添加数据
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="bg-muted/50">
                    <th className="border px-3 py-2 text-left font-medium w-12">#</th>
                    {columns.map(col => (
                      <th key={col} className="border px-3 py-2 text-left font-medium min-w-[120px]">
                        <div className="flex items-center justify-between gap-2">
                          <span>{col}</span>
                          <Button variant="ghost" size="icon" className="w-6 h-6 opacity-50 hover:opacity-100"
                            onClick={() => handleDeleteColumn(col)}><X className="w-3 h-3" /></Button>
                        </div>
                      </th>
                    ))}
                    <th className="border px-3 py-2 w-16">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {collectedData.map((row, rowIndex) => (
                    <tr key={rowIndex} className="hover:bg-muted/30">
                      <td className="border px-3 py-2 text-muted-foreground">{rowIndex + 1}</td>
                      {columns.map(col => (
                        <td key={col} className="border px-3 py-2 cursor-pointer hover:bg-muted/50"
                          onClick={() => startEdit(rowIndex, col, row[col])}>
                          {editingCell?.row === rowIndex && editingCell?.col === col ? (
                            <Input value={editValue} onChange={(e) => setEditValue(e.target.value)}
                              className="h-7 text-sm" autoFocus
                              onKeyDown={(e) => { if (e.key === 'Enter') saveEdit(); if (e.key === 'Escape') cancelEdit(); }}
                              onBlur={saveEdit} />
                          ) : (
                            <div className="flex items-center justify-between group">
                              <span className="truncate max-w-[200px]">{String(row[col] ?? '')}</span>
                              <Edit2 className="w-3 h-3 opacity-0 group-hover:opacity-50" />
                            </div>
                          )}
                        </td>
                      ))}
                      <td className="border px-3 py-2">
                        <Button variant="ghost" size="icon" className="w-6 h-6" onClick={() => deleteDataRow(rowIndex)}>
                          <Trash2 className="w-3 h-3 text-destructive" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </ScrollArea>
        <div className="p-3 border-t bg-muted/30 text-xs text-muted-foreground">
          提示：点击单元格可编辑内容，按 Enter 保存，按 Esc 取消
        </div>
      </div>
      
      {/* 确认对话框 */}
      {ConfirmDialog}
    </div>
  )
}
