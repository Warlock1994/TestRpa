import { useState } from 'react'
import { Button } from './button'
import { VariableInput } from './variable-input'
import { Folder, File, Loader2 } from 'lucide-react'
import { systemApi } from '@/services/api'
import { cn } from '@/lib/utils'

interface PathInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  type?: 'folder' | 'file'
  title?: string
  fileTypes?: Array<[string, string]>  // 文件类型过滤器，如 [["Excel文件", "*.xlsx"]]
}

export function PathInput({
  value,
  onChange,
  placeholder,
  className,
  type = 'folder',
  title,
  fileTypes,
}: PathInputProps) {
  const [isSelecting, setIsSelecting] = useState(false)

  const handleSelect = async () => {
    setIsSelecting(true)
    try {
      if (type === 'folder') {
        const result = await systemApi.selectFolder(title || '选择文件夹')
        if (result.data?.success && result.data.path) {
          onChange(result.data.path)
        }
      } else {
        const result = await systemApi.selectFile(title || '选择文件', undefined, fileTypes)
        if (result.data?.success && result.data.path) {
          onChange(result.data.path)
        }
      }
    } catch (error) {
      console.error('选择路径失败:', error)
    } finally {
      setIsSelecting(false)
    }
  }

  return (
    <div className={cn('flex gap-1', className)}>
      <div className="flex-1">
        <VariableInput
          value={value}
          onChange={onChange}
          placeholder={placeholder}
        />
      </div>
      <Button
        type="button"
        variant="outline"
        size="icon"
        onClick={handleSelect}
        disabled={isSelecting}
        title={type === 'folder' ? '选择文件夹' : '选择文件'}
        className="shrink-0"
      >
        {isSelecting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : type === 'folder' ? (
          <Folder className="w-4 h-4" />
        ) : (
          <File className="w-4 h-4" />
        )}
      </Button>
    </div>
  )
}
