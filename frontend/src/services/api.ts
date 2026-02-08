import { getBackendBaseUrl, getBackendPort } from './config'

// 动态获取 API 基础地址
function getApiBase(): string {
  return `${getBackendBaseUrl()}/api`
}

let API_BASE = getApiBase()

// 更新 API 基础地址（当获取到配置后调用）
export function updateApiBase() {
  API_BASE = getApiBase()
}

// 获取当前 API 基础地址
export function getApiBaseUrl(): string {
  return API_BASE
}

export interface ApiResponse<T = unknown> {
  data?: T
  error?: string
}

// 检查是否为连接错误
function isConnectionError(error: unknown): boolean {
  if (error instanceof TypeError) {
    const message = error.message.toLowerCase()
    return message.includes('failed to fetch') || 
           message.includes('network') || 
           message.includes('fetch')
  }
  return false
}

// 显示友好的错误提示
async function showConnectionErrorDialog() {
  // 创建一个友好的错误提示弹窗
  const existingDialog = document.getElementById('connection-error-dialog')
  if (existingDialog) {
    return // 已经有弹窗了，不重复显示
  }

  // 尝试从配置文件读取端口（如果后端未启动，sessionStorage 可能为空）
  let backendPort = getBackendPort()
  
  // 如果 sessionStorage 中没有端口信息，尝试从配置文件读取
  if (backendPort === '8000') {
    try {
      const configResponse = await fetch('/WebRPAConfig.json')
      if (configResponse.ok) {
        const config = await configResponse.json()
        backendPort = String(config.backend?.port || '8000')
      }
    } catch {
      // 读取失败，使用默认值
    }
  }
  
  const dialog = document.createElement('div')
  dialog.id = 'connection-error-dialog'
  dialog.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeIn 0.2s ease-out;
  `

  dialog.innerHTML = `
    <style>
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
    </style>
    <div style="
      background: white;
      border-radius: 16px;
      padding: 32px;
      max-width: 500px;
      width: 90%;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      animation: slideUp 0.3s ease-out;
    ">
      <div style="text-align: center; margin-bottom: 24px;">
        <div style="
          width: 64px;
          height: 64px;
          margin: 0 auto 16px;
          background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);
        ">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <h2 style="
          font-size: 24px;
          font-weight: 700;
          color: #1f2937;
          margin: 0 0 8px 0;
        ">无法连接到后端服务</h2>
        <p style="
          font-size: 14px;
          color: #6b7280;
          margin: 0;
        ">Failed to fetch</p>
      </div>

      <div style="
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #fbbf24;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
      ">
        <div style="display: flex; gap: 12px;">
          <div style="flex-shrink: 0;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div style="flex: 1;">
            <h3 style="
              font-size: 14px;
              font-weight: 600;
              color: #92400e;
              margin: 0 0 8px 0;
            ">可能的原因：</h3>
            <ul style="
              margin: 0;
              padding-left: 20px;
              font-size: 13px;
              color: #78350f;
              line-height: 1.6;
            ">
              <li><strong>后端服务未启动</strong> - 请确保已运行 <code style="background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace;">双击启动WebRPA本地服务.bat</code></li>
              <li><strong>端口被占用</strong> - 后端服务使用 ${backendPort} 端口，请检查是否被其他程序占用</li>
              <li><strong>防火墙拦截</strong> - 请检查防火墙设置，允许后端服务（端口 ${backendPort}）的连接</li>
              <li><strong>局域网访问</strong> - 如果通过局域网访问，请确保后端服务器的防火墙允许 ${backendPort} 端口的入站连接</li>
            </ul>
          </div>
        </div>
      </div>

      <div style="
        background: #f3f4f6;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
      ">
        <h3 style="
          font-size: 14px;
          font-weight: 600;
          color: #374151;
          margin: 0 0 12px 0;
          display: flex;
          align-items: center;
          gap: 8px;
        ">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          解决步骤：
        </h3>
        <ol style="
          margin: 0;
          padding-left: 20px;
          font-size: 13px;
          color: #4b5563;
          line-height: 1.8;
        ">
          <li>关闭当前浏览器窗口</li>
          <li>双击运行 <code style="background: white; padding: 2px 6px; border-radius: 4px; font-family: monospace; border: 1px solid #d1d5db;">双击启动WebRPA本地服务.bat</code></li>
          <li>等待后端服务启动完成（看到 "Uvicorn running" 提示）</li>
          <li>重新打开浏览器访问 <code style="background: white; padding: 2px 6px; border-radius: 4px; font-family: monospace; border: 1px solid #d1d5db;">http://localhost:${window.location.port || '5173'}</code></li>
        </ol>
      </div>

      <button onclick="document.getElementById('connection-error-dialog').remove()" style="
        width: 100%;
        padding: 12px 24px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(59, 130, 246, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.3)'">
        我知道了
      </button>
    </div>
  `

  document.body.appendChild(dialog)

  // 点击背景关闭
  dialog.addEventListener('click', (e) => {
    if (e.target === dialog) {
      dialog.remove()
    }
  })
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }))
      return { error: error.detail || '请求失败' }
    }

    const data = await response.json()
    return { data }
  } catch (error) {
    // 检查是否为连接错误
    if (isConnectionError(error)) {
      showConnectionErrorDialog() // 不需要 await，让它异步执行
      return { error: 'Failed to fetch' }
    }
    return { error: error instanceof Error ? error.message : '网络错误' }
  }
}

export const workflowApi = {
  // 创建工作流
  create: (workflow: {
    name: string
    nodes: unknown[]
    edges: unknown[]
    variables?: unknown[]
  }) => request<{ id: string }>('/workflows', {
    method: 'POST',
    body: JSON.stringify(workflow),
  }),

  // 获取工作流列表
  list: () => request<Array<{
    id: string
    name: string
    nodeCount: number
    createdAt: string
    updatedAt: string
  }>>('/workflows'),

  // 获取单个工作流
  get: (id: string) => request<{
    id: string
    name: string
    nodes: unknown[]
    edges: unknown[]
    variables: unknown[]
  }>(`/workflows/${id}`),

  // 更新工作流
  update: (id: string, data: {
    name?: string
    nodes?: unknown[]
    edges?: unknown[]
    variables?: unknown[]
  }) => request(`/workflows/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  // 删除工作流
  delete: (id: string) => request(`/workflows/${id}`, {
    method: 'DELETE',
  }),

  // 执行工作流
  execute: (id: string, options?: { headless?: boolean; browserConfig?: { type: string; executablePath?: string; fullscreen?: boolean; autoCloseBrowser?: boolean; launchArgs?: string } }) => request(`/workflows/${id}/execute`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  }),

  // 停止执行
  stop: (id: string) => request(`/workflows/${id}/stop`, {
    method: 'POST',
  }),

  // 获取执行状态
  getStatus: (id: string) => request<{
    status: string
    executedNodes: number
    failedNodes: number
    dataFile?: string
  }>(`/workflows/${id}/status`),

  // 导入工作流
  import: (data: unknown) => request<{ id: string }>('/workflows/import', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // 导出工作流
  export: (id: string) => request(`/workflows/${id}/export`),

  // 下载数据
  downloadData: (id: string) => {
    window.open(`${API_BASE}/workflows/${id}/data`, '_blank')
  },
}

