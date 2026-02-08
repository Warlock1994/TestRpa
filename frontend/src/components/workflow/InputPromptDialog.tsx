import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { socketService } from '@/services/socket'
import { X, List, Hash, Type, Lock, AlignLeft, File, Folder, CheckSquare, SlidersHorizontal, ListChecks } from 'lucide-react'

interface PromptData {
  requestId: string
  variableName: string
  title: string
  message: string
  defaultValue: string
  inputMode: 'single' | 'multiline' | 'number' | 'integer' | 'password' | 'list' | 'file' | 'folder' | 'checkbox' | 'slider_int' | 'slider_float' | 'select_single' | 'select_multiple'
  minValue?: number
  maxValue?: number
  maxLength?: number
  required?: boolean
  selectOptions?: string[]  // 列表选择的选项
}

export function InputPromptDialog() {
  const [promptData, setPromptData] = useState<PromptData | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [checkboxValue, setCheckboxValue] = useState(false)
  const [sliderValue, setSliderValue] = useState(0)
  const [selectedItems, setSelectedItems] = useState<string[]>([])
  const [error, setError] = useState('')

  const handlePromptRequest = useCallback((data: PromptData) => {
    try {
      setPromptData(data)
      setInputValue(data.defaultValue || '')
      // 复选框模式：解析默认值为布尔值
      if (data.inputMode === 'checkbox') {
        const defaultBool = data.defaultValue?.toLowerCase() === 'true' || data.defaultValue === '1'
        setCheckboxValue(defaultBool)
      } else {
        setCheckboxValue(false)
      }
      // 滑动条模式：解析默认值为数字
      if (data.inputMode === 'slider_int' || data.inputMode === 'slider_float') {
        const defaultNum = parseFloat(data.defaultValue) || data.minValue || 0
        setSliderValue(defaultNum)
      } else {
        setSliderValue(0)
      }
      // 列表选择模式：解析默认值为选中项
      if (data.inputMode === 'select_single' || data.inputMode === 'select_multiple') {
        // 确保 selectOptions 是字符串数组
        if (data.selectOptions && !Array.isArray(data.selectOptions)) {
          console.error('[InputPrompt] selectOptions 不是数组:', data.selectOptions)
          data.selectOptions = []
        }
        
        if (data.defaultValue) {
          try {
            const parsed = JSON.parse(data.defaultValue)
            setSelectedItems(Array.isArray(parsed) ? parsed : [parsed])
          } catch {
            setSelectedItems(data.defaultValue ? [data.defaultValue] : [])
          }
        } else {
          setSelectedItems([])
        }
      } else {
        setSelectedItems([])
      }
      setError('')
    } catch (err) {
      console.error('[InputPrompt] 处理输入请求失败:', err)
      setError('加载输入框失败，请检查配置')
    }
  }, [])

  useEffect(() => {
    socketService.setInputPromptCallback(handlePromptRequest)
    return () => {
      socketService.setInputPromptCallback(null)
    }
  }, [handlePromptRequest])

  const validateInput = (): boolean => {
    if (!promptData) return false
    
    const { inputMode, required, minValue, maxValue, maxLength } = promptData
    const trimmedValue = inputValue.trim()
    
    // 必填检查
    if (required !== false && !trimmedValue) {
      setError('此项为必填')
      return false
    }
    
    // 文件/文件夹模式不需要额外验证
    if (inputMode === 'file' || inputMode === 'folder') {
      setError('')
      return true
    }
    
    // 数字模式验证
    if (inputMode === 'number' || inputMode === 'integer') {
      if (trimmedValue) {
        const num = Number(trimmedValue)
        if (isNaN(num)) {
          setError(inputMode === 'integer' ? '请输入有效的整数' : '请输入有效的数字')
          return false
        }
        if (inputMode === 'integer' && !Number.isInteger(num)) {
          setError('请输入整数，不能包含小数')
          return false
        }
        if (minValue != null && num < minValue) {
          setError(`数值不能小于 ${minValue}`)
          return false
        }
        if (maxValue != null && num > maxValue) {
          setError(`数值不能大于 ${maxValue}`)
          return false
        }
      }
      // 数字模式不检查字符长度
      setError('')
      return true
    }
    
    // 长度检查（仅对非数字模式）
    if (maxLength != null && maxLength > 0 && trimmedValue.length > maxLength) {
      setError(`长度不能超过 ${maxLength} 个字符`)
      return false
    }
    
    setError('')
    return true
  }

  // 选择文件
  const handleSelectFile = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system/select-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: promptData?.title || '选择文件' })
      })
      const result = await response.json()
      if (result.success && result.path) {
        setInputValue(result.path)
        setError('')
      }
    } catch (err) {
      console.error('选择文件失败:', err)
      setError('选择文件失败')
    }
  }

  // 选择文件夹
  const handleSelectFolder = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system/select-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: promptData?.title || '选择文件夹' })
      })
      const result = await response.json()
      if (result.success && result.path) {
        setInputValue(result.path)
        setError('')
      }
    } catch (err) {
      console.error('选择文件夹失败:', err)
      setError('选择文件夹失败')
    }
  }

  const handleSubmit = () => {
    if (!validateInput()) return
    
    if (promptData) {
      let resultValue: string = inputValue
      
      // 复选框模式：返回布尔值的字符串表示
      if (promptData.inputMode === 'checkbox') {
        resultValue = checkboxValue ? 'true' : 'false'
      }
      // 滑动条模式：返回数字的字符串表示
      else if (promptData.inputMode === 'slider_int' || promptData.inputMode === 'slider_float') {
        resultValue = sliderValue.toString()
      }
      // 列表单选模式：返回选中的单个项
      else if (promptData.inputMode === 'select_single') {
        if (selectedItems.length === 0) {
          setError('请至少选择一项')
          return
        }
        resultValue = selectedItems[0]
      }
      // 列表多选模式：返回选中项的 JSON 数组
      else if (promptData.inputMode === 'select_multiple') {
        if (selectedItems.length === 0) {
          setError('请至少选择一项')
          return
        }
        resultValue = JSON.stringify(selectedItems)
      }
      // 数字模式转换
      else if ((promptData.inputMode === 'number' || promptData.inputMode === 'integer') && inputValue.trim()) {
        resultValue = inputValue.trim()
      }
      
      socketService.sendInputResult(promptData.requestId, resultValue)
      setPromptData(null)
      setInputValue('')
      setCheckboxValue(false)
      setSliderValue(0)
      setSelectedItems([])
      setError('')
    }
  }

  const handleCancel = () => {
    if (promptData) {
      socketService.sendInputResult(promptData.requestId, null)
      setPromptData(null)
      setInputValue('')
      setCheckboxValue(false)
      setSliderValue(0)
      setSelectedItems([])
      setError('')
    }
  }

  if (!promptData) return null

  const { inputMode } = promptData
  const isListMode = inputMode === 'list'
  const isMultiline = inputMode === 'multiline' || isListMode
  const isNumber = inputMode === 'number' || inputMode === 'integer'
  const isPassword = inputMode === 'password'
  const isFilePicker = inputMode === 'file'
  const isFolderPicker = inputMode === 'folder'
  const isCheckbox = inputMode === 'checkbox'
  const isSlider = inputMode === 'slider_int' || inputMode === 'slider_float'
  const isSliderInt = inputMode === 'slider_int'
  const isSelectSingle = inputMode === 'select_single'
  const isSelectMultiple = inputMode === 'select_multiple'
  const isSelect = isSelectSingle || isSelectMultiple
  const lineCount = inputValue.split('\n').filter(line => line.trim()).length
  
  // 列表选择的切换函数
  const toggleSelectItem = (item: string) => {
    if (isSelectSingle) {
      setSelectedItems([item])
    } else if (isSelectMultiple) {
      setSelectedItems(prev => 
        prev.includes(item) 
          ? prev.filter(i => i !== item)
          : [...prev, item]
      )
    }
  }

  const getModeIcon = () => {
    switch (inputMode) {
      case 'list': return <List className="w-4 h-4 text-blue-500" />
      case 'number':
      case 'integer': return <Hash className="w-4 h-4 text-green-500" />
      case 'password': return <Lock className="w-4 h-4 text-orange-500" />
      case 'multiline': return <AlignLeft className="w-4 h-4 text-purple-500" />
      case 'file': return <File className="w-4 h-4 text-cyan-500" />
      case 'folder': return <Folder className="w-4 h-4 text-yellow-500" />
      case 'checkbox': return <CheckSquare className="w-4 h-4 text-indigo-500" />
      case 'slider_int':
      case 'slider_float': return <SlidersHorizontal className="w-4 h-4 text-pink-500" />
      case 'select_single':
      case 'select_multiple': return <ListChecks className="w-4 h-4 text-teal-500" />
      default: return <Type className="w-4 h-4 text-gray-500" />
    }
  }

  const getModeLabel = () => {
    switch (inputMode) {
      case 'list': return '列表输入'
      case 'number': return '数字输入'
      case 'integer': return '整数输入'
      case 'password': return '密码输入'
      case 'multiline': return '多行输入'
      case 'file': return '文件选择'
      case 'folder': return '文件夹选择'
      case 'checkbox': return '复选框'
      case 'slider_int': return '滑动条（整数）'
      case 'slider_float': return '滑动条（小数）'
      case 'select_single': return '列表单选'
      case 'select_multiple': return '列表多选'
      default: return '文本输入'
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white text-black border border-gray-200 rounded-xl shadow-2xl w-full max-w-md p-4 overflow-hidden animate-scale-in">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            {getModeIcon()}
            <h3 className="font-semibold text-gray-900">{promptData.title || '输入'}</h3>
            <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">{getModeLabel()}</span>
          </div>
          <Button variant="ghost" size="icon" className="text-gray-600 hover:text-gray-900" onClick={handleCancel}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-gray-700">{promptData.message || '请输入值:'}</Label>
            {isSelect ? (
              <>
                <div className="space-y-2 p-3 bg-gray-50 rounded-lg border border-gray-200 max-h-80 overflow-y-auto">
                  {promptData.selectOptions && promptData.selectOptions.length > 0 ? (
                    promptData.selectOptions.map((option, index) => {
                      const isSelected = selectedItems.includes(option)
                      return (
                        <div
                          key={index}
                          onClick={() => toggleSelectItem(option)}
                          className={`
                            flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-all
                            ${isSelected 
                              ? 'border-blue-500 bg-blue-50' 
                              : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50'
                            }
                          `}
                        >
                          <div className={`
                            flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center
                            ${isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300 bg-white'}
                          `}>
                            {isSelected && (
                              <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </div>
                          <span className={`flex-1 ${isSelected ? 'text-blue-700 font-medium' : 'text-gray-700'}`}>
                            {option}
                          </span>
                          {isSelectMultiple && isSelected && (
                            <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
                              {selectedItems.indexOf(option) + 1}
                            </span>
                          )}
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center text-gray-400 py-8">
                      <ListChecks className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>没有可选项</p>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500">
                  {isSelectSingle ? (
                    <>
                      已选择: <code className="bg-gray-100 px-1 rounded">
                        {selectedItems.length > 0 ? selectedItems[0] : '无'}
                      </code>
                      <span className="ml-2 text-gray-400">→ 变量: {promptData.variableName}</span>
                    </>
                  ) : (
                    <>
                      已选择 <code className="bg-blue-100 text-blue-700 px-1 rounded font-medium">
                        {selectedItems.length}
                      </code> 项
                      <span className="ml-2 text-gray-400">→ 变量: {promptData.variableName}</span>
                    </>
                  )}
                </p>
              </>
            ) : isSlider ? (
              <>
                <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {promptData.minValue ?? 0}
                    </span>
                    <span className="text-2xl font-bold text-blue-600">
                      {isSliderInt ? Math.round(sliderValue) : sliderValue.toFixed(2)}
                    </span>
                    <span className="text-sm text-gray-600">
                      {promptData.maxValue ?? 100}
                    </span>
                  </div>
                  <div className="relative">
                    {/* 背景轨道 */}
                    <div className="absolute w-full h-2 bg-gray-300 rounded-lg" style={{ top: '50%', transform: 'translateY(-50%)' }}></div>
                    {/* 进度条 - 实时跟随（无过渡动画） */}
                    <div 
                      className="absolute h-2 rounded-lg"
                      style={{ 
                        top: '50%', 
                        transform: 'translateY(-50%)',
                        width: `${((sliderValue - (promptData.minValue ?? 0)) / ((promptData.maxValue ?? 100) - (promptData.minValue ?? 0))) * 100}%`,
                        background: 'linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%)'
                      }}
                    ></div>
                    {/* 滑块 */}
                    <input
                      type="range"
                      min={promptData.minValue ?? 0}
                      max={promptData.maxValue ?? 100}
                      step={isSliderInt ? 1 : 0.01}
                      value={sliderValue}
                      onChange={(e) => setSliderValue(parseFloat(e.target.value))}
                      className="relative w-full h-2 bg-transparent appearance-none cursor-pointer z-10"
                      style={{
                        WebkitAppearance: 'none',
                        appearance: 'none',
                      }}
                      autoFocus
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>拖动滑块选择数值</span>
                    <span className="text-gray-400">
                      {isSliderInt ? '整数' : '小数（精度0.01）'}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  将设置变量: <code className="bg-gray-100 px-1 rounded">{promptData.variableName}</code>
                  <span className="ml-2 text-gray-400">
                    = <code className="text-blue-600">{isSliderInt ? Math.round(sliderValue) : sliderValue.toFixed(2)}</code>
                  </span>
                </p>
                <style>{`
                  input[type="range"]::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
                    cursor: pointer;
                    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
                    transition: all 0.2s ease;
                  }
                  input[type="range"]::-webkit-slider-thumb:hover {
                    transform: scale(1.2);
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6);
                  }
                  input[type="range"]::-webkit-slider-thumb:active {
                    transform: scale(1.1);
                  }
                  input[type="range"]::-moz-range-thumb {
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
                    cursor: pointer;
                    border: none;
                    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
                    transition: all 0.2s ease;
                  }
                  input[type="range"]::-moz-range-thumb:hover {
                    transform: scale(1.2);
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6);
                  }
                  input[type="range"]::-moz-range-thumb:active {
                    transform: scale(1.1);
                  }
                  input[type="range"]:focus {
                    outline: none;
                  }
                  input[type="range"]:focus::-webkit-slider-thumb {
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2), 0 2px 8px rgba(59, 130, 246, 0.4);
                  }
                  input[type="range"]:focus::-moz-range-thumb {
                    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2), 0 2px 8px rgba(59, 130, 246, 0.4);
                  }
                `}</style>
              </>
            ) : isCheckbox ? (
              <>
                <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <input
                    type="checkbox"
                    id="checkbox-input"
                    checked={checkboxValue}
                    onChange={(e) => setCheckboxValue(e.target.checked)}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 cursor-pointer"
                    autoFocus
                  />
                  <Label 
                    htmlFor="checkbox-input" 
                    className="text-gray-700 cursor-pointer select-none flex-1"
                  >
                    {promptData.message || '请选择'}
                  </Label>
                  <span className={`text-sm font-medium px-2 py-1 rounded ${checkboxValue ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600'}`}>
                    {checkboxValue ? '已选中' : '未选中'}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  将设置变量: <code className="bg-gray-100 px-1 rounded">{promptData.variableName}</code>
                  <span className="ml-2 text-gray-400">
                    = <code className={checkboxValue ? 'text-green-600' : 'text-gray-600'}>{checkboxValue ? 'true' : 'false'}</code>
                  </span>
                </p>
              </>
            ) : isFilePicker || isFolderPicker ? (
              <>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    value={inputValue}
                    onChange={(e) => { setInputValue(e.target.value); setError('') }}
                    placeholder={isFilePicker ? "选择或输入文件路径..." : "选择或输入文件夹路径..."}
                    className={`flex-1 bg-white text-black ${error ? 'border-red-500' : 'border-gray-300'}`}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleSubmit()
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="border-gray-300 text-gray-700 hover:bg-gray-100 shrink-0"
                    onClick={isFilePicker ? handleSelectFile : handleSelectFolder}
                  >
                    {isFilePicker ? <File className="w-4 h-4 mr-1" /> : <Folder className="w-4 h-4 mr-1" />}
                    浏览
                  </Button>
                </div>
                <p className="text-xs text-gray-500">
                  将设置变量: <code className="bg-gray-100 px-1 rounded">{promptData.variableName}</code>
                  <span className="ml-2 text-gray-400">
                    {isFilePicker ? '点击"浏览"选择文件，或直接输入路径' : '点击"浏览"选择文件夹，或直接输入路径'}
                  </span>
                </p>
              </>
            ) : isMultiline ? (
              <>
                <textarea
                  value={inputValue}
                  onChange={(e) => { setInputValue(e.target.value); setError('') }}
                  placeholder={isListMode ? "每行输入一个值..." : "请输入内容..."}
                  className={`w-full h-40 px-3 py-2 bg-white text-black border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 ${error ? 'border-red-500' : 'border-gray-300'}`}
                  autoFocus
                />
                {isListMode && (
                  <p className="text-xs text-gray-500">
                    每行一个值，当前 {lineCount} 项 → 变量: <code className="bg-gray-100 px-1 rounded">{promptData.variableName}</code>
                  </p>
                )}
              </>
            ) : (
              <>
                <Input
                  type={isPassword ? 'password' : isNumber ? 'number' : 'text'}
                  value={inputValue}
                  onChange={(e) => { setInputValue(e.target.value); setError('') }}
                  placeholder={isNumber ? "请输入数字..." : "请输入..."}
                  className={`bg-white text-black ${error ? 'border-red-500' : 'border-gray-300'}`}
                  autoFocus
                  step={inputMode === 'integer' ? '1' : 'any'}
                  min={promptData.minValue}
                  max={promptData.maxValue}
                  maxLength={promptData.maxLength}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSubmit()
                    }
                  }}
                />
                <p className="text-xs text-gray-500">
                  将设置变量: <code className="bg-gray-100 px-1 rounded">{promptData.variableName}</code>
                  {isNumber && promptData.minValue !== undefined && promptData.maxValue !== undefined && (
                    <span className="ml-2">范围: {promptData.minValue} ~ {promptData.maxValue}</span>
                  )}
                </p>
              </>
            )}
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100" onClick={handleCancel}>
              取消
            </Button>
            <Button className="bg-blue-600 text-white hover:bg-blue-700" onClick={handleSubmit}>
              确定
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
