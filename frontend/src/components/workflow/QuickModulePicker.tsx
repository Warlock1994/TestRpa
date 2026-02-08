import { useState, useMemo } from 'react'
import { X, Search, Star } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useModuleStatsStore } from '@/store/moduleStatsStore'
import { pinyinMatch } from '@/lib/pinyin'
import type { ModuleType } from '@/types'

interface QuickModulePickerProps {
  isOpen: boolean
  position: { x: number; y: number }
  onClose: () => void
  onSelectModule: (moduleType: ModuleType) => void
  availableModules: Array<{
    type: ModuleType
    label: string
    category: string
    icon: React.ElementType
  }>
  favoritesOnly?: boolean // 是否仅显示收藏的模块
}

export function QuickModulePicker({
  isOpen,
  position,
  onClose,
  onSelectModule,
  availableModules,
  favoritesOnly = false,
}: QuickModulePickerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const { getStats, toggleFavorite, getSortedModules, stats } = useModuleStatsStore()
  
  // 在组件挂载时获取一次排序结果并缓存（只在浏览器刷新时排序）
  const [sortedModulesCache] = useState(() => {
    // 按分类分组
    const grouped = availableModules.reduce((acc, module) => {
      if (!acc[module.category]) {
        acc[module.category] = []
      }
      acc[module.category].push(module)
      return acc
    }, {} as Record<string, typeof availableModules>)
    
    // 对每个分类内的模块进行排序并缓存
    Object.keys(grouped).forEach((category) => {
      const moduleTypes = grouped[category].map((m) => m.type)
      const sorted = getSortedModules(moduleTypes)
      grouped[category] = sorted.map((type) =>
        grouped[category].find((m) => m.type === type)!
      )
    })
    
    return grouped
  })
  
  // 过滤模块（使用缓存的排序结果，但收藏状态需要实时响应，支持拼音搜索）
  const filteredModules = useMemo(() => {
    let grouped = { ...sortedModulesCache }
    
    // 如果仅显示收藏，过滤出收藏的模块（依赖 stats 实时更新）
    if (favoritesOnly) {
      Object.keys(grouped).forEach((category) => {
        grouped[category] = grouped[category].filter((m) => getStats(m.type).isFavorite)
      })
      // 移除空分类
      Object.keys(grouped).forEach((category) => {
        if (grouped[category].length === 0) {
          delete grouped[category]
        }
      })
    }
    
    // 搜索过滤（支持拼音和拼音首字母）
    if (searchTerm) {
      const term = searchTerm.trim()
      Object.keys(grouped).forEach((category) => {
        grouped[category] = grouped[category].filter((m) => {
          // 使用拼音匹配标签名
          if (pinyinMatch(m.label, term)) return true
          
          // 匹配分类名（也支持拼音）
          if (pinyinMatch(m.category, term)) return true
          
          // 匹配模块类型（英文）
          if (m.type.toLowerCase().includes(term.toLowerCase())) return true
          
          return false
        })
      })
      // 移除空分类
      Object.keys(grouped).forEach((category) => {
        if (grouped[category].length === 0) {
          delete grouped[category]
        }
      })
    }
    
    return grouped
  }, [searchTerm, sortedModulesCache, favoritesOnly, getStats, stats])
  
  const handleModuleClick = (moduleType: ModuleType) => {
    onSelectModule(moduleType)
    onClose()
  }
  
  const handleToggleFavorite = (e: React.MouseEvent, moduleType: ModuleType) => {
    e.stopPropagation()
    toggleFavorite(moduleType)
  }
  
  if (!isOpen) return null
  
  return (
    <>
      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />
      
      {/* 弹窗 */}
      <div
        className="fixed z-50 bg-white rounded-lg shadow-2xl border border-gray-200 w-[500px] max-h-[600px] flex flex-col"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
          transform: 'translate(-50%, -50%)',
        }}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-t-lg">
          <h3 className="font-semibold text-gray-900">
            {favoritesOnly ? '收藏的模块' : '快速选择模块'}
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/80 rounded transition-colors"
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
              placeholder="搜索模块..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
        </div>
        
        {/* 模块列表 */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {Object.keys(filteredModules).length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              {favoritesOnly ? (
                <div className="space-y-2">
                  <div>暂无收藏的模块</div>
                  <div className="text-xs">
                    点击模块右侧的 <Star className="w-3 h-3 inline" /> 图标可收藏模块
                  </div>
                </div>
              ) : (
                '无搜索结果'
              )}
            </div>
          ) : (
            Object.entries(filteredModules).map(([category, modules]) => (
              <div key={category}>
                <div className="text-xs font-semibold text-gray-500 mb-2 px-2">
                  {category}
                </div>
                <div className="space-y-1">
                  {modules.map((module) => {
                    const stats = getStats(module.type)
                    const Icon = module.icon
                    
                    return (
                      <button
                        key={module.type}
                        onClick={() => handleModuleClick(module.type)}
                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-blue-50 transition-colors text-left group"
                      >
                        <Icon className="w-5 h-5 text-gray-600 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {module.label}
                          </div>
                        </div>
                        <button
                          onClick={(e) => handleToggleFavorite(e, module.type)}
                          className={cn(
                            'p-1 rounded transition-colors flex-shrink-0',
                            stats.isFavorite
                              ? 'text-yellow-500 hover:text-yellow-600'
                              : 'text-gray-300 hover:text-yellow-500 opacity-0 group-hover:opacity-100'
                          )}
                        >
                          <Star
                            className={cn(
                              'w-4 h-4',
                              stats.isFavorite && 'fill-current'
                            )}
                          />
                        </button>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))
          )}
        </div>
        
        {/* 底部提示 */}
        <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500 text-center rounded-b-lg">
          {favoritesOnly ? (
            <>双击画布空白区域快速创建收藏的模块 · 右键显示所有模块</>
          ) : (
            <>右键画布空白区域可快速打开此面板</>
          )}
        </div>
      </div>
    </>
  )
}
