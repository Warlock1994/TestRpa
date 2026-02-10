import { Button } from '../ui/button'
import { Download, X, Sparkles } from 'lucide-react'
import { getBackendUrl } from '@/services/api'

interface UpdateDialogProps {
  isOpen: boolean
  currentVersion: string
  latestVersion: string
  downloadUrl: string
  onClose: () => void
  onSkip: () => void
}

export function UpdateDialog({
  isOpen,
  currentVersion,
  latestVersion,
  downloadUrl,
  onClose,
  onSkip,
}: UpdateDialogProps) {
  if (!isOpen) return null

  const handleDownload = async () => {
    try {
      // 通过后端 API 使用系统默认浏览器打开链接
      await fetch(`${getBackendUrl()}/api/system/open-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: downloadUrl }),
      })
    } catch {
      // 如果后端调用失败，回退到 window.open
      window.open(downloadUrl, '_blank')
    }
    onClose()
  }

  return (
    <div className="fixed inset-0 z-[100] bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
        {/* 头部 */}
        <div className="relative p-6 bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 text-white">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 rounded-full hover:bg-white/20 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold">发现新版本</h3>
          </div>
          <p className="text-white/90 text-sm">
            Web RPA 有新版本可用，建议更新以获得最新功能和修复
          </p>
        </div>

        {/* 版本信息 */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="text-center flex-1">
              <p className="text-xs text-gray-500 mb-1">当前版本</p>
              <p className="text-lg font-semibold text-gray-600">{currentVersion}</p>
            </div>
            <div className="px-4">
              <div className="w-8 h-0.5 bg-gradient-to-r from-gray-300 to-blue-400 relative">
                <div className="absolute -right-1 -top-1 w-0 h-0 border-t-4 border-b-4 border-l-6 border-transparent border-l-blue-400" />
              </div>
            </div>
            <div className="text-center flex-1">
              <p className="text-xs text-gray-500 mb-1">最新版本</p>
              <p className="text-lg font-semibold text-blue-600">{latestVersion}</p>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-amber-800">
              <span className="font-medium">更新方式：</span>
              前往GitHub Releases下载最新7z压缩包，解压替换程序所在文件夹中的的所有文件即可完成更新。
            </p>
          </div>

          {/* 按钮 */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              className="flex-1 border-gray-300 text-gray-600 hover:bg-gray-50"
              onClick={onSkip}
            >
              暂不更新
            </Button>
            <Button
              className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4 mr-2" />
              前往下载
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
