import type { ReactNode } from 'react'

function processInlineStyles(text: string): ReactNode {
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
    
    if (matches.length === 0) { parts.push(remaining); break }
    const first = matches[0]!
    if (first.index > 0) parts.push(remaining.slice(0, first.index))
    
    if (first.type === 'code') {
      parts.push(<code key={partKey++} className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600">{first.match![1]}</code>)
    } else if (first.type === 'bold') {
      parts.push(<strong key={partKey++} className="font-semibold">{first.match![1]}</strong>)
    }
    remaining = remaining.slice(first.index + first.match![0].length)
  }
  return <>{parts}</>
}

export function MarkdownRenderer({ content }: { content: string }) {
  const lines = content.split('\n')
  const elements: ReactNode[] = []
  let inCodeBlock = false
  let codeContent = ''
  let inTable = false
  let tableRows: string[][] = []
  let key = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    if (line.startsWith('```')) {
      if (!inCodeBlock) { inCodeBlock = true; codeContent = '' }
      else {
        inCodeBlock = false
        elements.push(<pre key={key++} className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code className="text-sm font-mono">{codeContent}</code></pre>)
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
          <thead><tr className="bg-gray-100">{tableRows[0]?.map((cell, i) => <th key={i} className="border border-gray-300 px-4 py-2 text-left font-semibold">{cell}</th>)}</tr></thead>
          <tbody>{tableRows.slice(1).map((row, ri) => <tr key={ri} className="hover:bg-gray-50">{row.map((cell, ci) => <td key={ci} className="border border-gray-300 px-4 py-2">{processInlineStyles(cell)}</td>)}</tr>)}</tbody>
        </table>
      )
      tableRows = []
    }
    
    if (line.startsWith('# ')) { elements.push(<h1 key={key++} className="text-3xl font-bold mt-8 mb-4 text-gray-900">{processInlineStyles(line.slice(2))}</h1>); continue }
    if (line.startsWith('## ')) { elements.push(<h2 key={key++} className="text-2xl font-bold mt-6 mb-3 text-gray-800 border-b pb-2">{processInlineStyles(line.slice(3))}</h2>); continue }
    if (line.startsWith('### ')) { elements.push(<h3 key={key++} className="text-xl font-semibold mt-5 mb-2 text-gray-700">{processInlineStyles(line.slice(4))}</h3>); continue }
    if (line.match(/^- /)) { elements.push(<li key={key++} className="ml-6 list-disc my-1">{processInlineStyles(line.slice(2))}</li>); continue }
    if (line.match(/^\d+\. /)) { const m = line.match(/^(\d+)\. (.*)/); if (m) elements.push(<li key={key++} className="ml-6 list-decimal my-1">{processInlineStyles(m[2])}</li>); continue }
    if (line.match(/^---+$/)) { elements.push(<hr key={key++} className="my-6 border-gray-300" />); continue }
    if (line.trim() === '') continue
    elements.push(<p key={key++} className="my-3 text-gray-700 leading-relaxed">{processInlineStyles(line)}</p>)
  }
  
  return <>{elements}</>
}
