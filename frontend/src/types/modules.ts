import type { ModuleConfig } from './workflow'

// ============ 基础模块配置 ============

export type WaitUntil = 'load' | 'domcontentloaded' | 'networkidle'

export interface OpenPageConfig extends ModuleConfig {
  url: string
  waitUntil?: WaitUntil
}

export type ClickType = 'single' | 'double' | 'right'

export interface ClickElementConfig extends ModuleConfig {
  selector: string
  clickType?: ClickType
  waitForSelector?: boolean
}

export interface InputTextConfig extends ModuleConfig {
  selector: string
  text: string
  clearBefore?: boolean
}

export type ElementAttribute = 'text' | 'innerHTML' | 'value' | 'href' | 'src' | 'custom'

export interface GetElementInfoConfig extends ModuleConfig {
  selector: string
  attribute?: ElementAttribute
  customAttribute?: string
  variableName: string
  columnName?: string
}

export type WaitType = 'time' | 'selector' | 'navigation'

export interface WaitConfig extends ModuleConfig {
  waitType?: WaitType
  duration?: number
  selector?: string
  state?: 'visible' | 'hidden' | 'attached' | 'detached'
}

export interface ClosePageConfig extends ModuleConfig {}

// ============ 高级模块配置 ============

export type SelectBy = 'value' | 'label' | 'index'

export interface SelectDropdownConfig extends ModuleConfig {
  selector: string
  selectBy?: SelectBy
  value: string
}

export interface SetCheckboxConfig extends ModuleConfig {
  selector: string
  checked?: boolean
}

export interface DragElementConfig extends ModuleConfig {
  sourceSelector: string
  targetSelector?: string
  targetPosition?: { x: number; y: number }
}

export type ScrollDirection = 'up' | 'down' | 'left' | 'right'

export interface ScrollPageConfig extends ModuleConfig {
  direction?: ScrollDirection
  distance?: number
  selector?: string
}

export interface UploadFileConfig extends ModuleConfig {
  selector: string
  filePath: string
}

export interface DownloadFileConfig extends ModuleConfig {
  triggerSelector: string
  savePath?: string
  variableName?: string
}

export interface SaveImageConfig extends ModuleConfig {
  selector: string
  savePath?: string
  variableName?: string
}

export interface GetChildElementsConfig extends ModuleConfig {
  parentSelector: string
  childSelector?: string
  variableName: string
}

export type SiblingType = 'all' | 'previous' | 'next'

export interface GetSiblingElementsConfig extends ModuleConfig {
  elementSelector: string
  variableName: string
  includeSelf?: boolean
  siblingType?: SiblingType
}

export interface InjectJavaScriptConfig extends ModuleConfig {
  javascriptCode: string
  saveResult?: string
  injectMode?: 'current' | 'all' | 'url_match' | 'index'
  targetUrl?: string
  targetIndex?: string
}

// ============ 验证码模块配置 ============

export interface OCRCaptchaConfig extends ModuleConfig {
  imageSelector: string
  inputSelector: string
  variableName?: string
  autoSubmit?: boolean
  submitSelector?: string
}

export interface SliderCaptchaConfig extends ModuleConfig {
  sliderSelector: string
  backgroundSelector?: string
  gapSelector?: string
}

// ============ 流程控制模块配置 ============

export type ConditionType = 'variable' | 'element_exists' | 'element_visible' | 'element_text'

export type Operator = '==' | '!=' | '>' | '<' | '>=' | '<=' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with'

export interface ConditionConfig extends ModuleConfig {
  conditionType?: ConditionType
  leftOperand: string
  operator?: Operator
  rightOperand: string
}

export type LoopType = 'count' | 'while'

export interface LoopConfig extends ModuleConfig {
  loopType?: LoopType
  count?: number
  condition?: string
  maxIterations?: number
  indexVariable?: string
}

export interface ForeachConfig extends ModuleConfig {
  dataSource: string
  itemVariable?: string
  indexVariable?: string
}

export interface BreakLoopConfig extends ModuleConfig {}

export interface ContinueLoopConfig extends ModuleConfig {}

// ============ AI智能模块配置 ============

export type LLMProvider = 'ollama' | 'openai' | 'groq' | 'gemini' | 'azure'

export interface AISmartScraperConfig extends ModuleConfig {
  url: string
  prompt: string
  variableName: string
  llmProvider?: LLMProvider
  llmModel?: string
  apiKey?: string
  azureEndpoint?: string
  verbose?: boolean
  headless?: boolean
}

export interface AIElementSelectorConfig extends ModuleConfig {
  elementDescription: string
  variableName: string
  llmProvider?: LLMProvider
  llmModel?: string
  apiKey?: string
  azureEndpoint?: string
  verbose?: boolean
}

// 所有模块配置类型联合
export type AnyModuleConfig =
  | OpenPageConfig
  | ClickElementConfig
  | InputTextConfig
  | GetElementInfoConfig
  | WaitConfig
  | ClosePageConfig
  | SelectDropdownConfig
  | SetCheckboxConfig
  | DragElementConfig
  | ScrollPageConfig
  | UploadFileConfig
  | DownloadFileConfig
  | SaveImageConfig
  | GetChildElementsConfig
  | GetSiblingElementsConfig
  | InjectJavaScriptConfig
  | OCRCaptchaConfig
  | SliderCaptchaConfig
  | AISmartScraperConfig
  | AIElementSelectorConfig
  | ConditionConfig
  | LoopConfig
  | ForeachConfig
  | BreakLoopConfig
  | ContinueLoopConfig
