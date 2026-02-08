import * as React from 'react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/store/workflowStore'
import type { Variable } from '@/types'

// 从节点配置中提取变量名的字段列表
const VARIABLE_NAME_FIELDS = [
  'variableName',      // 通用存储变量名
  'itemVariable',      // 遍历列表的项变量
  'indexVariable',     // 循环索引变量
  'resultVariable',    // 结果变量
  'outputVariable',    // 输出变量
  'variableNameX',     // X坐标变量名
  'variableNameY',     // Y坐标变量名
  'listVariable',      // 列表变量名
  'dictVariable',      // 字典变量名
  'tableVariable',     // 表格变量名
  'imageVariable',     // 图片变量名
  'textVariable',      // 文本变量名
  'urlVariable',       // URL变量名
  'fileVariable',      // 文件变量名
  'dataVariable',      // 数据变量名
  'responseVariable',  // 响应变量名
  'cookieVariable',    // Cookie变量名
  'headerVariable',    // Header变量名
  'bodyVariable',      // Body变量名
  'statusVariable',    // 状态变量名
  'errorVariable',     // 错误变量名
  'countVariable',     // 计数变量名
  'sumVariable',       // 求和变量名
  'avgVariable',       // 平均值变量名
  'maxVariable',       // 最大值变量名
  'minVariable',       // 最小值变量名
  'connectionVariable', // 数据库连接变量名
  'shareVariable',     // 共享变量名
]

export interface NumberInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'type' | 'value'> {
  value: number | string
  onChange: (value: number | string) => void
  defaultValue?: number
  min?: number
  max?: number
  step?: number
}

/**
 * 数字输入框组件 - 支持变量引用
 * - 输入时允许清空，失焦时保持为空
 * - 支持输入 {变量名} 引用变量
 * - 支持 min/max 限制
 */