// 元素选择器API
export const elementPickerApi = {
  // 启动元素选择器（URL可选，为空时使用当前页面）
  start: (url?: string, browserConfig?: { type: string; executablePath?: string; fullscreen?: boolean }) => request<{ message: string; status: string }>('/element-picker/start', {
    method: 'POST',
    body: JSON.stringify({ 
      url: url || null,
      browserConfig: browserConfig || undefined
    }),
  }),

  // 停止元素选择器
  stop: () => request<{ message: string; status: string }>('/element-picker/stop', {
    method: 'POST',
  }),

  // 获取选中的元素（单选模式）
  getSelected: () => request<{
    selected: boolean
    active: boolean
    element?: {
      selector: string
      originalSelector: string
      tagName: string
      text: string
      attributes: Record<string, string>
      rect: { x: number; y: number; width: number; height: number }
    }
  }>('/element-picker/selected'),

  // 获取相似元素选择结果
  getSimilar: () => request<{
    selected: boolean
    active: boolean
    similar?: {
      pattern: string
      count: number
      indices: number[]
      minIndex: number
      maxIndex: number
      selector1: string
      selector2: string
    }
  }>('/element-picker/similar'),

  // 获取状态
  getStatus: () => request<{ status: string }>('/element-picker/status'),
}

// Excel文件资源API
export const dataAssetApi = {
  // 上传Excel文件
  upload: async (file: File, folder?: string): Promise<ApiResponse<{
    id: string
    name: string
    originalName: string
    size: number
    uploadedAt: string
    sheetNames: string[]
    folder: string
  }>> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (folder) {
        formData.append('folder', folder)
      }
      
      const response = await fetch(`${API_BASE}/data-assets/upload${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '上传失败' }))
        return { error: error.detail || '上传失败' }
      }
      
      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : '网络错误' }
    }
  },

  // 批量上传Excel文件
  uploadBatch: async (files: File[], folder?: string): Promise<ApiResponse<{
    success: any[]
    errors: any[]
    total: number
    successCount: number
    errorCount: number
  }>> => {
    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      
      const response = await fetch(`${API_BASE}/data-assets/upload-batch${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '批量上传失败' }))
        return { error: error.detail || '批量上传失败' }
      }
      
      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : '网络错误' }
    }
  },

  // 获取所有Excel文件资源
  list: (folder?: string) => request<Array<{
    id: string
    name: string
    originalName: string
    size: number
    uploadedAt: string
    sheetNames: string[]
    folder: string
  }>>(`/data-assets${folder !== undefined ? `?folder=${encodeURIComponent(folder)}` : ''}`),

  // 获取文件夹列表
  listFolders: () => request<string[]>('/data-assets/folders'),

  // 创建文件夹
  createFolder: (name: string, parentPath?: string) => request<{ success: boolean; path: string }>('/data-assets/folders', {
    method: 'POST',
    body: JSON.stringify({ name, parentPath }),
  }),

  // 重命名文件夹
  renameFolder: (oldPath: string, newName: string) => request<{ success: boolean; newPath: string }>('/data-assets/folders/rename', {
    method: 'PUT',
    body: JSON.stringify({ oldPath, newName }),
  }),

  // 删除文件夹
  deleteFolder: (folderPath: string) => request<{ success: boolean; deletedCount: number }>('/data-assets/folders', {
    method: 'DELETE',
    body: JSON.stringify({ folderPath }),
  }),

  // 移动文件到文件夹
  moveAsset: (assetId: string, targetFolder?: string) => request<{ success: boolean; newFolder: string }>('/data-assets/move', {
    method: 'PUT',
    body: JSON.stringify({ assetId, targetFolder }),
  }),

  // 删除Excel文件资源
  delete: (id: string) => request(`/data-assets/${id}`, {
    method: 'DELETE',
  }),

  // 重命名Excel文件资源
  rename: (id: string, newName: string) => request<{ success: boolean; asset: any }>(`/data-assets/${id}/rename?newName=${encodeURIComponent(newName)}`, {
    method: 'PUT',
  }),

  // 读取Excel数据
  read: (params: {
    fileId: string
    sheetName?: string
    readMode: 'cell' | 'row' | 'column' | 'range'
    cellAddress?: string
    rowIndex?: number
    columnIndex?: number
    startCell?: string
    endCell?: string
  }) => request<{
    data: unknown
    type: string
  }>('/data-assets/read', {
    method: 'POST',
    body: JSON.stringify(params),
  }),

  // 预览Excel数据
  preview: (fileId: string, sheet?: string) => request<{
    data: string[][]
    totalRows: number
    totalCols: number
    previewRows: number
    previewCols: number
  }>(`/data-assets/${fileId}/preview${sheet ? `?sheet=${encodeURIComponent(sheet)}` : ''}`),
}

