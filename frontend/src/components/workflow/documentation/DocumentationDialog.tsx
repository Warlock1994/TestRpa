import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { X, ChevronRight, BookOpen, ArrowUp, Search, Download, FileDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { documents } from './documents'
import { documentContents } from './contents'
import { MarkdownRenderer } from './MarkdownRenderer'
import type { DocumentationDialogProps } from './types'
import { pinyinMatch } from '@/lib/pinyin'

export function DocumentationDialog({ isOpen, onClose }: DocumentationDialogProps) {
  const [selectedDoc, setSelectedDoc] = useState('getting-started')
  const [showScrollTop, setShowScrollTop] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{docId: string, title: string, matches: string[]}>>([])
  const [isSearching, setIsSearching] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  
  // 切换文档时滚动到顶部
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = 0
      setShowScrollTop(false)
    }
  }, [selectedDoc])

  // 监听滚动显示返回顶部按钮
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      setShowScrollTop(scrollContainerRef.current.scrollTop > 300)
    }
  }

  const scrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  // 搜索功能
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    
    if (!query.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }
    
    setIsSearching(true)
    const results: Array<{docId: string, title: string, matches: string[]}> = []
    const queryLower = query.toLowerCase()
    
    for (const doc of documents) {
      const content = documentContents[doc.id] || ''
      const contentLower = content.toLowerCase()
      const titleLower = doc.title.toLowerCase()
      const descLower = doc.description.toLowerCase()
      
      // 检查标题、描述和内容是否匹配
      const titleMatch = titleLower.includes(queryLower) || pinyinMatch(doc.title, query)
      const descMatch = descLower.includes(queryLower) || pinyinMatch(doc.description, query)
      const contentMatch = contentLower.includes(queryLower)
      
      if (titleMatch || descMatch || contentMatch) {
        // 提取匹配的上下文
        const matches: string[] = []
        
        if (contentMatch) {
          // 找到所有匹配位置并提取上下文
          let searchIndex = 0
          let matchCount = 0
          while (searchIndex < contentLower.length && matchCount < 3) {
            const index = contentLower.indexOf(queryLower, searchIndex)
            if (index === -1) break
            
            // 提取前后50个字符作为上下文
            const start = Math.max(0, index - 30)
            const end = Math.min(content.length, index + query.length + 50)
            let context = content.slice(start, end)
            
            // 清理markdown标记
            context = context.replace(/[#*`\[\]()]/g, '').replace(/\n/g, ' ').trim()
            if (start > 0) context = '...' + context
            if (end < content.length) context = context + '...'
            
            matches.push(context)
            searchIndex = index + query.length
            matchCount++
          }
        }
        
        results.push({
          docId: doc.id,
          title: doc.title,
          matches
        })
      }
    }
    
    setSearchResults(results)
  }

  // 清除搜索
  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults([])
    setIsSearching(false)
    searchInputRef.current?.focus()
  }

  // 选择搜索结果
  const selectSearchResult = (docId: string) => {
    setSelectedDoc(docId)
    setIsSearching(false)
    // 不清除搜索词，方便用户继续搜索
  }
  
  // 下载当前文档
  const handleDownloadCurrent = () => {
    const doc = documents.find(d => d.id === selectedDoc)
    if (!doc) return
    
    const content = documentContents[selectedDoc] || ''
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${doc.title.replace(/[🚀⚡📊🧠💡🌐📝🔧🎯📁🔍]/g, '').trim()}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  // 下载全部文档
  const handleDownloadAll = () => {
    let allContent = '# Web RPA 教学文档\n\n'
    allContent += '> 本文档包含 Web RPA 的完整使用指南\n\n'
    allContent += '---\n\n'
    
    documents.forEach((doc, index) => {
      const content = documentContents[doc.id] || ''
      allContent += `\n\n# ${index + 1}. ${doc.title}\n\n`
      allContent += `> ${doc.description}\n\n`
      allContent += content
      allContent += '\n\n---\n\n'
    })
    
    const blob = new Blob([allContent], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'WebRPA完整教学文档.md'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  if (!isOpen) return null
  
  const content = documentContents[selectedDoc] || ''
  const currentDoc = documents.find(d => d.id === selectedDoc)
  
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white text-black rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden animate-scale-in">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold">教学文档</h2>
          </div>
          <div className="flex items-center gap-1">
            <Button 
              variant="outline" 
              size="icon" 
              onClick={handleDownloadCurrent}
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
              title={`下载当前文档：${currentDoc?.title}`}
            >
              <FileDown className="w-4 h-4" />
            </Button>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={handleDownloadAll}
              className="text-green-600 hover:text-green-700 hover:bg-green-50 border-green-200"
              title="下载全部文档为一个文件"
            >
              <Download className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={onClose} className="hover:bg-gray-100 ml-1">
              <X className="w-5 h-5 text-gray-500" />
            </Button>
          </div>
        </div>
        
        <div className="flex-1 flex overflow-hidden rounded-b-lg">
          <div className="w-72 border-r bg-gray-50 flex flex-col rounded-bl-lg">
            {/* 搜索框 */}
            <div className="p-3 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  placeholder="搜索文档内容..."
                  className="w-full pl-9 pr-8 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {searchQuery && (
                  <button
                    onClick={clearSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            
            {/* 搜索结果或文档目录 */}
            <div className="flex-1 p-3 overflow-y-auto">
              {isSearching && searchResults.length > 0 ? (
                <>
                  <h3 className="text-xs font-medium text-gray-500 mb-2">
                    搜索结果 ({searchResults.length})
                  </h3>
                  <div className="space-y-2">
                    {searchResults.map(result => (
                      <button
                        key={result.docId}
                        className="w-full text-left p-2 rounded-lg hover:bg-blue-50 border border-transparent hover:border-blue-200 transition-colors"
                        onClick={() => selectSearchResult(result.docId)}
                      >
                        <div className="text-sm font-medium text-gray-800">{result.title}</div>
                        {result.matches.length > 0 && (
                          <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {result.matches[0]}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </>
              ) : isSearching && searchQuery ? (
                <div className="text-center text-gray-500 py-8">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">未找到相关内容</p>
                  <p className="text-xs mt-1">试试其他关键词</p>
                </div>
              ) : (
                <>
                  <h3 className="text-xs font-medium text-gray-500 mb-2">文档目录</h3>
                  <div className="space-y-1">
                    {documents.map(doc => {
                      const Icon = doc.icon
                      return (
                        <button
                          key={doc.id}
                          className={cn(
                            'w-full flex items-center gap-2 px-2 py-2 rounded-lg text-left transition-colors border',
                            selectedDoc === doc.id 
                              ? 'bg-blue-100 text-blue-700 border-blue-200' 
                              : 'hover:bg-gray-100 text-gray-700 border-transparent hover:border-gray-200'
                          )}
                          onClick={() => setSelectedDoc(doc.id)}
                        >
                          <Icon className="w-4 h-4 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">{doc.title}</div>
                            <div className="text-xs text-gray-500 truncate">{doc.description}</div>
                          </div>
                          {selectedDoc === doc.id && <ChevronRight className="w-4 h-4 shrink-0" />}
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
            <div className="px-4 py-3 border-t text-xs text-gray-400 text-center shrink-0">
              © 2026 青云制作_彭明航 版权所有
            </div>
          </div>
          
          <div className="flex-1 relative">
            <div 
              ref={scrollContainerRef}
              onScroll={handleScroll}
              className="h-full overflow-y-auto"
            >
              <div className="p-8">
                <MarkdownRenderer content={content} />
              </div>
            </div>
            
            {/* 返回顶部按钮 */}
            {showScrollTop && (
              <button
                onClick={scrollToTop}
                className="absolute bottom-6 right-6 w-10 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-110"
                title="返回顶部"
              >
                <ArrowUp className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
