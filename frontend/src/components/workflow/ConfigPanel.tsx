import { useWorkflowStore, moduleTypeLabels, getModuleDefaultTimeout, type NodeData } from '@/store/workflowStore'
import { useGlobalConfigStore } from '@/store/globalConfigStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { NumberInput } from '@/components/ui/number-input'
import { Label } from '@/components/ui/label'
import { SelectNative as Select } from '@/components/ui/select-native'
import { Button } from '@/components/ui/button'
import { VariableInput } from '@/components/ui/variable-input'
import { Trash2, Crosshair, Loader2, Ban, ChevronLeft, ChevronRight, Settings } from 'lucide-react'
import { useState, useCallback, useRef, useEffect } from 'react'
import { elementPickerApi } from '@/services/api'

// 导入拆分的配置组件
import { ReadExcelConfig } from './config-panels/ReadExcelConfig'
import { SimilarSelectorDialog } from './config-panels/SimilarSelectorDialog'
import { UrlInputDialog } from './config-panels/UrlInputDialog'
import {
  OpenPageConfig,
  ClickElementConfig,
  HoverElementConfig,
  InputTextConfig,
  GetElementInfoConfig,
  WaitConfig,
  WaitElementConfig,
  WaitImageConfig,
  SetVariableConfig,
  PrintLogConfig,
  PlaySoundConfig,
  SystemNotificationConfig,
  PlayMusicConfig,
  PlayVideoConfig,
  ViewImageConfig,
  InputPromptConfig,
  TextToSpeechConfig,
  JsScriptConfig,
  PythonScriptConfig,
  ExtractTableDataConfig,
  SwitchTabConfig,
  GroupConfig,
  SubflowHeaderConfig,
  RefreshPageConfig,
  GoBackConfig,
  GoForwardConfig,
  HandleDialogConfig,
  InjectJavaScriptConfig,
  SwitchIframeConfig,
  SwitchToMainConfig,
} from './config-panels/BasicModuleConfigs'
import {
  SelectDropdownConfig,
  SetCheckboxConfig,
  DragElementConfig,
  ScrollPageConfig,
  UploadFileConfig,
  DownloadFileConfig,
  SaveImageConfig,
  GetChildElementsConfig,
  GetSiblingElementsConfig,
  ScreenshotConfig,
  OCRCaptchaConfig,
  SliderCaptchaConfig,
  SendEmailConfig,
  SetClipboardConfig,
  GetClipboardConfig,
  KeyboardActionConfig,
  RealMouseScrollConfig,
  ShutdownSystemConfig,
  LockScreenConfig,
  WindowFocusConfig,
  RealMouseClickConfig,
  RealMouseMoveConfig,
  RealMouseDragConfig,
  RealKeyboardConfig,
  RunCommandConfig,
  ClickImageConfig,
  GetMousePositionConfig,
  ScreenshotScreenConfig,
  RenameFileConfig,
  NetworkCaptureConfig,
  MacroRecorderConfig,
} from './config-panels/AdvancedModuleConfigs'
import {
  AIChatConfig,
  AIVisionConfig,
  ApiRequestConfig,
  AISmartScraperConfig,
  AIElementSelectorConfig,
  FirecrawlScrapeConfig,
  FirecrawlMapConfig,
  FirecrawlCrawlConfig,
} from './config-panels/AIModuleConfigs'
import {
  ConditionConfig,
  LoopConfig,
  ForeachConfig,
  ScheduledTaskConfig,
  SubflowConfig,
} from './config-panels/ControlModuleConfigs'
import {
  WebhookTriggerConfig,
  HotkeyTriggerConfig,
  FileWatcherTriggerConfig,
  EmailTriggerConfig,
  ApiTriggerConfig,
  MouseTriggerConfig,
  ImageTriggerConfig,
  SoundTriggerConfig,
  FaceTriggerConfig,
  ElementChangeTriggerConfig,
} from './config-panels/TriggerModuleConfigs'
import {
  RegexExtractConfig,
  StringReplaceConfig,
  StringSplitConfig,
  StringJoinConfig,
  StringConcatConfig,
  StringTrimConfig,
  StringCaseConfig,
  StringSubstringConfig,
  JsonParseConfig,
  Base64Config,
  RandomNumberConfig,
  GetTimeConfig,
  ListOperationConfig,
  ListGetConfig,
  ListLengthConfig,
  ListExportConfig,
  DictOperationConfig,
  DictGetConfig,
  DictKeysConfig,
  TableAddRowConfig,
  TableAddColumnConfig,
  TableSetCellConfig,
  TableGetCellConfig,
  TableDeleteRowConfig,
  TableClearConfig,
  TableExportConfig,
} from './config-panels/DataModuleConfigs'
import {
  DbConnectConfig,
  DbQueryConfig,
  DbExecuteConfig,
  DbInsertConfig,
  DbUpdateConfig,
  DbDeleteConfig,
  DbCloseConfig,
} from './config-panels/DatabaseModuleConfigs'
import {
  FormatConvertConfig,
  CompressImageConfig,
  CompressVideoConfig,
  ExtractAudioConfig,
  TrimVideoConfig,
  MergeMediaConfig,
  AddWatermarkConfig,
  FaceRecognitionConfig,
  ImageOCRConfig,
  DownloadM3U8Config,
  RotateVideoConfig,
  VideoSpeedConfig,
  ExtractFrameConfig,
  AddSubtitleConfig,
  AdjustVolumeConfig,
  ResizeVideoConfig,
  ImageGrayscaleConfig,
  ImageRoundCornersConfig,
  AudioToTextConfig,
  QRGenerateConfig,
  QRDecodeConfig,
  ScreenRecordConfig,
  CameraCaptureConfig,
  CameraRecordConfig,
} from './config-panels/MediaModuleConfigs'
import {
  ListFilesConfig,
  CopyFileConfig,
  MoveFileConfig,
  DeleteFileConfig,
  CreateFolderConfig,
  FileExistsConfig,
  GetFileInfoConfig,
  ReadTextFileConfig,
  WriteTextFileConfig,
  RenameFolderConfig,
} from './config-panels/FileModuleConfigs'
import {
  QQSendMessageConfig,
  QQSendImageConfig,
  QQSendFileConfig,
  QQGetFriendsConfig,
  QQGetGroupsConfig,
  QQGetGroupMembersConfig,
  QQGetLoginInfoConfig,
  QQWaitMessageConfig,
} from './config-panels/QQModuleConfigs'