// 图像资源API
export const imageAssetApi = {
  // 上传图像文件
  upload: async (file: File, folder?: string): Promise<ApiResponse<{
    id: string
    name: string
    originalName: string
    size: number
    uploadedAt: string
    folder: string
    extension: string
  }>> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${API_BASE}/image-assets/upload${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '上传失败' }))
        return { error: error.detail || '上传失败' }
      }
      
      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : '网络错误' }
    }
  },

  // 批量上传图像文件
  uploadBatch: async (files: File[], folder?: string): Promise<ApiResponse<{
    success: any[]
    errors: any[]
    total: number
    successCount: number
    errorCount: number
  }>> => {
    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))
      
      const response = await fetch(`${API_BASE}/image-assets/upload-batch${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '批量上传失败' }))
        return { error: error.detail || '批量上传失败' }
      }
      
      const data = await response.json()
      return { data }
    } catch (error) {
      return { error: error instanceof Error ? error.message : '网络错误' }
    }
  },

  // 获取所有图像资源
  list: (folder?: string) => request<Array<{
    id: string
    name: string
    originalName: string
    size: number
    uploadedAt: string
    folder: string
    extension: string
  }>>(`/image-assets${folder !== undefined ? `?folder=${encodeURIComponent(folder)}` : ''}`),

  // 获取文件夹列表
  listFolders: () => request<string[]>('/image-assets/folders'),

  // 创建文件夹
  createFolder: (name: string, parentPath?: string) => request<{ success: boolean; path: string }>('/image-assets/folders', {
    method: 'POST',
    body: JSON.stringify({ name, parentPath }),
  }),

  // 重命名文件夹
  renameFolder: (oldPath: string, newName: string) => request<{ success: boolean; newPath: string }>('/image-assets/folders/rename', {
    method: 'PUT',
    body: JSON.stringify({ oldPath, newName }),
  }),

  // 删除文件夹
  deleteFolder: (folderPath: string) => request<{ success: boolean; deletedCount: number }>('/image-assets/folders', {
    method: 'DELETE',
    body: JSON.stringify({ folderPath }),
  }),

  // 移动图像到文件夹
  moveAsset: (assetId: string, targetFolder?: string) => request<{ success: boolean; newFolder: string }>('/image-assets/move', {
    method: 'PUT',
    body: JSON.stringify({ assetId, targetFolder }),
  }),

  // 删除图像资源
  delete: (id: string) => request(`/image-assets/${id}`, {
    method: 'DELETE',
  }),

  // 重命名图像资源
  rename: (id: string, newName: string) => request<{ success: boolean; asset: any }>(`/image-assets/${id}/rename?newName=${encodeURIComponent(newName)}`, {
    method: 'PUT',
  }),

  // 获取图像路径
  getPath: (id: string) => request<{ path: string }>(`/image-assets/${id}/path`),
}

// 自动化浏览器API
export const browserApi = {
  // 打开浏览器
  open: (url?: string, browserConfig?: { type: string; executablePath?: string; fullscreen?: boolean }) => request<{ message: string; status: string }>('/browser/open', {
    method: 'POST',
    body: JSON.stringify({ 
      url: url || 'about:blank',
      browserConfig: browserConfig || undefined
    }),
  }),

  // 关闭浏览器
  close: () => request<{ message: string; status: string }>('/browser/close', {
    method: 'POST',
  }),

  // 获取状态
  getStatus: () => request<{ status: string; isOpen: boolean; pickerActive: boolean }>('/browser/status'),

  // 导航到URL
  navigate: (url: string) => request<{ message: string; url: string }>('/browser/navigate', {
    method: 'POST',
    body: JSON.stringify({ url }),
  }),

  // 启动元素选择器
  startPicker: () => request<{ message: string; status: string; hint: string }>('/browser/picker/start', {
    method: 'POST',
  }),

  // 停止元素选择器
  stopPicker: () => request<{ message: string; status: string }>('/browser/picker/stop', {
    method: 'POST',
  }),

  // 获取选中的单个元素
  getSelectedElement: () => request<{
    selected: boolean
    element?: {
      selector: string
      tagName: string
      text: string
      attributes: Record<string, string>
      rect: { x: number; y: number; width: number; height: number }
    }
  }>('/browser/picker/selected'),

  // 获取选中的相似元素
  getSimilarElements: () => request<{
    selected: boolean
    similar?: {
      pattern: string
      count: number
      indices: number[]
      minIndex: number
      maxIndex: number
    }
  }>('/browser/picker/similar'),
}

// 系统API
export const systemApi = {
  // 选择文件夹
  selectFolder: (title?: string, initialDir?: string) => 
    request<{ success: boolean; path: string | null; message?: string; error?: string }>('/system/select-folder', {
      method: 'POST',
      body: JSON.stringify({ title, initialDir }),
    }),

  // 选择文件
  selectFile: (title?: string, initialDir?: string, fileTypes?: Array<[string, string]>) => 
    request<{ success: boolean; path: string | null; message?: string; error?: string }>('/system/select-file', {
      method: 'POST',
      body: JSON.stringify({ title, initialDir, fileTypes }),
    }),
}


// 计划任务API
export const scheduledTaskApi = {
  // 获取所有计划任务
  list: () => request<any[]>('/scheduled-tasks'),

  // 获取单个计划任务
  get: (id: string) => request<any>(`/scheduled-tasks/${id}`),

  // 创建计划任务
  create: (task: any) => request<any>('/scheduled-tasks', {
    method: 'POST',
    body: JSON.stringify(task),
  }),

  // 更新计划任务
  update: (id: string, updates: any) => request<any>(`/scheduled-tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  }),

  // 删除计划任务
  delete: (id: string) => request<{ success: boolean; message: string }>(`/scheduled-tasks/${id}`, {
    method: 'DELETE',
  }),

  // 启用/禁用计划任务
  toggle: (id: string, enabled: boolean) => request<{ success: boolean; enabled: boolean }>(`/scheduled-tasks/${id}/toggle`, {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  }),

  // 手动执行计划任务
  execute: (id: string) => request<{ success: boolean; message: string }>(`/scheduled-tasks/${id}/execute`, {
    method: 'POST',
  }),

  // 停止正在执行的计划任务
  stop: (id: string) => request<{ success: boolean; message: string }>(`/scheduled-tasks/${id}/stop`, {
    method: 'POST',
  }),

  // 获取任务执行日志
  getTaskLogs: (taskId: string, limit = 100) => request<any[]>(`/scheduled-tasks/${taskId}/logs?limit=${limit}`),

  // 获取所有执行日志
  getAllLogs: (limit = 100) => request<any[]>(`/scheduled-tasks/logs/all?limit=${limit}`),

  // 清空任务执行日志
  clearTaskLogs: (taskId: string) => request<{ success: boolean; message: string }>(`/scheduled-tasks/${taskId}/logs`, {
    method: 'DELETE',
  }),

  // 清空所有执行日志
  clearAllLogs: () => request<{ success: boolean; message: string }>('/scheduled-tasks/logs/all', {
    method: 'DELETE',
  }),

  // 获取统计摘要
  getStatistics: () => request<any>('/scheduled-tasks/statistics/summary'),
}

