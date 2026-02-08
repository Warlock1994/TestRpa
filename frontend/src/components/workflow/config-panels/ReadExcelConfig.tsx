import { useState, useEffect } from 'react'
import { Eye } from 'lucide-react'
import { useWorkflowStore, type NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { NumberInput } from '@/components/ui/number-input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { Button } from '@/components/ui/button'
import { VariableInput } from '@/components/ui/variable-input'
import { VariableNameInput } from '@/components/ui/variable-name-input'
import { HierarchicalExcelSelector } from '@/components/ui/hierarchical-excel-selector'
import { dataAssetApi } from '@/services/api'
import { ExcelPreviewDialog, type SelectionResult } from './ExcelPreviewDialog'
import type { DataAsset } from '@/types'

interface ReadExcelConfigProps {
  data: NodeData
  onChange: (key: string, value: unknown) => void
}

export function ReadExcelConfig({ data, onChange }: ReadExcelConfigProps) {
  const [assets, setAssets] = useState<DataAsset[]>([])
  const [sheetNames, setSheetNames] = useState<string[]>([])
  const [previewOpen, setPreviewOpen] = useState(false)
  const dataAssets = useWorkflowStore((state) => state.dataAssets)

  // 加载Excel文件资源列表
  useEffect(() => {
    if (dataAssets.length > 0) {
      setAssets(dataAssets)
    } else {
      dataAssetApi.list().then(result => {
        if (result.data) {
          setAssets(result.data)
        }
      })
    }
  }, [dataAssets])

  // 当选择文件时，更新工作表列表
  useEffect(() => {
    const fileName = data.fileName as string
    if (fileName) {
      const asset = assets.find(a => a.originalName === fileName)
      if (asset) {
        setSheetNames(asset.sheetNames)
      }
    } else {
      setSheetNames([])
    }
  }, [data.fileName, assets])

  const readMode = (data.readMode as string) || 'cell'
  const fileName = (data.fileName as string) || ''
  const selectedAsset = assets.find(a => a.originalName === fileName)

  // 处理可视化选择结果
  const handleSelection = (result: SelectionResult) => {
    if (result.mode === 'cell' && result.cellAddress) {
      onChange('cellAddress', result.cellAddress)
    } else if (result.mode === 'row' && result.rowIndex) {
      onChange('rowIndex', result.rowIndex)
    } else if (result.mode === 'column' && result.columnIndex) {
      onChange('columnIndex', result.columnIndex)
    } else if (result.mode === 'range' && result.startCell && result.endCell) {
      onChange('startCell', result.startCell)
      onChange('endCell', result.endCell)
    }
  }

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="fileName">选择Excel文件</Label>
        <HierarchicalExcelSelector
          value={fileName}
          onChange={(newFileName) => {
            onChange('fileName', newFileName)
            onChange('sheetName', '')
          }}
        />
        {assets.length === 0 && (
          <p className="text-xs text-orange-500">
            请先在底部"Excel资源"分页中上传Excel文件
          </p>
        )}
      </div>

      {sheetNames.length > 0 && (
        <div className="space-y-2">
          <Label htmlFor="sheetName">工作表 (可选)</Label>
          <Select
            id="sheetName"
            value={(data.sheetName as string) || ''}
            onChange={(e) => onChange('sheetName', e.target.value)}
          >
            <option value="">默认工作表</option>
            {sheetNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </Select>
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="readMode">读取方式</Label>
        <Select
          id="readMode"
          value={readMode}
          onChange={(e) => onChange('readMode', e.target.value)}
        >
          <option value="cell">单元格级别</option>
          <option value="row">行级别</option>
          <option value="column">列级别</option>
          <option value="range">块级别 (范围)</option>
        </Select>
      </div>

      {readMode === 'cell' && (
        <div className="space-y-2">
          <Label htmlFor="cellAddress">单元格地址</Label>
          <div className="flex gap-2">
            <VariableInput
              value={(data.cellAddress as string) || ''}
              onChange={(v) => onChange('cellAddress', v)}
              placeholder="如 A1, B2, C3，支持 {变量名}"
              className="flex-1"
            />
            {selectedAsset && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPreviewOpen(true)}
                title="可视化选择"
              >
                <Eye className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      )}

      {readMode === 'row' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="rowIndex">行号 (从1开始)</Label>
            <div className="flex gap-2">
              <NumberInput
                id="rowIndex"
                value={(data.rowIndex as number) ?? 1}
                onChange={(v) => onChange('rowIndex', v)}
                defaultValue={1}
                min={1}
                className="flex-1"
              />
              {selectedAsset && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPreviewOpen(true)}
                  title="可视化选择"
                >
                  <Eye className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="startCol">起始列 (可选)</Label>
            <VariableInput
              value={(data.startCol as string) || ''}
              onChange={(v) => onChange('startCol', v)}
              placeholder="如 A 或 1，留空则从第1列开始，支持 {变量名}"
            />
          </div>
        </>
      )}

      {readMode === 'column' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="columnIndex">列号或列字母</Label>
            <div className="flex gap-2">
              <VariableInput
                value={(data.columnIndex as string) || ''}
                onChange={(v) => onChange('columnIndex', v)}
                placeholder="如 A 或 1，支持 {变量名}"
                className="flex-1"
              />
              {selectedAsset && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPreviewOpen(true)}
                  title="可视化选择"
                >
                  <Eye className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="startRow">起始行 (从1开始)</Label>
            <NumberInput
              id="startRow"
              value={(data.startRow as number) ?? 2}
              onChange={(v) => onChange('startRow', v)}
              defaultValue={2}
              min={1}
            />
            <p className="text-xs text-gray-500">默认从第2行开始，跳过表头</p>
          </div>
        </>
      )}

      {readMode === 'range' && (
        <>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>选择范围</Label>
              {selectedAsset && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPreviewOpen(true)}
                  className="h-7 text-xs"
                >
                  <Eye className="w-3 h-3 mr-1" />
                  可视化选择
                </Button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="startCell" className="text-xs text-gray-500">起始</Label>
                <VariableInput
                  value={(data.startCell as string) || ''}
                  onChange={(v) => onChange('startCell', v)}
                  placeholder="如 A1，支持 {变量名}"
                />
              </div>
              <div>
                <Label htmlFor="endCell" className="text-xs text-gray-500">结束</Label>
                <VariableInput
                  value={(data.endCell as string) || ''}
                  onChange={(v) => onChange('endCell', v)}
                  placeholder="如 C10，支持 {变量名}"
                />
              </div>
            </div>
          </div>
        </>
      )}

      <div className="space-y-2">
        <Label htmlFor="variableName">存储到变量</Label>
        <VariableNameInput
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名"
          isStorageVariable={true}
        />
      </div>

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>读取结果说明：</strong><br/>
          • 单元格：返回单个值<br/>
          • 行/列：返回数组 [值1, 值2, ...]<br/>
          • 块：返回二维数组 [[行1], [行2], ...]
        </p>
      </div>

      {/* Excel预览对话框 */}
      {selectedAsset && (
        <ExcelPreviewDialog
          open={previewOpen}
          onClose={() => setPreviewOpen(false)}
          fileId={selectedAsset.id}
          fileName={selectedAsset.originalName}
          sheetName={(data.sheetName as string) || undefined}
          mode={readMode as 'cell' | 'row' | 'column' | 'range'}
          onSelect={handleSelection}
        />
      )}
    </>
  )
}