import {
  WeChatSendMessageConfig,
  WeChatSendFileConfig,
} from './config-panels/WeChatModuleConfigs'
import {
  PhoneTapConfig,
  PhoneSwipeConfig,
  PhoneLongPressConfig,
  PhoneInputTextConfig,
  PhonePressKeyConfig,
  PhoneScreenshotConfig,
  PhoneStartMirrorConfig,
  PhoneStopMirrorConfig,
  PhoneInstallAppConfig,
  PhoneStartAppConfig,
  PhoneStopAppConfig,
  PhoneUninstallAppConfig,
  PhonePushFileConfig,
  PhonePullFileConfig,
  PhoneClickImageConfig,
  PhoneClickTextConfig,
  PhoneWaitImageConfig,
  PhoneSetVolumeConfig,
  PhoneSetBrightnessConfig,
} from './config-panels/PhoneModuleConfigs'
import {
  PDFToImagesConfig,
  ImagesToPDFConfig,
  PDFMergeConfig,
  PDFSplitConfig,
  PDFExtractTextConfig,
  PDFExtractImagesConfig,
  PDFEncryptConfig,
  PDFDecryptConfig,
  PDFAddWatermarkConfig,
  PDFRotateConfig,
  PDFDeletePagesConfig,
  PDFGetInfoConfig,
  PDFCompressConfig,
  PDFInsertPagesConfig,
  PDFReorderPagesConfig,
  PDFToWordConfig,
} from './config-panels/PDFModuleConfigs'
import {
  MarkdownToHTMLConfig,
  HTMLToMarkdownConfig,
  MarkdownToPDFConfig,
  MarkdownToDocxConfig,
  DocxToMarkdownConfig,
  HTMLToDocxConfig,
  DocxToHTMLConfig,
  MarkdownToEPUBConfig,
  EPUBToMarkdownConfig,
  LaTeXToPDFConfig,
  RSTToHTMLConfig,
  OrgToHTMLConfig,
  UniversalDocConvertConfig,
} from './config-panels/DocumentConvertConfigs'
import {
  ImageResizeConfig,
  ImageCropConfig,
  ImageRotateConfig,
  ImageFlipConfig,
  ImageBlurConfig,
  ImageSharpenConfig,
  ImageBrightnessConfig,
  ImageContrastConfig,
  ImageColorBalanceConfig,
  ImageConvertFormatConfig,
  ImageAddTextConfig,
  ImageMergeConfig,
  ImageThumbnailConfig,
  ImageFilterConfig,
  ImageGetInfoConfig,
  ImageRemoveBgConfig,
} from './config-panels/PillowImageConfigs'
import {
  ExportLogConfig,
  ClickTextConfig,
  HoverImageConfig,
  HoverTextConfig,
  DragImageConfig,
  ShareFolderConfig,
  ShareFileConfig,
  StopShareConfig,
  StartScreenShareConfig,
  StopScreenShareConfig,
} from './config-panels/AdvancedModuleConfigs'
import {
  ImageFormatConvertConfig,
  VideoFormatConvertConfig,
  AudioFormatConvertConfig,
  VideoToAudioConfig,
  VideoToGIFConfig,
  BatchFormatConvertConfig,
} from './config-panels/FormatFactoryConfigs'
import {
  FileHashCompareConfig,
  FileDiffCompareConfig,
  FolderHashCompareConfig,
  FolderDiffCompareConfig,
  RandomPasswordGeneratorConfig,
  URLEncodeDecodeConfig,
  MD5EncryptConfig,
  SHAEncryptConfig,
  TimestampConverterConfig,
  RGBToHSVConfig,
  RGBToCMYKConfig,
  HEXToCMYKConfig,
  UUIDGeneratorConfig,
  PrinterCallConfig,
} from './config-panels/UtilityToolsConfigs'

interface ConfigPanelProps {
  selectedNodeId?: string | null  // 改为可选，优先使用 store 中的值
}

