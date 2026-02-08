import { useState, useRef, useCallback, useEffect } from 'react'
import { useWorkflowStore } from '@/store/workflowStore'
import { dataAssetApi } from '@/services/api'
import { useConfirm } from '@/components/ui/confirm-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Upload,
  Folder,
  File,
  Trash2,
  Edit2,
  Plus,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { DataAsset } from '@/types'
import { ExcelPreviewDialog } from './config-panels/ExcelPreviewDialog'

export function ExcelAssetsPanel() {
  const { dataAssets, setDataAssets, addDataAsset, deleteDataAsset } = useWorkflowStore()
  const { confirm, alert, ConfirmDialog } = useConfirm()
  
  const [folders, setFolders] = useState<string[]>([])
  const [currentPath, setCurrentPath] = useState<string>('')  // 当前所在路径
  const [isCreatingFolder, setIsCreatingFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [editingFolder, setEditingFolder] = useState<string | null>(null)
  const [editFolderName, setEditFolderName] = useState('')
  const [editingAsset, setEditingAsset] = useState<string | null>(null)
  const [editAssetName, setEditAssetName] = useState('')
  const [previewAsset, setPreviewAsset] = useState<DataAsset | null>(null)
  const [dragOverFolder, setDragOverFolder] = useState<string | null>(null)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; folder: string; isFile?: boolean; assetId?: string; isBlank?: boolean } | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 加载文件夹列表
  const loadFolders = useCallback(async () => {
    const result = await dataAssetApi.listFolders()
    if (result.data) {
      setFolders(result.data)
    }
  }, [])

  useEffect(() => {
    loadFolders()
  }, [loadFolders])

  // 获取当前路径下的子文件夹和文件
  const getCurrentItems = useCallback(() => {
    // 获取当前路径下的直接子文件夹
    const subfolders = folders.filter(f => {
      if (!currentPath) {
        // 根目录：只显示一级文件夹
        return !f.includes('/')
      } else {
        // 子目录：显示直接子文件夹
        const prefix = currentPath + '/'
        return f.startsWith(prefix) && !f.substring(prefix.length).includes('/')
      }
    })

    // 获取当前路径下的文件
    const files = dataAssets.filter(a => a.folder === currentPath)

    return { subfolders, files }
  }, [folders, dataAssets, currentPath])

  const { subfolders, files } = getCurrentItems()

  // 面包屑导航
  const breadcrumbs = currentPath ? currentPath.split('/') : []

  // 导航到指定路径
  const navigateTo = (path: string) => {
    setCurrentPath(path)
  }

  // 双击进入文件夹
  const handleFolderDoubleClick = (folderPath: string) => {
    setCurrentPath(folderPath)
  }

  // 创建文件夹
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return
    
    // 在当前路径下创建文件夹
    const result = await dataAssetApi.createFolder(newFolderName.trim(), currentPath || undefined)
    if (result.error) {
      await alert(result.error)
    } else {
      await loadFolders()
      setIsCreatingFolder(false)
      setNewFolderName('')
    }
  }

  // 重命名文件夹
  const handleRenameFolder = async (folderPath: string) => {
    if (!editFolderName.trim() || editFolderName === folderPath.split('/').pop()) {
      setEditingFolder(null)
      return
    }
    
    const result = await dataAssetApi.renameFolder(folderPath, editFolderName.trim())
    if (result.error) {
      await alert(result.error)
    } else {
      await loadFolders()
      const excelResult = await dataAssetApi.list()
      if (excelResult.data) {
        setDataAssets(excelResult.data)
      }
    }
    setEditingFolder(null)
  }

  // 重命名文件
  const handleRenameAsset = async (assetId: string) => {
    if (!editAssetName.trim()) {
      setEditingAsset(null)
      return
    }
    
    const result = await dataAssetApi.rename(assetId, editAssetName.trim())
    if (result.error) {
      await alert(result.error)
    } else if (result.data?.asset) {
      // 更新本地状态
      const excelResult = await dataAssetApi.list()
      if (excelResult.data) {
        setDataAssets(excelResult.data)
      }
    }
    setEditingAsset(null)
  }

  // 删除文件夹
  const handleDeleteFolder = async (folderPath: string) => {
    const folderName = folderPath.split('/').pop() || folderPath
    const confirmed = await confirm(
      `确定要删除文件夹"${folderName}"及其所有内容吗？`,
      { type: 'warning', title: '删除文件夹' }
    )
    if (!confirmed) return
    
    const result = await dataAssetApi.deleteFolder(folderPath)
    if (result.error) {
      await alert(result.error)
    } else {
      await loadFolders()
      const excelResult = await dataAssetApi.list()
      if (excelResult.data) {
        setDataAssets(excelResult.data)
      }
    }
  }

  // 批量上传处理
  const handleBatchFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    if (files.length === 0) return

    const excelFiles = files.filter(f => f.name.match(/\.(xlsx|xls)$/i))
    if (excelFiles.length === 0) {
      await alert('没有找到 Excel 文件')
      return
    }

    try {
      const result = await dataAssetApi.uploadBatch(excelFiles, currentPath || undefined)
      if (result.data) {
        result.data.success.forEach(asset => addDataAsset(asset))
        if (result.data.errors.length > 0) {
          await alert(`部分文件上传失败:\n${result.data.errors.map(e => e.filename).join('\n')}`)
        }
      }
    } catch (error) {
      await alert(`批量上传失败: ${error}`)
    } finally {
      event.target.value = ''
    }
  }

  // 删除当前目录所有文件
  const handleDeleteAllFiles = async () => {
    const currentFiles = dataAssets.filter(a => a.folder === currentPath)
    if (currentFiles.length === 0) {
      await alert('当前目录没有文件')
      return
    }

    const confirmed = await confirm(
      `确定要删除当前目录中的所有 ${currentFiles.length} 个文件吗？此操作不可恢复！`,
      { type: 'warning', title: '删除所有文件' }
    )
    if (!confirmed) return

    let successCount = 0
    let errorCount = 0

    for (const asset of currentFiles) {
      const result = await dataAssetApi.delete(asset.id)
      if (result.error) {
        errorCount++
      } else {
        deleteDataAsset(asset.id)
        successCount++
      }
    }

    if (errorCount > 0) {
      await alert(`删除完成：成功 ${successCount} 个，失败 ${errorCount} 个`)
    }
  }

  // 删除文件
  const handleDeleteAsset = async (id: string) => {
    const confirmed = await confirm('确定要删除此文件吗？', { type: 'warning', title: '删除文件' })
    if (!confirmed) return
    
    const result = await dataAssetApi.delete(id)
    if (!result.error) {
      deleteDataAsset(id)
    }
  }

  // 拖拽处理
  const handleDragStart = (e: React.DragEvent, asset: DataAsset) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('assetId', asset.id)
    e.dataTransfer.setData('assetType', 'excel')
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
    setDragOverFolder(currentPath)
  }

  const handleDragLeave = () => {
    setDragOverFolder(null)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragOverFolder(null)

    // 处理文件拖拽导入
    if (e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files).filter(f => 
        f.name.match(/\.(xlsx|xls)$/i)
      )
      
      if (files.length === 0) return

      try {
        const result = await dataAssetApi.uploadBatch(files, currentPath || undefined)
        if (result.data) {
          result.data.success.forEach(asset => addDataAsset(asset))
        }
      } catch (error) {
        await alert(`导入失败: ${error}`)
      }
      return
    }

    // 处理资源移动
    const assetId = e.dataTransfer.getData('assetId')
    const assetType = e.dataTransfer.getData('assetType')
    
    if (assetId && assetType === 'excel') {
      const result = await dataAssetApi.moveAsset(assetId, currentPath || undefined)
      if (result.error) {
        await alert(result.error)
      } else {
        const excelResult = await dataAssetApi.list()
        if (excelResult.data) {
          setDataAssets(excelResult.data)
        }
      }
    }
  }

  // 右键菜单
  const handleContextMenu = (e: React.MouseEvent, folder?: string, assetId?: string) => {
    e.preventDefault()
    const isBlank = folder === undefined && assetId === undefined
    setContextMenu({ 
      x: e.clientX, 
      y: e.clientY, 
      folder: assetId ? '' : (folder !== undefined ? folder : currentPath),
      isFile: !!assetId,
      assetId,
      isBlank
    })
  }

  useEffect(() => {
    const handleClick = () => setContextMenu(null)
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [])

  // 渲染文件夹卡片（更小尺寸）
  const renderFolderCard = (folderPath: string) => {
    const folderName = folderPath.split('/').pop() || folderPath
    const isEditing = editingFolder === folderPath
    const folderAssets = dataAssets.filter(a => a.folder === folderPath)
    const isDragOver = dragOverFolder === folderPath

    return (
      <div
        key={folderPath}
        className={cn(
          'relative group cursor-pointer transition-all duration-200',
          'bg-white rounded-lg border p-2',
          'hover:shadow-md hover:scale-102 hover:-translate-y-0.5',
          isDragOver ? 'border-blue-400 bg-blue-50 ring-2 ring-blue-200' : 'border-orange-200 hover:border-orange-300'
        )}
        onClick={() => handleFolderDoubleClick(folderPath)}
        onContextMenu={(e) => {
          e.stopPropagation()
          handleContextMenu(e, folderPath)
        }}
        onDragOver={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setDragOverFolder(folderPath)
        }}
        onDragLeave={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setDragOverFolder(null)
        }}
        onDrop={async (e) => {
          e.preventDefault()
          e.stopPropagation()
          setDragOverFolder(null)

          const assetId = e.dataTransfer.getData('assetId')
          const assetType = e.dataTransfer.getData('assetType')
          
          if (assetId && assetType === 'excel') {
            const result = await dataAssetApi.moveAsset(assetId, folderPath)
            if (result.error) {
              await alert(result.error)
            } else {
              const excelResult = await dataAssetApi.list()
              if (excelResult.data) {
                setDataAssets(excelResult.data)
              }
            }
          }
        }}
      >
        <div className="flex flex-col items-center gap-1">
          <div className="relative">
            <Folder className="w-10 h-10 text-orange-500" />
            {folderAssets.length > 0 && (
              <div className="absolute -top-1 -right-1 bg-orange-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center">
                {folderAssets.length}
              </div>
            )}
          </div>
          
          {isEditing ? (
            <Input
              value={editFolderName}
              onChange={(e) => setEditFolderName(e.target.value)}
              className="h-6 text-xs text-center bg-white border-orange-300"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRenameFolder(folderPath)
                if (e.key === 'Escape') setEditingFolder(null)
              }}
              onBlur={() => handleRenameFolder(folderPath)}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <p className="text-xs font-medium text-gray-700 text-center truncate w-full px-1" title={folderName}>
              {folderName}
            </p>
          )}
        </div>
      </div>
    )
  }

  // 渲染 Excel 文件卡片（更小尺寸）
  const renderExcelCard = (asset: DataAsset) => {
    const isEditing = editingAsset === asset.id

    return (
      <div
        key={asset.id}
        className="relative group cursor-pointer transition-all duration-200 bg-white rounded-lg border p-2 hover:shadow-md hover:scale-102 hover:-translate-y-0.5 border-green-200 hover:border-green-300"
        draggable
        onDragStart={(e) => handleDragStart(e, asset)}
        onClick={() => !isEditing && setPreviewAsset(asset)}
        onContextMenu={(e) => {
          e.stopPropagation()
          handleContextMenu(e, undefined, asset.id)
        }}
      >
        <div className="flex flex-col items-center gap-1">
          <File className="w-10 h-10 text-green-600" />
          
          {isEditing ? (
            <Input
              value={editAssetName}
              onChange={(e) => setEditAssetName(e.target.value)}
              className="h-6 text-xs text-center bg-white border-green-300"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleRenameAsset(asset.id)
                if (e.key === 'Escape') setEditingAsset(null)
              }}
              onBlur={() => handleRenameAsset(asset.id)}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <p className="text-xs font-medium text-gray-700 text-center truncate w-full px-1" title={asset.originalName}>
              {asset.originalName}
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-gray-50 to-white">
      {/* 面包屑导航 */}
      {currentPath && (
        <div className="flex items-center gap-1 px-3 py-1.5 bg-white border-b text-xs">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 hover:bg-green-50"
            onClick={() => navigateTo('')}
          >
            <Folder className="w-3 h-3 mr-1" />
            根目录
          </Button>
          {breadcrumbs.map((crumb, index) => {
            const path = breadcrumbs.slice(0, index + 1).join('/')
            return (
              <div key={path} className="flex items-center gap-1">
                <ChevronRight className="w-3 h-3 text-gray-400" />
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 hover:bg-green-50"
                  onClick={() => navigateTo(path)}
                >
                  {crumb}
                </Button>
              </div>
            )
          })}
        </div>
      )}

      {/* 文件列表 */}
      <ScrollArea className="flex-1">
        <div
          className={cn(
            'p-3 min-h-full',
            dragOverFolder === currentPath && 'bg-blue-50 border-2 border-dashed border-blue-400'
          )}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onContextMenu={(e) => handleContextMenu(e)}
        >
          {dataAssets.length === 0 && folders.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground py-12">
              <File className="w-16 h-16 mb-3 opacity-30" />
              <p className="text-sm font-medium">暂无 Excel 文件</p>
              <p className="text-xs mt-1">点击上传或拖拽文件到此处</p>
            </div>
          ) : subfolders.length === 0 && files.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground py-12">
              <Folder className="w-16 h-16 mb-3 opacity-30" />
              <p className="text-sm font-medium">此文件夹为空</p>
              <p className="text-xs mt-1">点击上传或拖拽文件到此处</p>
            </div>
          ) : (
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12 gap-2">
              {subfolders.map(folder => renderFolderCard(folder))}
              {files.map(asset => renderExcelCard(asset))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* 隐藏的文件输入（批量上传） */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".xlsx,.xls"
        multiple
        onChange={handleBatchFileUpload}
        className="hidden"
      />

      {/* 预览对话框 */}
      {previewAsset && (
        <ExcelPreviewDialog
          open={!!previewAsset}
          onClose={() => setPreviewAsset(null)}
          fileId={previewAsset.id}
          fileName={previewAsset.originalName}
          previewOnly
        />
      )}

      {/* 新建文件夹对话框 */}
      {isCreatingFolder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setIsCreatingFolder(false)}>
          <div className="bg-white rounded-xl shadow-2xl p-6 w-96 animate-in fade-in zoom-in duration-200" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4 text-gray-800">新建文件夹</h3>
            <Input
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="请输入文件夹名称"
              className="mb-4"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateFolder()
                if (e.key === 'Escape') {
                  setIsCreatingFolder(false)
                  setNewFolderName('')
                }
              }}
            />
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreatingFolder(false)
                  setNewFolderName('')
                }}
              >
                取消
              </Button>
              <Button
                onClick={handleCreateFolder}
                className="bg-green-500 hover:bg-green-600"
              >
                创建
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 右键菜单 */}
      {contextMenu && (
        <div
          className="fixed bg-white border border-gray-200 rounded-xl shadow-2xl py-2 z-50 min-w-[140px] animate-in fade-in zoom-in-95 duration-200"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          {contextMenu.isFile ? (
            <>
              {/* 文件右键菜单：重命名、删除 */}
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-orange-50 hover:to-amber-50 flex items-center gap-2.5 transition-all duration-150 text-gray-700 hover:text-orange-700"
                onClick={() => {
                  if (contextMenu.assetId) {
                    const asset = dataAssets.find(a => a.id === contextMenu.assetId)
                    if (asset) {
                      setEditingAsset(asset.id)
                      setEditAssetName(asset.originalName)
                    }
                  }
                  setContextMenu(null)
                }}
              >
                <Edit2 className="w-4 h-4" />
                重命名
              </button>
              <div className="h-px bg-gray-200 my-1 mx-2"></div>
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-red-50 hover:to-pink-50 flex items-center gap-2.5 transition-all duration-150 text-red-600 hover:text-red-700"
                onClick={() => {
                  if (contextMenu.assetId) handleDeleteAsset(contextMenu.assetId)
                  setContextMenu(null)
                }}
              >
                <Trash2 className="w-4 h-4" />
                删除
              </button>
            </>
          ) : contextMenu.isBlank ? (
            <>
              {/* 空白区域右键菜单：上传、新建文件夹、删除所有文件 */}
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 flex items-center gap-2.5 transition-all duration-150 text-gray-700 hover:text-green-700"
                onClick={() => {
                  fileInputRef.current?.click()
                  setContextMenu(null)
                }}
              >
                <Upload className="w-4 h-4" />
                上传文件
              </button>
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-orange-50 hover:to-amber-50 flex items-center gap-2.5 transition-all duration-150 text-gray-700 hover:text-orange-700"
                onClick={() => {
                  setIsCreatingFolder(true)
                  setContextMenu(null)
                }}
              >
                <Plus className="w-4 h-4" />
                新建文件夹
              </button>
              <div className="h-px bg-gray-200 my-1 mx-2"></div>
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-red-50 hover:to-pink-50 flex items-center gap-2.5 transition-all duration-150 text-red-600 hover:text-red-700"
                onClick={() => {
                  handleDeleteAllFiles()
                  setContextMenu(null)
                }}
              >
                <Trash2 className="w-4 h-4" />
                删除所有文件
              </button>
            </>
          ) : (
            <>
              {/* 文件夹右键菜单：上传到此文件夹、重命名、删除 */}
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 flex items-center gap-2.5 transition-all duration-150 text-gray-700 hover:text-green-700"
                onClick={() => {
                  const targetFolder = contextMenu.folder
                  const originalHandler = fileInputRef.current?.onchange
                  if (fileInputRef.current) {
                    fileInputRef.current.onchange = async (e) => {
                      const input = e.target as HTMLInputElement
                      const files = Array.from(input.files || [])
                      if (files.length === 0) return

                      const excelFiles = files.filter(f => f.name.match(/\.(xlsx|xls)$/i))
                      if (excelFiles.length === 0) {
                        await alert('没有找到 Excel 文件')
                        return
                      }

                      try {
                        const result = await dataAssetApi.uploadBatch(excelFiles, targetFolder || undefined)
                        if (result.data) {
                          result.data.success.forEach(asset => addDataAsset(asset))
                          if (result.data.errors.length > 0) {
                            await alert(`部分文件上传失败:\n${result.data.errors.map(e => e.filename).join('\n')}`)
                          }
                        }
                      } catch (error) {
                        await alert(`批量上传失败: ${error}`)
                      } finally {
                        input.value = ''
                        if (fileInputRef.current && originalHandler) {
                          fileInputRef.current.onchange = originalHandler
                        }
                      }
                    }
                  }
                  fileInputRef.current?.click()
                  setContextMenu(null)
                }}
              >
                <Upload className="w-4 h-4" />
                上传到此文件夹
              </button>
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-orange-50 hover:to-amber-50 flex items-center gap-2.5 transition-all duration-150 text-gray-700 hover:text-orange-700"
                onClick={() => {
                  setEditingFolder(contextMenu.folder)
                  setEditFolderName(contextMenu.folder.split('/').pop() || '')
                  setContextMenu(null)
                }}
              >
                <Edit2 className="w-4 h-4" />
                重命名
              </button>
              <div className="h-px bg-gray-200 my-1 mx-2"></div>
              <button
                className="w-full px-4 py-2 text-sm text-left hover:bg-gradient-to-r hover:from-red-50 hover:to-pink-50 flex items-center gap-2.5 transition-all duration-150 text-red-600 hover:text-red-700"
                onClick={() => {
                  handleDeleteFolder(contextMenu.folder)
                  setContextMenu(null)
                }}
              >
                <Trash2 className="w-4 h-4" />
                删除
              </button>
            </>
          )}
        </div>
      )}

      {ConfirmDialog}
    </div>
  )
}