const NumberInput = React.forwardRef<HTMLInputElement, NumberInputProps>(
  ({ className, value, onChange, defaultValue = 0, min, max, step, ...props }, ref) => {
    const [displayValue, setDisplayValue] = React.useState<string>(String(value ?? defaultValue))
    const [showSuggestions, setShowSuggestions] = React.useState(false)
    const [selectedIndex, setSelectedIndex] = React.useState(0)
    const [searchText, setSearchText] = React.useState('')
    const [cursorPosition, setCursorPosition] = React.useState(0)
    const inputRef = React.useRef<HTMLInputElement>(null)
    const suggestionsRef = React.useRef<HTMLDivElement>(null)
    
    const globalVariables = useWorkflowStore((state) => state.variables)
    const nodes = useWorkflowStore((state) => state.nodes)

    // 收集所有变量（全局变量 + 模块定义的变量）
    const allVariables = React.useMemo(() => {
      const variableMap = new Map<string, Variable>()
      
      // 添加全局变量
      globalVariables.forEach(v => {
        variableMap.set(v.name, v)
      })
      
      // 从节点配置中提取变量名
      nodes.forEach(node => {
        const data = node.data as Record<string, unknown>
        
        VARIABLE_NAME_FIELDS.forEach(field => {
          const varName = data[field]
          if (typeof varName === 'string' && varName.trim() && !variableMap.has(varName)) {
            // 根据模块类型推断变量类型
            let varType: Variable['type'] = 'string'
            const moduleType = data.moduleType as string
            
            // 推断变量类型
            if (moduleType === 'foreach' && field === 'indexVariable') {
              varType = 'number'
            } else if (moduleType === 'loop' && field === 'indexVariable') {
              varType = 'number'
            } else if (moduleType === 'list_length') {
              varType = 'number'
            } else if (moduleType === 'random_number') {
              varType = 'number'
            } else if (['list_operation', 'list_get', 'dict_keys', 'string_split'].includes(moduleType)) {
              varType = 'array'
            } else if (['dict_operation', 'dict_get', 'json_parse', 'api_request'].includes(moduleType)) {
              varType = 'object'
            } else if (moduleType === 'network_capture') {
              varType = 'array'
            }
            
            variableMap.set(varName, {
              name: varName,
              value: undefined,
              type: varType,
              scope: 'local'
            })
          }
        })
      })
      
      return Array.from(variableMap.values())
    }, [globalVariables, nodes])

    // 合并 ref
    React.useImperativeHandle(ref, () => inputRef.current!)

    // 当外部 value 变化时同步
    React.useEffect(() => {
      setDisplayValue(String(value ?? defaultValue))
    }, [value, defaultValue])

    // 检查是否包含变量引用
    const hasVariableRef = (val: string) => val.includes('{')

    // 过滤变量列表
    const filteredVariables = React.useMemo(() => {
      if (!searchText) return allVariables
      const lower = searchText.toLowerCase()
      return allVariables.filter(v => v.name.toLowerCase().includes(lower))
    }, [allVariables, searchText])

    // 检测是否在输入变量引用
    const checkVariableInput = React.useCallback((inputValue: string, cursorPos: number) => {
      // 从光标位置向前查找 {
      let braceStart = -1
      for (let i = cursorPos - 1; i >= 0; i--) {
        if (inputValue[i] === '}') break
        if (inputValue[i] === '{') {
          braceStart = i
          break
        }
      }

      if (braceStart !== -1) {
        const textAfterBrace = inputValue.slice(braceStart + 1, cursorPos)
        // 检查是否包含非法字符（如空格后的内容）
        if (!textAfterBrace.includes('}')) {
          setSearchText(textAfterBrace)
          setShowSuggestions(true)
          setSelectedIndex(0)
          return
        }
      }

      setShowSuggestions(false)
      setSearchText('')
    }, [])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value
      const pos = e.target.selectionStart || 0
      setCursorPosition(pos)
      setDisplayValue(inputValue)
      
      // 检查是否在输入变量
      checkVariableInput(inputValue, pos)

      // 如果包含变量引用，直接传递字符串
      if (hasVariableRef(inputValue)) {
        onChange(inputValue)
      } else {
        // 尝试解析为数字
        const num = parseFloat(inputValue)
        if (!isNaN(num)) {
          onChange(num)
        } else if (inputValue === '' || inputValue === '-') {
          // 允许空字符串和负号
          onChange(inputValue)
        }
      }
    }

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      // 延迟关闭建议，以便点击建议项
      setTimeout(() => {
        setShowSuggestions(false)
      }, 150)

      // 如果包含变量引用，不做数字处理
      if (hasVariableRef(displayValue)) {
        props.onBlur?.(e)
        return
      }

      // 如果为空字符串，保持为空，不自动填充默认值
      if (displayValue === '' || displayValue === '-') {
        onChange('')
        props.onBlur?.(e)
        return
      }

      let finalValue: number | string = parseFloat(displayValue)
      
      // 如果不是有效数字，清空输入框
      if (isNaN(finalValue)) {
        setDisplayValue('')
        onChange('')
        props.onBlur?.(e)
        return
      }
      
      // 应用 min/max 限制
      if (typeof finalValue === 'number') {
        if (min !== undefined && finalValue < min) {
          finalValue = min
        }
        if (max !== undefined && finalValue > max) {
          finalValue = max
        }
      }
      
      setDisplayValue(String(finalValue))
      onChange(finalValue)
      
      props.onBlur?.(e)
    }

    const insertVariable = (varName: string) => {
      const input = inputRef.current
      if (!input) return

      // 找到 { 的位置
      let braceStart = -1
      for (let i = cursorPosition - 1; i >= 0; i--) {
        if (displayValue[i] === '{') {
          braceStart = i
          break
        }
      }

      if (braceStart !== -1) {
        const before = displayValue.slice(0, braceStart + 1)
        const after = displayValue.slice(cursorPosition)
        const newValue = before + varName + '}' + after
        setDisplayValue(newValue)
        onChange(newValue)
        
        // 设置光标位置到变量名后面
        setTimeout(() => {
          const newPos = braceStart + varName.length + 2
          input.setSelectionRange(newPos, newPos)
          input.focus()
        }, 0)
      }

      setShowSuggestions(false)
      setSearchText('')
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!showSuggestions || filteredVariables.length === 0) {
        props.onKeyDown?.(e)
        return
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex(prev => (prev + 1) % filteredVariables.length)
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex(prev => (prev - 1 + filteredVariables.length) % filteredVariables.length)
          break
        case 'Enter':
        case 'Tab':
          e.preventDefault()
          if (filteredVariables[selectedIndex]) {
            insertVariable(filteredVariables[selectedIndex].name)
          }
          break
        case 'Escape':
          setShowSuggestions(false)
          break
        default:
          props.onKeyDown?.(e)
      }
    }

    const handleClick = (e: React.MouseEvent<HTMLInputElement>) => {
      const cursorPos = e.currentTarget.selectionStart || 0
      setCursorPosition(cursorPos)
      checkVariableInput(displayValue, cursorPos)
    }

    // 格式化变量值显示
    const formatValue = (val: unknown): string => {
      if (val === null || val === undefined) return 'null'
      if (typeof val === 'object') {
        try {
          const str = JSON.stringify(val)
          return str.length > 30 ? str.slice(0, 30) + '...' : str
        } catch {
          return String(val)
        }
      }
      const str = String(val)
      return str.length > 30 ? str.slice(0, 30) + '...' : str
    }

    // 获取变量类型颜色
    const getTypeColor = (type: string) => {
      switch (type) {
        case 'string': return 'text-green-600'
        case 'number': return 'text-blue-600'
        case 'boolean': return 'text-purple-600'
        case 'array': return 'text-orange-600'
        case 'object': return 'text-cyan-600'
        default: return 'text-gray-600'
      }
    }

    // 当选中索引变化时，自动滚动到选中项
    React.useEffect(() => {
      if (!showSuggestions || selectedIndex < 0 || selectedIndex >= filteredVariables.length) {
        return
      }

      const container = suggestionsRef.current
      if (!container) {
        return
      }

      // 使用 querySelector 直接找到选中的元素
      const selectedElement = container.querySelector(`[data-index="${selectedIndex}"]`) as HTMLElement
      if (!selectedElement) {
        return
      }

      // 获取容器和元素的位置信息
      const containerRect = container.getBoundingClientRect()
      const elementRect = selectedElement.getBoundingClientRect()

      // 如果元素在可视区域下方
      if (elementRect.bottom > containerRect.bottom) {
        const scrollAmount = elementRect.bottom - containerRect.bottom
        container.scrollTop += scrollAmount
      }
      // 如果元素在可视区域上方
      else if (elementRect.top < containerRect.top) {
        const scrollAmount = containerRect.top - elementRect.top
        container.scrollTop -= scrollAmount
      }
    }, [selectedIndex, showSuggestions, filteredVariables])

    return (
      <div className="relative">
        <input
          type="text"
          inputMode={hasVariableRef(displayValue) ? 'text' : 'numeric'}
          className={cn(
            'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
          ref={inputRef}
          value={displayValue}
          onChange={handleChange}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          onClick={handleClick}
          {...props}
        />
        
        {/* 变量提示下拉框 */}
        {showSuggestions && filteredVariables.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-50 mt-1 w-full max-h-48 overflow-auto rounded-md border border-gray-200 bg-white shadow-lg animate-scale-in"
          >
            <div className="p-1">
              {filteredVariables.map((variable, index) => (
                <div
                  key={variable.name}
                  data-index={index}
                  className={cn(
                    'flex items-center justify-between px-2 py-1.5 text-sm rounded cursor-pointer transition-colors',
                    index === selectedIndex ? 'bg-blue-100 text-blue-900' : 'hover:bg-muted'
                  )}
                  onClick={() => insertVariable(variable.name)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-blue-600">{variable.name}</span>
                    <span className={cn('text-xs', getTypeColor(variable.type))}>
                      ({variable.type})
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground truncate max-w-[120px]">
                    {formatValue(variable.value)}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t px-2 py-1 text-[10px] text-muted-foreground bg-muted/50">
              ↑↓ 选择 · Enter 确认 · Esc 关闭
            </div>
          </div>
        )}
        
        {/* 无匹配变量时的提示 */}
        {showSuggestions && filteredVariables.length === 0 && (
          <div className="absolute z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg p-3 text-sm animate-scale-in">
            {allVariables.length === 0 ? (
              <div className="text-muted-foreground">
                <p className="font-medium text-amber-600">暂无可用变量</p>
                <p className="text-xs mt-1">请先在"全局变量"面板中添加变量，或在模块中配置"存储变量名"</p>
              </div>
            ) : (
              <div className="text-muted-foreground">
                未找到匹配的变量 "<span className="text-blue-600">{searchText}</span>"
              </div>
            )}
          </div>
        )}
      </div>
    )
  }
)
NumberInput.displayName = 'NumberInput'

export { NumberInput }