export function ConfigPanel({ selectedNodeId: propSelectedNodeId }: ConfigPanelProps) {
  // 直接从 store 订阅 selectedNodeId，确保实时更新
  const storeSelectedNodeId = useWorkflowStore((state) => state.selectedNodeId)
  const selectedNodeId = propSelectedNodeId ?? storeSelectedNodeId
  
  const nodes = useWorkflowStore((state) => state.nodes)
  const updateNodeData = useWorkflowStore((state) => state.updateNodeData)
  const deleteNode = useWorkflowStore((state) => state.deleteNode)
  const addLog = useWorkflowStore((state) => state.addLog)
  const addVariable = useWorkflowStore((state) => state.addVariable)
  const toggleNodesDisabled = useWorkflowStore((state) => state.toggleNodesDisabled)
  
  // 获取浏览器配置
  const browserConfig = useGlobalConfigStore((state) => state.config.browser)

  const [isPicking, setIsPicking] = useState(false)
  const [pickingField, setPickingField] = useState<string | null>(null)
  const [showUrlDialog, setShowUrlDialog] = useState(false)
  const [pickerUrl, setPickerUrl] = useState('')
  const [pendingField, setPendingField] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pollingRef = useRef<number | null>(null)
  
  // 相似元素选择状态
  const [showSimilarDialog, setShowSimilarDialog] = useState(false)
  const [similarResult, setSimilarResult] = useState<{
    pattern: string
    count: number
    minIndex: number
    maxIndex: number
  } | null>(null)

  const selectedNode = nodes.find((n) => n.id === selectedNodeId)
  const nodeData = selectedNode?.data as NodeData | undefined

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  const handleChange = useCallback((key: string, value: unknown) => {
    if (selectedNodeId) {
      updateNodeData(selectedNodeId, { [key]: value })
    }
  }, [selectedNodeId, updateNodeData])

  const handleDelete = () => {
    if (selectedNodeId) {
      deleteNode(selectedNodeId)
    }
  }

  // 打开URL输入对话框
  const openUrlDialog = useCallback((fieldName: string) => {
    const openPageNode = nodes.find(n => (n.data as NodeData).moduleType === 'open_page')
    const defaultUrl = (openPageNode?.data as NodeData)?.url as string || ''
    setPickerUrl(defaultUrl)
    setPendingField(fieldName)
    setShowUrlDialog(true)
  }, [nodes])

  // 解析URL中的变量引用
  const resolveVariables = useCallback((value: string): string => {
    const variables = useWorkflowStore.getState().variables
    return value.replace(/\{([^}]+)\}/g, (match, varName) => {
      const variable = variables.find(v => v.name === varName.trim())
      return variable ? String(variable.value ?? '') : match
    })
  }, [])

  // 启动元素选择器
  const startElementPicker = useCallback(async (fieldName: string, url: string) => {
    const resolvedUrl = url ? resolveVariables(url) : ''
    setIsPicking(true)
    setPickingField(fieldName)
    setShowUrlDialog(false)
    
    if (resolvedUrl) {
      addLog({ level: 'info', message: `正在启动元素选择器，URL: ${resolvedUrl}` })
    } else {
      addLog({ level: 'info', message: '正在启动元素选择器（使用当前页面）' })
    }

    try {
      // 传递浏览器配置
      const result = await elementPickerApi.start(resolvedUrl || undefined, browserConfig)
      if (result.error) {
        addLog({ level: 'error', message: `启动失败: ${result.error}` })
        setIsPicking(false)
        setPickingField(null)
        return
      }

      addLog({ level: 'success', message: '元素选择器已启动：Ctrl+点击单选，Shift+点击选择相似元素' })

      pollingRef.current = window.setInterval(async () => {
        const selectedResult = await elementPickerApi.getSelected()
        
        if (selectedResult.data?.active === false) {
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setIsPicking(false)
          setPickingField(null)
          return
        }
        
        if (selectedResult.data?.selected && selectedResult.data.element) {
          const selector = selectedResult.data.element.selector
          handleChange(fieldName, selector)
          addLog({ level: 'success', message: `已选择元素: ${selector}` })
          
          await elementPickerApi.stop()
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setIsPicking(false)
          setPickingField(null)
          return
        }
        
        const similarRes = await elementPickerApi.getSimilar()
        if (similarRes.data?.selected && similarRes.data.similar) {
          const similar = similarRes.data.similar
          addLog({ level: 'success', message: `找到 ${similar.count} 个相似元素` })
          
          setSimilarResult({
            pattern: similar.pattern,
            count: similar.count,
            minIndex: similar.minIndex,
            maxIndex: similar.maxIndex,
          })
          setShowSimilarDialog(true)
          
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
        }
      }, 500)

    } catch (error) {
      addLog({ level: 'error', message: `启动元素选择器失败: ${error}` })
      setIsPicking(false)
      setPickingField(null)
    }
  }, [addLog, handleChange, resolveVariables, browserConfig])

  // 确认相似元素选择
  const handleSimilarConfirm = useCallback(async (variableName: string) => {
    if (!similarResult || !pickingField) return
    
    const finalSelector = similarResult.pattern.replace('{index}', `{${variableName}}`)
    handleChange(pickingField, finalSelector)
    
    addVariable({
      name: variableName,
      value: similarResult.minIndex,
      type: 'number',
      scope: 'global'
    })
    
    addLog({ 
      level: 'success', 
      message: `已设置相似元素选择器，变量 ${variableName} 范围: ${similarResult.minIndex}-${similarResult.maxIndex}` 
    })
    
    setShowSimilarDialog(false)
    setSimilarResult(null)
    await elementPickerApi.stop()
    setIsPicking(false)
    setPickingField(null)
  }, [similarResult, pickingField, handleChange, addVariable, addLog])

  // 停止元素选择器
  const stopElementPicker = useCallback(async () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    await elementPickerApi.stop()
    setIsPicking(false)
    setPickingField(null)
    setShowSimilarDialog(false)
    setSimilarResult(null)
    addLog({ level: 'info', message: '元素选择器已停止' })
  }, [addLog])

  if (!selectedNode || !nodeData) {
    return (
      <aside className={`border-l bg-card flex flex-col transition-all duration-300 ${isCollapsed ? 'w-12' : 'w-80'}`}>
        {isCollapsed ? (
          <div 
            className="flex flex-col items-center py-4 gap-3 cursor-pointer hover:bg-cyan-50/50 transition-colors h-full"
            onClick={() => setIsCollapsed(false)}
            title="点击展开配置面板"
          >
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-md">
              <ChevronLeft className="w-4 h-4" />
            </div>
            <div className="w-px h-4 bg-gray-200" />
            <Settings className="w-5 h-5 text-muted-foreground/50" />
          </div>
        ) : (
          <>
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-sm font-medium">配置面板</h2>
              <button
                onClick={() => setIsCollapsed(true)}
                className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200"
                title="收起"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 flex items-center justify-center p-4">
              <div className="text-center animate-fade-in">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-50 to-cyan-50 flex items-center justify-center">
                  <Crosshair className="w-8 h-8 text-muted-foreground/40" />
                </div>
                <p className="text-sm text-muted-foreground">
                  选择一个节点查看配置
                </p>
              </div>
            </div>
          </>
        )}
      </aside>
    )
  }

  // 渲染带选择器按钮的输入框
  const renderSelectorInput = (id: string, label: string, placeholder: string) => (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex gap-2">
        <VariableInput
          value={(nodeData[id] as string) || ''}
          onChange={(v) => handleChange(id, v)}
          placeholder={placeholder}
          className="flex-1"
        />
        <Button
          variant="outline"
          size="icon"
          onClick={() => isPicking && pickingField === id ? stopElementPicker() : openUrlDialog(id)}
          title={isPicking && pickingField === id ? '停止选择' : '可视化选择元素'}
          disabled={isPicking && pickingField !== id}
        >
          {isPicking && pickingField === id ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Crosshair className="w-4 h-4" />
          )}
        </Button>
      </div>
      {isPicking && pickingField === id && (
        <p className="text-xs text-blue-500">Ctrl+点击单选，Shift+点击选择相似元素</p>
      )}
    </div>
  )

  // 渲染模块配置
  const renderModuleConfig = () => {
    const props = { data: nodeData, onChange: handleChange, renderSelectorInput }
    
    switch (nodeData.moduleType) {
      case 'open_page':
        return <OpenPageConfig data={nodeData} onChange={handleChange} />
      case 'click_element':
        return <ClickElementConfig {...props} />
      case 'hover_element':
        return <HoverElementConfig {...props} />
      case 'input_text':
        return <InputTextConfig {...props} />
      case 'get_element_info':
        return <GetElementInfoConfig {...props} />
      case 'wait':
        return <WaitConfig {...props} />
      case 'wait_element':
        return <WaitElementConfig {...props} />
      case 'wait_image':
        return <WaitImageConfig data={nodeData} onChange={handleChange} />
      case 'refresh_page':
        return <RefreshPageConfig data={nodeData} onChange={handleChange} />
      case 'go_back':
        return <GoBackConfig data={nodeData} onChange={handleChange} />
      case 'go_forward':
        return <GoForwardConfig data={nodeData} onChange={handleChange} />
      case 'handle_dialog':
        return <HandleDialogConfig data={nodeData} onChange={handleChange} />
      case 'inject_javascript':
        return <InjectJavaScriptConfig data={nodeData} onChange={handleChange} />
      case 'switch_iframe':
        return <SwitchIframeConfig data={nodeData} onChange={handleChange} />
      case 'switch_to_main':
        return <SwitchToMainConfig />
      case 'close_page':
        return (
          <p className="text-sm text-muted-foreground">
            关闭当前打开的网页，无需额外配置
          </p>
        )
      case 'set_variable':
        return <SetVariableConfig data={nodeData} onChange={handleChange} />
      case 'print_log':
        return <PrintLogConfig data={nodeData} onChange={handleChange} />
      case 'play_sound':
        return <PlaySoundConfig data={nodeData} onChange={handleChange} />
      case 'system_notification':
        return <SystemNotificationConfig data={nodeData} onChange={handleChange} />
      case 'play_music':
        return <PlayMusicConfig data={nodeData} onChange={handleChange} />
      case 'play_video':
        return <PlayVideoConfig data={nodeData} onChange={handleChange} />
      case 'view_image':
        return <ViewImageConfig data={nodeData} onChange={handleChange} />
      case 'input_prompt':
        return <InputPromptConfig data={nodeData} onChange={handleChange} />
      case 'text_to_speech':
        return <TextToSpeechConfig data={nodeData} onChange={handleChange} />
      case 'js_script':
        return <JsScriptConfig data={nodeData} onChange={handleChange} />
      case 'python_script':
        return <PythonScriptConfig data={nodeData} onChange={handleChange} />
      case 'extract_table_data':
        return <ExtractTableDataConfig {...props} />
      case 'switch_tab':
        return <SwitchTabConfig data={nodeData} onChange={handleChange} />
      case 'select_dropdown':
        return <SelectDropdownConfig {...props} />
      case 'set_checkbox':
        return <SetCheckboxConfig {...props} />
      case 'drag_element':
        return <DragElementConfig {...props} />
      case 'scroll_page':
        return <ScrollPageConfig data={nodeData} onChange={handleChange} />
      case 'upload_file':
        return <UploadFileConfig {...props} />
      case 'download_file':
        return <DownloadFileConfig {...props} />
      case 'save_image':
        return <SaveImageConfig {...props} />
      case 'get_child_elements':
        return <GetChildElementsConfig {...props} />
      case 'get_sibling_elements':
        return <GetSiblingElementsConfig {...props} />
      case 'screenshot':
        return <ScreenshotConfig {...props} />
      case 'ocr_captcha':
        return <OCRCaptchaConfig {...props} />
      case 'slider_captcha':
        return <SliderCaptchaConfig {...props} />
      case 'send_email':
        return <SendEmailConfig data={nodeData} onChange={handleChange} />
      case 'set_clipboard':
        return <SetClipboardConfig data={nodeData} onChange={handleChange} />
      case 'get_clipboard':
        return <GetClipboardConfig data={nodeData} onChange={handleChange} />
      case 'keyboard_action':
        return <KeyboardActionConfig {...props} />
      case 'real_mouse_scroll':
        return <RealMouseScrollConfig data={nodeData} onChange={handleChange} />
      case 'shutdown_system':
        return <ShutdownSystemConfig data={nodeData} onChange={handleChange} />
      case 'lock_screen':
        return <LockScreenConfig />
      case 'window_focus':
        return <WindowFocusConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_click':
        return <RealMouseClickConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_move':
        return <RealMouseMoveConfig data={nodeData} onChange={handleChange} />
      case 'real_mouse_drag':
        return <RealMouseDragConfig data={nodeData} onChange={handleChange} />
      case 'real_keyboard':
        return <RealKeyboardConfig data={nodeData} onChange={handleChange} />
      case 'run_command':
        return <RunCommandConfig data={nodeData} onChange={handleChange} />
      case 'click_image':
        return <ClickImageConfig data={nodeData} onChange={handleChange} />
      case 'get_mouse_position':
        return <GetMousePositionConfig data={nodeData} onChange={handleChange} />
      case 'screenshot_screen':
        return <ScreenshotScreenConfig data={nodeData} onChange={handleChange} />
      case 'rename_file':
        return <RenameFileConfig data={nodeData} onChange={handleChange} />
      case 'network_capture':
        return <NetworkCaptureConfig data={nodeData} onChange={handleChange} />
      case 'macro_recorder':
        return <MacroRecorderConfig data={nodeData} onChange={handleChange} />
      case 'ai_chat':
        return <AIChatConfig data={nodeData} onChange={handleChange} />
      case 'ai_vision':
        return <AIVisionConfig {...props} />
      case 'ai_smart_scraper':
        return <AISmartScraperConfig data={nodeData} onChange={handleChange} />
      case 'ai_element_selector':
        return <AIElementSelectorConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_scrape':
        return <FirecrawlScrapeConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_map':
        return <FirecrawlMapConfig data={nodeData} onChange={handleChange} />
      case 'firecrawl_crawl':
        return <FirecrawlCrawlConfig data={nodeData} onChange={handleChange} />
      case 'api_request':
        return <ApiRequestConfig data={nodeData} onChange={handleChange} />
      case 'condition':
        return <ConditionConfig {...props} />
      case 'loop':
        return <LoopConfig data={nodeData} onChange={handleChange} />
      case 'foreach':
        return <ForeachConfig data={nodeData} onChange={handleChange} />
      case 'scheduled_task':
        return <ScheduledTaskConfig data={nodeData} onChange={handleChange} />
      case 'subflow':
        return <SubflowConfig data={nodeData} onChange={handleChange} />
      case 'break_loop':
        return (
          <p className="text-sm text-muted-foreground">
            跳出当前循环，继续执行循环后的模块
          </p>
        )
      case 'continue_loop':
        return (
          <p className="text-sm text-muted-foreground">
            跳过当前循环的剩余部分，进入下一次循环
          </p>
        )
      // 触发器模块
      case 'webhook_trigger':
        return <WebhookTriggerConfig data={nodeData} onChange={handleChange} />
      case 'hotkey_trigger':
        return <HotkeyTriggerConfig data={nodeData} onChange={handleChange} />
      case 'file_watcher_trigger':
        return <FileWatcherTriggerConfig data={nodeData} onChange={handleChange} />
      case 'email_trigger':
        return <EmailTriggerConfig data={nodeData} onChange={handleChange} />
      case 'api_trigger':
        return <ApiTriggerConfig data={nodeData} onChange={handleChange} />
      case 'mouse_trigger':
        return <MouseTriggerConfig data={nodeData} onChange={handleChange} />
      case 'image_trigger':
        return <ImageTriggerConfig data={nodeData} onChange={handleChange} />
      case 'sound_trigger':
        return <SoundTriggerConfig data={nodeData} onChange={handleChange} />
      case 'face_trigger':
        return <FaceTriggerConfig data={nodeData} onChange={handleChange} />
      case 'element_change_trigger':
        return <ElementChangeTriggerConfig {...props} />
      case 'regex_extract':
        return <RegexExtractConfig data={nodeData} onChange={handleChange} />
      case 'string_replace':
        return <StringReplaceConfig data={nodeData} onChange={handleChange} />
      case 'string_split':
        return <StringSplitConfig data={nodeData} onChange={handleChange} />
      case 'string_join':
        return <StringJoinConfig data={nodeData} onChange={handleChange} />
      case 'string_concat':
        return <StringConcatConfig data={nodeData} onChange={handleChange} />
      case 'string_trim':
        return <StringTrimConfig data={nodeData} onChange={handleChange} />
      case 'string_case':
        return <StringCaseConfig data={nodeData} onChange={handleChange} />
      case 'string_substring':
        return <StringSubstringConfig data={nodeData} onChange={handleChange} />
      case 'json_parse':
        return <JsonParseConfig data={nodeData} onChange={handleChange} />
      case 'base64':
        return <Base64Config data={nodeData} onChange={handleChange} />
      case 'random_number':
        return <RandomNumberConfig data={nodeData} onChange={handleChange} />
      case 'get_time':
        return <GetTimeConfig data={nodeData} onChange={handleChange} />
      case 'read_excel':
        return <ReadExcelConfig data={nodeData} onChange={handleChange} />
      case 'list_operation':
        return <ListOperationConfig data={nodeData} onChange={handleChange} />
      case 'list_get':
        return <ListGetConfig data={nodeData} onChange={handleChange} />
      case 'list_length':
        return <ListLengthConfig data={nodeData} onChange={handleChange} />
      case 'list_export':
        return <ListExportConfig data={nodeData} onChange={handleChange} />
      case 'dict_operation':
        return <DictOperationConfig data={nodeData} onChange={handleChange} />
      case 'dict_get':
        return <DictGetConfig data={nodeData} onChange={handleChange} />
      case 'dict_keys':
        return <DictKeysConfig data={nodeData} onChange={handleChange} />
      case 'table_add_row':
        return <TableAddRowConfig data={nodeData} onChange={handleChange} />
      case 'table_add_column':
        return <TableAddColumnConfig data={nodeData} onChange={handleChange} />
      case 'table_set_cell':
        return <TableSetCellConfig data={nodeData} onChange={handleChange} />
      case 'table_get_cell':
        return <TableGetCellConfig data={nodeData} onChange={handleChange} />
      case 'table_delete_row':
        return <TableDeleteRowConfig data={nodeData} onChange={handleChange} />
      case 'table_clear':
        return <TableClearConfig />
      case 'table_export':
        return <TableExportConfig data={nodeData} onChange={handleChange} />
      case 'db_connect':
        return <DbConnectConfig data={nodeData} onChange={handleChange} />
      case 'db_query':
        return <DbQueryConfig data={nodeData} onChange={handleChange} />
      case 'db_execute':
        return <DbExecuteConfig data={nodeData} onChange={handleChange} />
      case 'db_insert':
        return <DbInsertConfig data={nodeData} onChange={handleChange} />
      case 'db_update':
        return <DbUpdateConfig data={nodeData} onChange={handleChange} />
      case 'db_delete':
        return <DbDeleteConfig data={nodeData} onChange={handleChange} />
      case 'db_close':
        return <DbCloseConfig data={nodeData} onChange={handleChange} />
      case 'format_convert':
        return <FormatConvertConfig data={nodeData} onChange={handleChange} />
      case 'compress_image':
        return <CompressImageConfig data={nodeData} onChange={handleChange} />
      case 'compress_video':
        return <CompressVideoConfig data={nodeData} onChange={handleChange} />
      case 'extract_audio':
        return <ExtractAudioConfig data={nodeData} onChange={handleChange} />
      
      // 格式工厂模块
      case 'image_format_convert':
        return <ImageFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_format_convert':
        return <VideoFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'audio_format_convert':
        return <AudioFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_to_audio':
        return <VideoToAudioConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'video_to_gif':
        return <VideoToGIFConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      case 'batch_format_convert':
        return <BatchFormatConvertConfig config={nodeData} onChange={(newConfig) => handleChange('config', newConfig)} />
      
      case 'trim_video':
        return <TrimVideoConfig data={nodeData} onChange={handleChange} />
      case 'merge_media':
        return <MergeMediaConfig data={nodeData} onChange={handleChange} />
      case 'add_watermark':
        return <AddWatermarkConfig data={nodeData} onChange={handleChange} />
      case 'face_recognition':
        return <FaceRecognitionConfig data={nodeData} onChange={handleChange} />
      case 'image_ocr':
        return <ImageOCRConfig data={nodeData} onChange={handleChange} />
      case 'download_m3u8':
        return <DownloadM3U8Config data={nodeData} onChange={handleChange} />
      case 'rotate_video':
        return <RotateVideoConfig data={nodeData} onChange={handleChange} />
      case 'video_speed':
        return <VideoSpeedConfig data={nodeData} onChange={handleChange} />
      case 'extract_frame':
        return <ExtractFrameConfig data={nodeData} onChange={handleChange} />
      case 'add_subtitle':
        return <AddSubtitleConfig data={nodeData} onChange={handleChange} />
      case 'adjust_volume':
        return <AdjustVolumeConfig data={nodeData} onChange={handleChange} />
      case 'resize_video':
        return <ResizeVideoConfig data={nodeData} onChange={handleChange} />
      case 'image_grayscale':
        return <ImageGrayscaleConfig data={nodeData} onChange={handleChange} />
      case 'image_round_corners':
        return <ImageRoundCornersConfig data={nodeData} onChange={handleChange} />
      case 'audio_to_text':
        return <AudioToTextConfig data={nodeData} onChange={handleChange} />
      case 'qr_generate':
        return <QRGenerateConfig data={nodeData} onChange={handleChange} />
      case 'qr_decode':
        return <QRDecodeConfig data={nodeData} onChange={handleChange} />
      case 'screen_record':
        return <ScreenRecordConfig data={nodeData} onChange={handleChange} />
      case 'camera_capture':
        return <CameraCaptureConfig data={nodeData} onChange={handleChange} />
      case 'camera_record':
        return <CameraRecordConfig data={nodeData} onChange={handleChange} />
      case 'list_files':
        return <ListFilesConfig data={nodeData} onChange={handleChange} />
      case 'copy_file':
        return <CopyFileConfig data={nodeData} onChange={handleChange} />
      case 'move_file':
        return <MoveFileConfig data={nodeData} onChange={handleChange} />
      case 'delete_file':
        return <DeleteFileConfig data={nodeData} onChange={handleChange} />
      case 'create_folder':
        return <CreateFolderConfig data={nodeData} onChange={handleChange} />
      case 'file_exists':
        return <FileExistsConfig data={nodeData} onChange={handleChange} />
      case 'get_file_info':
        return <GetFileInfoConfig data={nodeData} onChange={handleChange} />
      case 'read_text_file':
        return <ReadTextFileConfig data={nodeData} onChange={handleChange} />
      case 'write_text_file':
        return <WriteTextFileConfig data={nodeData} onChange={handleChange} />
      case 'rename_folder':
        return <RenameFolderConfig data={nodeData} onChange={handleChange} />
      
      // QQ机器人模块
      case 'qq_send_message':
        return <QQSendMessageConfig data={nodeData} onChange={handleChange} />
      case 'qq_send_image':
        return <QQSendImageConfig data={nodeData} onChange={handleChange} />
      case 'qq_send_file':
        return <QQSendFileConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_friends':
        return <QQGetFriendsConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_groups':
        return <QQGetGroupsConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_group_members':
        return <QQGetGroupMembersConfig data={nodeData} onChange={handleChange} />
      case 'qq_get_login_info':
        return <QQGetLoginInfoConfig data={nodeData} onChange={handleChange} />
      case 'qq_wait_message':
        return <QQWaitMessageConfig data={nodeData} onChange={handleChange} />
      // 微信自动化模块
      case 'wechat_send_message':
        return <WeChatSendMessageConfig data={nodeData} onChange={handleChange} />
      case 'wechat_send_file':
        return <WeChatSendFileConfig data={nodeData} onChange={handleChange} />
      // 手机自动化模块
      case 'phone_tap':
        return <PhoneTapConfig data={nodeData} onChange={handleChange} />
      case 'phone_swipe':
        return <PhoneSwipeConfig data={nodeData} onChange={handleChange} />
      case 'phone_long_press':
        return <PhoneLongPressConfig data={nodeData} onChange={handleChange} />
      case 'phone_input_text':
        return <PhoneInputTextConfig data={nodeData} onChange={handleChange} />
      case 'phone_press_key':
        return <PhonePressKeyConfig data={nodeData} onChange={handleChange} />
      case 'phone_screenshot':
        return <PhoneScreenshotConfig data={nodeData} onChange={handleChange} />
      case 'phone_start_mirror':
        return <PhoneStartMirrorConfig data={nodeData} onChange={handleChange} />
      case 'phone_stop_mirror':
        return <PhoneStopMirrorConfig />
      case 'phone_install_app':
        return <PhoneInstallAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_start_app':
        return <PhoneStartAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_stop_app':
        return <PhoneStopAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_uninstall_app':
        return <PhoneUninstallAppConfig data={nodeData} onChange={handleChange} />
      case 'phone_push_file':
        return <PhonePushFileConfig data={nodeData} onChange={handleChange} />
      case 'phone_pull_file':
        return <PhonePullFileConfig data={nodeData} onChange={handleChange} />
      case 'phone_click_image':
        return <PhoneClickImageConfig data={nodeData} onChange={handleChange} />
      case 'phone_click_text':
        return <PhoneClickTextConfig data={nodeData} onChange={handleChange} />
      case 'phone_wait_image':
        return <PhoneWaitImageConfig data={nodeData} onChange={handleChange} />
      case 'phone_set_volume':
        return <PhoneSetVolumeConfig data={nodeData} onChange={handleChange} />
      case 'phone_set_brightness':
        return <PhoneSetBrightnessConfig data={nodeData} onChange={handleChange} />
      // PDF处理模块
      case 'pdf_to_images':
        return <PDFToImagesConfig config={nodeData} updateConfig={handleChange} />
      case 'images_to_pdf':
        return <ImagesToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_merge':
        return <PDFMergeConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_split':
        return <PDFSplitConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_extract_text':
        return <PDFExtractTextConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_extract_images':
        return <PDFExtractImagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_encrypt':
        return <PDFEncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_decrypt':
        return <PDFDecryptConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_add_watermark':
        return <PDFAddWatermarkConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_rotate':
        return <PDFRotateConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_delete_pages':
        return <PDFDeletePagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_get_info':
        return <PDFGetInfoConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_compress':
        return <PDFCompressConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_insert_pages':
        return <PDFInsertPagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_reorder_pages':
        return <PDFReorderPagesConfig config={nodeData} updateConfig={handleChange} />
      case 'pdf_to_word':
        return <PDFToWordConfig config={nodeData} updateConfig={handleChange} />
      // 文档转换模块
      case 'markdown_to_html':
        return <MarkdownToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'html_to_markdown':
        return <HTMLToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_pdf':
        return <MarkdownToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_docx':
        return <MarkdownToDocxConfig config={nodeData} updateConfig={handleChange} />
      case 'docx_to_markdown':
        return <DocxToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'html_to_docx':
        return <HTMLToDocxConfig config={nodeData} updateConfig={handleChange} />
      case 'docx_to_html':
        return <DocxToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'markdown_to_epub':
        return <MarkdownToEPUBConfig config={nodeData} updateConfig={handleChange} />
      case 'epub_to_markdown':
        return <EPUBToMarkdownConfig config={nodeData} updateConfig={handleChange} />
      case 'latex_to_pdf':
        return <LaTeXToPDFConfig config={nodeData} updateConfig={handleChange} />
      case 'rst_to_html':
        return <RSTToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'org_to_html':
        return <OrgToHTMLConfig config={nodeData} updateConfig={handleChange} />
      case 'universal_doc_convert':
        return <UniversalDocConvertConfig config={nodeData} updateConfig={handleChange} />
      // Pillow图像处理模块
      case 'image_resize':
        return <ImageResizeConfig config={nodeData} updateConfig={handleChange} />
      case 'image_crop':
        return <ImageCropConfig config={nodeData} updateConfig={handleChange} />
      case 'image_rotate':
        return <ImageRotateConfig config={nodeData} updateConfig={handleChange} />
      case 'image_flip':
        return <ImageFlipConfig config={nodeData} updateConfig={handleChange} />
      case 'image_blur':
        return <ImageBlurConfig config={nodeData} updateConfig={handleChange} />
      case 'image_sharpen':
        return <ImageSharpenConfig config={nodeData} updateConfig={handleChange} />
      case 'image_brightness':
        return <ImageBrightnessConfig config={nodeData} updateConfig={handleChange} />
      case 'image_contrast':
        return <ImageContrastConfig config={nodeData} updateConfig={handleChange} />
      case 'image_color_balance':
        return <ImageColorBalanceConfig config={nodeData} updateConfig={handleChange} />
      case 'image_convert_format':
        return <ImageConvertFormatConfig config={nodeData} updateConfig={handleChange} />
      case 'image_add_text':
        return <ImageAddTextConfig config={nodeData} updateConfig={handleChange} />
      case 'image_merge':
        return <ImageMergeConfig config={nodeData} updateConfig={handleChange} />
      case 'image_thumbnail':
        return <ImageThumbnailConfig config={nodeData} updateConfig={handleChange} />
      case 'image_filter':
        return <ImageFilterConfig config={nodeData} updateConfig={handleChange} />
      case 'image_get_info':
        return <ImageGetInfoConfig config={nodeData} updateConfig={handleChange} />
      case 'image_remove_bg':
        return <ImageRemoveBgConfig config={nodeData} updateConfig={handleChange} />
      // 高级模块
      case 'export_log':
        return <ExportLogConfig data={nodeData} onChange={handleChange} />
      case 'click_text':
        return <ClickTextConfig data={nodeData} onChange={handleChange} />
      case 'hover_image':
        return <HoverImageConfig data={nodeData} onChange={handleChange} />
      case 'hover_text':
        return <HoverTextConfig data={nodeData} onChange={handleChange} />
      case 'drag_image':
        return <DragImageConfig data={nodeData} onChange={handleChange} />
      case 'share_folder':
        return <ShareFolderConfig data={nodeData} onChange={handleChange} />
      case 'share_file':
        return <ShareFileConfig data={nodeData} onChange={handleChange} />
      case 'stop_share':
        return <StopShareConfig data={nodeData} onChange={handleChange} />
      case 'start_screen_share':
        return <StartScreenShareConfig data={nodeData} onChange={handleChange} />
      case 'stop_screen_share':
        return <StopScreenShareConfig data={nodeData} onChange={handleChange} />
      // 实用工具模块
      case 'file_hash_compare':
        return <FileHashCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'file_diff_compare':
        return <FileDiffCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'folder_hash_compare':
        return <FolderHashCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'folder_diff_compare':
        return <FolderDiffCompareConfig config={nodeData} updateConfig={handleChange} />
      case 'random_password_generator':
        return <RandomPasswordGeneratorConfig config={nodeData} updateConfig={handleChange} />
      case 'url_encode_decode':
        return <URLEncodeDecodeConfig config={nodeData} updateConfig={handleChange} />
      case 'md5_encrypt':
        return <MD5EncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'sha_encrypt':
        return <SHAEncryptConfig config={nodeData} updateConfig={handleChange} />
      case 'timestamp_converter':
        return <TimestampConverterConfig config={nodeData} updateConfig={handleChange} />
      case 'rgb_to_hsv':
        return <RGBToHSVConfig config={nodeData} updateConfig={handleChange} />
      case 'rgb_to_cmyk':
        return <RGBToCMYKConfig config={nodeData} updateConfig={handleChange} />
      case 'hex_to_cmyk':
        return <HEXToCMYKConfig config={nodeData} updateConfig={handleChange} />
      case 'uuid_generator':
        return <UUIDGeneratorConfig config={nodeData} updateConfig={handleChange} />
      case 'printer_call':
        return <PrinterCallConfig config={nodeData} updateConfig={handleChange} />
      case 'group':
        return <GroupConfig data={nodeData} onChange={handleChange} />
      case 'subflow_header':
        return <SubflowHeaderConfig data={nodeData} onChange={handleChange} />
      case 'note':
        return (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              便签模块用于在画布上添加注释，不会被执行
            </p>
            <div className="space-y-2">
              <Label htmlFor="noteContent">便签内容</Label>
              <textarea
                id="noteContent"
                value={(nodeData.content as string) || ''}
                onChange={(e) => handleChange('content', e.target.value)}
                placeholder="在这里输入便签内容..."
                className="w-full min-h-[100px] px-3 py-2 text-sm border rounded-md resize-y"
              />
            </div>
          </div>
        )
      default:
        return (
          <p className="text-sm text-muted-foreground">
            该模块暂无额外配置
          </p>
        )
    }
  }

  return (
    <>
      {/* URL输入对话框 */}
      <UrlInputDialog
        isOpen={showUrlDialog}
        url={pickerUrl}
        onUrlChange={setPickerUrl}
        onClose={() => setShowUrlDialog(false)}
        onConfirm={() => pendingField && startElementPicker(pendingField, pickerUrl)}
      />
      
      {/* 相似元素选择对话框 */}
      {similarResult && (
        <SimilarSelectorDialog
          isOpen={showSimilarDialog}
          onClose={() => {
            setShowSimilarDialog(false)
            setSimilarResult(null)
            stopElementPicker()
          }}
          onConfirm={handleSimilarConfirm}
          pattern={similarResult.pattern}
          count={similarResult.count}
          minIndex={similarResult.minIndex}
          maxIndex={similarResult.maxIndex}
        />
      )}
      
      <aside className={`border-l bg-gradient-to-b from-white to-cyan-50/20 flex flex-col animate-slide-in-right transition-all duration-300 ${isCollapsed ? 'w-12' : 'w-80'}`}>
        {isCollapsed ? (
          <div 
            className="flex flex-col items-center py-4 gap-3 cursor-pointer hover:bg-cyan-50/50 transition-colors h-full"
            onClick={() => setIsCollapsed(false)}
            title="点击展开配置面板"
          >
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-md">
              <ChevronLeft className="w-4 h-4" />
            </div>
            <div className="w-px h-4 bg-gray-200" />
            <Settings className="w-5 h-5 text-blue-500" />
            <span className="text-[10px] text-muted-foreground writing-mode-vertical" style={{ writingMode: 'vertical-rl' }}>
              {moduleTypeLabels[nodeData.moduleType]}
            </span>
          </div>
        ) : (
          <>
            <div className="p-4 border-b flex items-center justify-between bg-gradient-to-r from-blue-50/30 via-cyan-50/30 to-teal-50/30">
              <div>
                <h2 className="text-sm font-medium text-gradient">{moduleTypeLabels[nodeData.moduleType]}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">节点配置</p>
              </div>
              <div className="flex items-center gap-1">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => {
                    toggleNodesDisabled([selectedNode.id])
                    addLog({ level: 'info', message: nodeData.disabled ? '已启用模块' : '已禁用模块' })
                  }}
                  title={nodeData.disabled ? '启用模块 (Ctrl+D)' : '禁用模块 (Ctrl+D)'}
                  className="transition-all duration-200 hover:scale-110 active:scale-95"
                >
                  <Ban className={`w-4 h-4 transition-colors duration-200 ${nodeData.disabled ? 'text-orange-500' : 'text-muted-foreground'}`} />
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={handleDelete} 
                  title="删除模块"
                  className="transition-all duration-200 hover:scale-110 hover:bg-red-50 active:scale-95"
                >
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
                <button
                  onClick={() => setIsCollapsed(true)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200"
                  title="收起配置面板"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4 animate-fade-in">
                {/* 通用配置 */}
                <div className="space-y-2">
                  <Label htmlFor="name">节点名称</Label>
                  <Input
                    id="name"
                    value={(nodeData.name as string) || ''}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="可选的节点名称"
                    className="transition-all duration-200 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>

                {/* 模块特定配置 */}
                {renderModuleConfig()}

                {/* 高级配置 */}
                <div className="pt-4 border-t space-y-4">
                  <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    高级配置
                  </h3>
                  <div className="space-y-2">
                    <Label htmlFor="timeout">超时时间 (毫秒)</Label>
                    <NumberInput
                      id="timeout"
                      value={(nodeData.timeout as number) ?? getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType)}
                      onChange={(v) => handleChange('timeout', v)}
                      defaultValue={getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType)}
                      min={0}
                    />
                    <p className="text-xs text-muted-foreground">
                      0 表示不限制超时，当前模块建议: {(getModuleDefaultTimeout(nodeData.moduleType as import('@/types').ModuleType) / 1000).toFixed(0)}秒
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="timeoutAction">运行超时后</Label>
                    <Select
                      id="timeoutAction"
                      value={(nodeData.timeoutAction as string) || 'retry'}
                      onChange={(e) => handleChange('timeoutAction', e.target.value)}
                    >
                      <option value="retry">重试</option>
                      <option value="skip">跳过该模块，继续执行</option>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {(nodeData.timeoutAction as string) === 'skip' 
                        ? '超时后跳过此模块，直接执行后续流程'
                        : '超时后按重试次数进行重试'}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="retryCount">重试次数</Label>
                    <NumberInput
                      id="retryCount"
                      value={(nodeData.retryCount as number) ?? 0}
                      onChange={(v) => handleChange('retryCount', v)}
                      defaultValue={0}
                      min={0}
                      max={10}
                    />
                  </div>
                </div>

                {/* 变量使用提示 */}
                <div className="pt-4 border-t">
                  <div className="p-3 bg-gradient-to-r from-blue-50 via-cyan-50/50 to-teal-50 rounded-xl border border-blue-200/30 shadow-sm">
                    <p className="text-xs text-muted-foreground">
                      💡 提示：在任意输入框中使用 <code className="bg-gradient-to-r from-blue-100 to-cyan-100 px-1.5 py-0.5 rounded text-blue-600 font-mono">{'{变量名}'}</code> 来引用变量值
                    </p>
                  </div>
                </div>
              </div>
            </ScrollArea>
          </>
        )}
      </aside>
    </>
  )
}
