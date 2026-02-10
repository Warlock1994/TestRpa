import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import mermaid from 'mermaid'

interface MarkdownRendererProps {
  content: string
  highlightKeyword?: string
}

// 初始化 Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'system-ui, -apple-system, sans-serif',
  fontSize: 16,
  flowchart: {
    htmlLabels: true,
    curve: 'basis',
    padding: 20,
    nodeSpacing: 80,
    rankSpacing: 80,
  },
})

function highlightText(text: string, keyword: string): ReactNode {
  if (!keyword) return text
  
  const parts: ReactNode[] = []
  const lowerText = text.toLowerCase()
  const lowerKeyword = keyword.toLowerCase()
  let lastIndex = 0
  let partKey = 0
  
  let searchIndex = 0
  while (searchIndex < lowerText.length) {
    const index = lowerText.indexOf(lowerKeyword, searchIndex)
    if (index === -1) break
    
    // 添加关键词前的文本
    if (index > lastIndex) {
      parts.push(text.slice(lastIndex, index))
    }
    
    // 添加高亮的关键词
    parts.push(
      <mark key={partKey++} className="bg-yellow-200 text-gray-900 px-0.5 rounded">
        {text.slice(index, index + keyword.length)}
      </mark>
    )
    
    lastIndex = index + keyword.length
    searchIndex = lastIndex
  }
  
  // 添加剩余文本
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }
  
  return <>{parts}</>
}

function processInlineStyles(text: string, keyword?: string): ReactNode {
  const parts: (string | ReactNode)[] = []
  let remaining = text
  let partKey = 0
  
  while (remaining.length > 0) {
    const codeMatch = remaining.match(/`([^`]+)`/)
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/)
    const matches = [
      codeMatch ? { type: 'code', match: codeMatch, index: codeMatch.index! } : null,
      boldMatch ? { type: 'bold', match: boldMatch, index: boldMatch.index! } : null,
    ].filter(Boolean).sort((a, b) => a!.index - b!.index)
    
    if (matches.length === 0) { 
      parts.push(keyword ? highlightText(remaining, keyword) : remaining)
      break 
    }
    const first = matches[0]!
    if (first.index > 0) {
      const beforeText = remaining.slice(0, first.index)
      parts.push(keyword ? highlightText(beforeText, keyword) : beforeText)
    }
    
    if (first.type === 'code') {
      parts.push(<code key={partKey++} className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600">{first.match![1]}</code>)
    } else if (first.type === 'bold') {
      const boldText = first.match![1]
      parts.push(<strong key={partKey++} className="font-semibold">{keyword ? highlightText(boldText, keyword) : boldText}</strong>)
    }
    remaining = remaining.slice(first.index + first.match![0].length)
  }
  return <>{parts}</>
}

export function MarkdownRenderer({ content, highlightKeyword = '' }: MarkdownRendererProps) {
  const mermaidContainerRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    // 渲染所有 Mermaid 图表
    if (mermaidContainerRef.current) {
      const mermaidElements = mermaidContainerRef.current.querySelectorAll('.mermaid')
      mermaidElements.forEach((element, index) => {
        const id = `mermaid-${Date.now()}-${index}`
        element.id = id
        try {
          mermaid.run({ nodes: [element as HTMLElement] })
        } catch (error) {
          console.error('Mermaid rendering error:', error)
          element.innerHTML = '<div class="text-red-500 text-sm p-4 border border-red-300 rounded">流程图渲染失败</div>'
        }
      })
    }
  }, [content])
  
  const lines = content.split('\n')
  const elements: ReactNode[] = []
  let inCodeBlock = false
  let codeContent = ''
  let codeLanguage = ''
  let inTable = false
  let tableRows: string[][] = []
  let key = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    if (line.startsWith('```')) {
      if (!inCodeBlock) { 
        inCodeBlock = true
        codeContent = ''
        // 提取语言标识
        codeLanguage = line.slice(3).trim().toLowerCase()
      }
      else {
        inCodeBlock = false
        // 如果是 Mermaid 代码块，特殊处理
        if (codeLanguage === 'mermaid') {
          elements.push(
            <div key={key++} className="my-8 flex justify-center">
              <div className="mermaid bg-white p-8 rounded-lg border border-gray-200 shadow-sm w-full max-w-4xl" style={{ minHeight: '300px' }}>
                {codeContent}
              </div>
            </div>
          )
        } else {
          // 普通代码块
          elements.push(
            <pre key={key++} className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4">
              <code className="text-sm font-mono">{codeContent}</code>
            </pre>
          )
        }
        codeLanguage = ''
      }
      continue
    }
    if (inCodeBlock) { codeContent += (codeContent ? '\n' : '') + line; continue }
    
    if (line.startsWith('|')) {
      if (!inTable) { inTable = true; tableRows = [] }
      const cells = line.split('|').slice(1, -1).map(c => c.trim())
      if (!cells.every(c => c.match(/^-+$/))) tableRows.push(cells)
      continue
    } else if (inTable) {
      inTable = false
      elements.push(
        <table key={key++} className="w-full border-collapse my-4">
          <thead><tr className="bg-gray-100">{tableRows[0]?.map((cell, i) => <th key={i} className="border border-gray-300 px-4 py-2 text-left font-semibold">{processInlineStyles(cell, highlightKeyword)}</th>)}</tr></thead>
          <tbody>{tableRows.slice(1).map((row, ri) => <tr key={ri} className="hover:bg-gray-50">{row.map((cell, ci) => <td key={ci} className="border border-gray-300 px-4 py-2">{processInlineStyles(cell, highlightKeyword)}</td>)}</tr>)}</tbody>
        </table>
      )
      tableRows = []
    }
    
    if (line.startsWith('# ')) { elements.push(<h1 key={key++} className="text-3xl font-bold mt-8 mb-4 text-gray-900">{processInlineStyles(line.slice(2), highlightKeyword)}</h1>); continue }
    if (line.startsWith('## ')) { elements.push(<h2 key={key++} className="text-2xl font-bold mt-6 mb-3 text-gray-800 border-b pb-2">{processInlineStyles(line.slice(3), highlightKeyword)}</h2>); continue }
    if (line.startsWith('### ')) { elements.push(<h3 key={key++} className="text-xl font-semibold mt-5 mb-2 text-gray-700">{processInlineStyles(line.slice(4), highlightKeyword)}</h3>); continue }
    if (line.match(/^- /)) { elements.push(<li key={key++} className="ml-6 list-disc my-1">{processInlineStyles(line.slice(2), highlightKeyword)}</li>); continue }
    if (line.match(/^\d+\. /)) { const m = line.match(/^(\d+)\. (.*)/); if (m) elements.push(<li key={key++} className="ml-6 list-decimal my-1">{processInlineStyles(m[2], highlightKeyword)}</li>); continue }
    if (line.match(/^---+$/)) { elements.push(<hr key={key++} className="my-6 border-gray-300" />); continue }
    if (line.trim() === '') continue
    elements.push(<p key={key++} className="my-3 text-gray-700 leading-relaxed">{processInlineStyles(line, highlightKeyword)}</p>)
  }
  
  return <div ref={mermaidContainerRef}>{elements}</div>
}