// 本地工作流API
export const localWorkflowApi = {
  // 获取默认工作流文件夹
  getDefaultFolder: () => request<{ folder: string; workflows?: Array<{
    filename: string
    name: string
    modifiedTime: string
    size: number
  }> }>('/local-workflows/default-folder'),

  // 列出工作流文件
  list: (folder?: string) => request<{ workflows: Array<{
    filename: string
    name: string
    modifiedTime: string
    size: number
  }> }>('/local-workflows/list', {
    method: 'POST',
    body: JSON.stringify({ folder: folder || '' }),
  }),

  // 加载工作流
  load: (filename: string, folder?: string) => request<{ success: boolean; content?: any; error?: string }>(`/local-workflows/load/${encodeURIComponent(filename)}${folder ? `?folder=${encodeURIComponent(folder)}` : ''}`),

  // 保存工作流
  save: (filename: string, content: any, folder?: string) => request<{ success: boolean; filepath?: string; filename?: string; error?: string }>('/local-workflows/save-to-folder', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      content: { ...content, _folder: folder },
    }),
  }),

  // 删除工作流
  delete: (filename: string, folder?: string) => request<{ success: boolean; error?: string }>('/local-workflows/delete', {
    method: 'POST',
    body: JSON.stringify({ filename, folder }),
  }),

  // 检查文件是否存在
  checkExists: (filename: string, content: any) => request<{ exists: boolean; filename: string; filepath: string }>('/local-workflows/check-exists', {
    method: 'POST',
    body: JSON.stringify({ filename, content }),
  }),
}

