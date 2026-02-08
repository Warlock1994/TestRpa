import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// 浏览器类型
export type BrowserType = 'msedge' | 'chrome' | 'chromium' | 'firefox'

// 全局默认配置
export interface GlobalConfig {
  // AI大脑模块默认配置
  ai: {
    apiUrl: string
    apiKey: string
    model: string
    temperature: number
    maxTokens: number
    systemPrompt: string
  }
  // AI智能爬虫模块默认配置
  aiScraper: {
    llmProvider: string
    apiUrl: string
    llmModel: string
    apiKey: string
    azureEndpoint: string
  }
  // 发送邮件模块默认配置
  email: {
    senderEmail: string
    authCode: string
    smtpServer: string
    smtpPort: number
  }
  // 邮件触发器默认配置
  emailTrigger: {
    imapServer: string
    imapPort: number
    emailAccount: string
    emailPassword: string
    checkInterval: number
  }
  // API触发器默认配置
  apiTrigger: {
    defaultHeaders: string  // JSON格式的默认请求头
    checkInterval: number
  }
  // 文件监控触发器默认配置
  fileTrigger: {
    defaultWatchPath: string
  }
  // 本地工作流文件夹配置
  workflow: {
    localFolder: string
    autoSave: boolean  // 是否自动保存工作流
    showOverwriteConfirm: boolean  // 保存时是否显示覆盖提示（默认true）
  }
  // 数据库默认配置
  database: {
    host: string
    port: number
    user: string
    password: string
    database: string
    charset: string
  }
  // QQ自动化模块配置
  qq: {
    apiUrl: string
    accessToken: string
  }
  // 显示设置
  display: {
    showMouseCoordinates: boolean
    handleSize: number  // 连接点尺寸（像素），默认12
  }
  // 浏览器自动化配置
  browser: {
    type: BrowserType
    executablePath: string  // 自定义浏览器路径（可选）
    userDataDir: string  // 浏览器数据缓存目录（可选）
    fullscreen: boolean  // 是否全屏启动
    autoCloseBrowser: boolean  // 工作流执行结束后是否自动关闭浏览器
    launchArgs: string  // 浏览器启动参数（每行一个参数）
  }
}

interface GlobalConfigState {
  config: GlobalConfig
  updateAIConfig: (config: Partial<GlobalConfig['ai']>) => void
  updateAIScraperConfig: (config: Partial<GlobalConfig['aiScraper']>) => void
  updateEmailConfig: (config: Partial<GlobalConfig['email']>) => void
  updateEmailTriggerConfig: (config: Partial<GlobalConfig['emailTrigger']>) => void
  updateApiTriggerConfig: (config: Partial<GlobalConfig['apiTrigger']>) => void
  updateFileTriggerConfig: (config: Partial<GlobalConfig['fileTrigger']>) => void
  updateWorkflowConfig: (config: Partial<GlobalConfig['workflow']>) => void
  updateDatabaseConfig: (config: Partial<GlobalConfig['database']>) => void
  updateQQConfig: (config: Partial<GlobalConfig['qq']>) => void
  updateDisplayConfig: (config: Partial<GlobalConfig['display']>) => void
  updateBrowserConfig: (config: Partial<GlobalConfig['browser']>) => void
  resetConfig: () => void
}

const defaultConfig: GlobalConfig = {
  ai: {
    apiUrl: '',
    apiKey: '',
    model: '',
    temperature: 0.7,
    maxTokens: 2000,
    systemPrompt: '',
  },
  aiScraper: {
    llmProvider: 'ollama',
    apiUrl: '',
    llmModel: 'llama3.2',
    apiKey: '',
    azureEndpoint: '',
  },
  email: {
    senderEmail: '',
    authCode: '',
    smtpServer: 'smtp.qq.com',
    smtpPort: 465,
  },
  emailTrigger: {
    imapServer: 'imap.qq.com',
    imapPort: 993,
    emailAccount: '',
    emailPassword: '',
    checkInterval: 30,
  },
  apiTrigger: {
    defaultHeaders: '{}',
    checkInterval: 10,
  },
  fileTrigger: {
    defaultWatchPath: '',
  },
  workflow: {
    localFolder: '',  // 空字符串表示使用默认路径
    autoSave: false,  // 默认不开启自动保存
    showOverwriteConfirm: true,  // 默认显示覆盖提示
  },
  database: {
    host: 'localhost',
    port: 3306,
    user: 'root',
    password: '',
    database: '',
    charset: 'utf8mb4',
  },
  qq: {
    apiUrl: 'http://127.0.0.1:3000',
    accessToken: '',
  },
  display: {
    showMouseCoordinates: false,
    handleSize: 12,  // 默认连接点尺寸12px
  },
  browser: {
    type: 'msedge',  // 默认使用 Edge 浏览器
    executablePath: '',  // 空字符串表示使用系统默认路径
    userDataDir: '',  // 空字符串表示使用默认缓存目录
    fullscreen: false,  // 默认不全屏
    autoCloseBrowser: true,  // 默认自动关闭浏览器
    launchArgs: `--disable-blink-features=AutomationControlled
--start-maximized
--ignore-certificate-errors
--ignore-ssl-errors
--disable-features=IsolateOrigins,site-per-process
--allow-running-insecure-content
--disable-infobars
--disable-notifications`,  // 默认启动参数
  },
}

export const useGlobalConfigStore = create<GlobalConfigState>()(
  persist(
    (set, get) => ({
      config: defaultConfig,

      updateAIConfig: (aiConfig) => {
        set({
          config: {
            ...get().config,
            ai: { ...get().config.ai, ...aiConfig },
          },
        })
      },

      updateAIScraperConfig: (aiScraperConfig) => {
        set({
          config: {
            ...get().config,
            aiScraper: { ...get().config.aiScraper, ...aiScraperConfig },
          },
        })
      },

      updateEmailConfig: (emailConfig) => {
        set({
          config: {
            ...get().config,
            email: { ...get().config.email, ...emailConfig },
          },
        })
      },

      updateEmailTriggerConfig: (emailTriggerConfig) => {
        set({
          config: {
            ...get().config,
            emailTrigger: { ...get().config.emailTrigger, ...emailTriggerConfig },
          },
        })
      },

      updateApiTriggerConfig: (apiTriggerConfig) => {
        set({
          config: {
            ...get().config,
            apiTrigger: { ...get().config.apiTrigger, ...apiTriggerConfig },
          },
        })
      },

      updateFileTriggerConfig: (fileTriggerConfig) => {
        set({
          config: {
            ...get().config,
            fileTrigger: { ...get().config.fileTrigger, ...fileTriggerConfig },
          },
        })
      },

      updateWorkflowConfig: (workflowConfig) => {
        set({
          config: {
            ...get().config,
            workflow: { ...(get().config.workflow || defaultConfig.workflow), ...workflowConfig },
          },
        })
      },

      updateDatabaseConfig: (databaseConfig) => {
        set({
          config: {
            ...get().config,
            database: { ...(get().config.database || defaultConfig.database), ...databaseConfig },
          },
        })
      },

      updateQQConfig: (qqConfig) => {
        set({
          config: {
            ...get().config,
            qq: { ...(get().config.qq || defaultConfig.qq), ...qqConfig },
          },
        })
      },

      updateDisplayConfig: (displayConfig) => {
        set({
          config: {
            ...get().config,
            display: { ...(get().config.display || defaultConfig.display), ...displayConfig },
          },
        })
      },

      updateBrowserConfig: (browserConfig) => {
        set({
          config: {
            ...get().config,
            browser: { ...(get().config.browser || defaultConfig.browser), ...browserConfig },
          },
        })
      },

      resetConfig: () => {
        set({ config: defaultConfig })
      },
    }),
    {
      name: 'minghang-waf-global-config',
      // 数据迁移：确保旧数据兼容新结构
      merge: (persistedState, currentState) => {
        const persisted = persistedState as GlobalConfigState
        return {
          ...currentState,
          config: {
            ...defaultConfig,
            ...persisted?.config,
            aiScraper: persisted?.config?.aiScraper || defaultConfig.aiScraper,
            workflow: persisted?.config?.workflow || defaultConfig.workflow,
            database: persisted?.config?.database || defaultConfig.database,
            qq: persisted?.config?.qq || defaultConfig.qq,
            display: persisted?.config?.display || defaultConfig.display,
            browser: persisted?.config?.browser || defaultConfig.browser,
            emailTrigger: persisted?.config?.emailTrigger || defaultConfig.emailTrigger,
            apiTrigger: persisted?.config?.apiTrigger || defaultConfig.apiTrigger,
            fileTrigger: persisted?.config?.fileTrigger || defaultConfig.fileTrigger,
          },
        }
      },
    }
  )
)
