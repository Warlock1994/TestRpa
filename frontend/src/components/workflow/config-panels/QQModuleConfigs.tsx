import type { NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { SelectNative as Select } from '@/components/ui/select-native'
import { VariableInput } from '@/components/ui/variable-input'
import { VariableNameInput } from '@/components/ui/variable-name-input'
import { Button } from '@/components/ui/button'
import { QQContactSelect } from '@/components/ui/qq-contact-select'
import { useState, useEffect, useCallback } from 'react'
import { ExternalLink, CheckCircle, XCircle, Loader2, Play, Square, RefreshCw, X, FolderOpen } from 'lucide-react'
import { systemApi } from '@/services/api'
import { getBackendBaseUrl } from '@/services/config'
import { ImagePathInput } from '@/components/ui/image-path-input'

// NapCat 服务状态类型
interface NapCatStatus {
  napcat_installed: boolean
  qq_installed: boolean
  qq_path: string | null
  is_running: boolean
  qq_running?: boolean  // QQ 进程是否在运行
  onebot_available?: boolean  // OneBot API 是否可用
  onebot_logged_in?: boolean  // 是否已登录
  qq_number: string | null
  webui_url: string | null
  onebot_port: number
  qrcode_available?: boolean
}

// 二维码扫码弹窗
function QRCodeDialog({ 
  isOpen, 
  onClose, 
  onLoginSuccess,
  webuiUrl
}: { 
  isOpen: boolean
  onClose: () => void
  onLoginSuccess: (qqNumber: string) => void
  webuiUrl?: string | null
}) {
  const [qrcodeUrl, setQrcodeUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [step, setStep] = useState<'qrcode' | 'config'>('qrcode')
  const [loggedQQ, setLoggedQQ] = useState<string>('')
  const [currentWebuiUrl, setCurrentWebuiUrl] = useState<string | null>(webuiUrl || null)

  // 更新 webuiUrl
  useEffect(() => {
    if (webuiUrl) {
      setCurrentWebuiUrl(webuiUrl)
    }
  }, [webuiUrl])

  // 加载二维码 - 轮询检测直到二维码可用
  const loadQRCode = useCallback(async () => {
    setLoading(true)
    const API_BASE = getBackendBaseUrl()
    
    // 轮询检测二维码是否可用（最多等待10秒）
    let attempts = 0
    const maxAttempts = 20 // 10秒 (每次500ms)
    
    while (attempts < maxAttempts) {
      try {
        const testUrl = `${API_BASE}/api/system/napcat/qrcode?t=${Date.now()}`
        const response = await fetch(testUrl, { method: 'GET' })
        
        if (response.ok) {
          // 二维码可用，显示它
          setQrcodeUrl(testUrl)
          setLoading(false)
          return
        }
      } catch (e) {
        // 继续等待
      }
      
      attempts++
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    // 超时后仍然尝试显示（可能会显示加载失败）
    const url = `${API_BASE}/api/system/napcat/qrcode?t=${Date.now()}`
    setQrcodeUrl(url)
    setLoading(false)
  }, [])

  // 刷新二维码（重启服务生成新二维码）
  const refreshQRCode = useCallback(async () => {
    setRefreshing(true)
    setQrcodeUrl(null)
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/system/napcat/refresh-qrcode`, {
        method: 'POST'
      })
      const result = await response.json()
      if (result.success) {
        // 等待新二维码生成后加载
        setTimeout(() => {
          loadQRCode()
          setRefreshing(false)
        }, 3000)
      } else {
        console.error('刷新二维码失败:', result.error)
        setRefreshing(false)
      }
    } catch (e) {
      console.error('刷新二维码失败:', e)
      setRefreshing(false)
    }
  }, [loadQRCode])

  // 轮询检测登录状态和二维码刷新
  useEffect(() => {
    if (!isOpen || step !== 'qrcode') return
    
    // 立即加载二维码
    loadQRCode()
    
    // 二维码每2分钟过期，提前10秒自动刷新
    const qrcodeRefreshInterval = setInterval(() => {
      console.log('[QRCodeDialog] 二维码即将过期，自动刷新')
      loadQRCode()
    }, 110000) // 110秒 = 1分50秒
    
    // 轮询检测登录状态
    const checkLogin = async () => {
      try {
        const API_BASE = getBackendBaseUrl()
        const response = await fetch(`${API_BASE}/api/system/napcat/status`)
        const status = await response.json()
        
        // 更新 WebUI URL
        if (status.webui_url) {
          setCurrentWebuiUrl(status.webui_url)
        }
        
        // 检测到 qq_number 说明已经登录成功
        if (status.qq_number) {
          console.log('[QRCodeDialog] 检测到登录成功:', status.qq_number)
          setLoggedQQ(status.qq_number)
          setStep('config')
          onLoginSuccess(status.qq_number)
        }
      } catch (e) {
        console.error('[QRCodeDialog] 检测状态失败:', e)
      }
    }
    
    const loginCheckInterval = setInterval(checkLogin, 1000)
    
    return () => {
      clearInterval(qrcodeRefreshInterval)
      clearInterval(loginCheckInterval)
    }
  }, [isOpen, step, loadQRCode, onLoginSuccess])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-[480px] max-h-[90vh] overflow-auto">
        {/* 标题栏 */}
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-medium">
            {step === 'qrcode' ? '扫码登录 QQ' : '配置 OneBot 服务'}
          </h3>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 内容区 */}
        <div className="p-6">
          {step === 'qrcode' ? (
            <div className="flex flex-col items-center space-y-4">
              {/* 二维码图片 */}
              <div className="w-64 h-64 bg-gray-100 rounded-lg flex flex-col items-center justify-center overflow-hidden">
                {loading || refreshing ? (
                  <>
                    <Loader2 className="w-8 h-8 animate-spin text-gray-400 mb-2" />
                    <p className="text-sm text-gray-500">{refreshing ? '正在刷新二维码...' : '加载二维码中...'}</p>
                  </>
                ) : qrcodeUrl ? (
                  <img 
                    src={qrcodeUrl} 
                    alt="QQ登录二维码" 
                    className="w-full h-full object-contain"
                    onError={() => setLoading(true)}
                  />
                ) : (
                  <p className="text-gray-400 text-sm">二维码加载失败</p>
                )}
              </div>
              
              {/* 提示文字 */}
              <div className="text-center space-y-2">
                <p className="text-sm text-gray-600">请使用手机 QQ 扫描上方二维码登录</p>
                <p className="text-xs text-gray-400">扫码后在手机上确认登录</p>
                <p className="text-xs text-blue-500">💡 若之前已扫码登录过，稍等片刻会自动登录</p>
              </div>

              {/* 刷新按钮 */}
              <Button variant="outline" size="sm" onClick={refreshQRCode} disabled={refreshing}>
                <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? '刷新中...' : '刷新二维码'}
              </Button>

              {/* 等待提示 */}
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                等待扫码登录...
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 登录成功提示 */}
              <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm text-green-800">
                  QQ {loggedQQ} 登录成功！
                </span>
              </div>

              {/* 配置步骤 */}
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">接下来请完成以下配置：</p>
                
                <div className="space-y-3 text-sm text-gray-600">
                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">1</span>
                    <div>
                      <p>打开 NapCat WebUI 管理界面：</p>
                      <div className="flex items-center gap-2 mt-1">
                        <a 
                          href={currentWebuiUrl || 'http://127.0.0.1:6099/webui'} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                        >
                          打开 NapCat WebUI <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">2</span>
                    <p>点击左侧「网络配置」菜单</p>
                  </div>

                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">3</span>
                    <p>点击「新建」按钮，选择「HTTP服务器」</p>
                  </div>

                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">4</span>
                    <p>打开「启用」开关，给服务器起个名称（如：WebRPA）</p>
                  </div>

                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-xs font-medium">5</span>
                    <div>
                      <p className="font-medium text-amber-700">重要：清空 Token 输入框</p>
                      <p className="text-xs text-gray-500 mt-1">确保 Token 输入框为空，否则会导致连接失败</p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-medium">6</span>
                    <p>点击「保存」按钮完成配置</p>
                  </div>
                </div>
              </div>

              {/* 完成按钮 */}
              <div className="pt-4 border-t">
                <Button className="w-full" onClick={onClose}>
                  <CheckCircle className="w-4 h-4 mr-1" />
                  配置完成
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// QQ服务状态检测组件
function QQServiceStatus({ apiUrl }: { apiUrl: string }) {
  const [status, setStatus] = useState<'idle' | 'checking' | 'online' | 'offline'>('idle')
  const [loginInfo, setLoginInfo] = useState<{ nickname: string; user_id: string } | null>(null)

  const checkStatus = async () => {
    setStatus('checking')
    try {
      const url = (apiUrl || 'http://127.0.0.1:3000').replace(/\/$/, '')
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const response = await fetch(`${url}/get_login_info`, {
        method: 'POST',
        headers,
        body: JSON.stringify({})
      })
      const result = await response.json()
      if (result.status === 'ok' && result.data) {
        setLoginInfo(result.data)
        setStatus('online')
      } else {
        setStatus('offline')
        setLoginInfo(null)
      }
    } catch {
      setStatus('offline')
      setLoginInfo(null)
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={checkStatus} disabled={status === 'checking'}>
        {status === 'checking' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
        检测服务
      </Button>
      {status === 'online' && (
        <span className="flex items-center gap-1 text-xs text-green-600">
          <CheckCircle className="w-3 h-3" />
          已连接: {loginInfo?.nickname}
        </span>
      )}
      {status === 'offline' && (
        <span className="flex items-center gap-1 text-xs text-red-500">
          <XCircle className="w-3 h-3" />
          未连接
        </span>
      )}
    </div>
  )
}

// 内置 NapCat 服务管理组件
function NapCatServiceManager() {
  const [status, setStatus] = useState<NapCatStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [qqNumber, setQqNumber] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [showQRDialog, setShowQRDialog] = useState(false)
  const [webuiUrl, setWebuiUrl] = useState<string | null>(null)

  // 获取服务状态
  const fetchStatus = async () => {
    setLoading(true)
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/system/napcat/status`)
      const data = await response.json()
      setStatus(data)
      // 更新 WebUI URL
      if (data.webui_url) {
        setWebuiUrl(data.webui_url)
      }
    } catch (e) {
      console.error('获取 NapCat 状态失败:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  // 启动服务
  const startService = async () => {
    setActionLoading(true)
    setMessage(null)
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/system/napcat/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qq_number: qqNumber })
      })
      const result = await response.json()
      if (result.success) {
        setMessage({ type: 'success', text: result.message })
        // 启动成功后立即显示二维码弹窗，弹窗内部会处理二维码加载
        setShowQRDialog(true)
        setActionLoading(false)
      } else {
        setMessage({ type: 'error', text: result.error })
        setActionLoading(false)
      }
    } catch (e) {
      setMessage({ type: 'error', text: '启动失败' })
      setActionLoading(false)
    }
  }

  // 停止服务
  const stopService = async () => {
    setActionLoading(true)
    setMessage(null)
    try {
      const API_BASE = getBackendBaseUrl()
      const response = await fetch(`${API_BASE}/api/system/napcat/stop`, {
        method: 'POST'
      })
      const result = await response.json()
      if (result.success) {
        setMessage({ type: 'success', text: result.message })
      } else {
        setMessage({ type: 'error', text: result.error })
      }
      // 等待一下再刷新状态，确保进程已经停止
      await new Promise(resolve => setTimeout(resolve, 500))
      await fetchStatus()
    } catch (e) {
      setMessage({ type: 'error', text: '停止失败' })
    } finally {
      setActionLoading(false)
    }
  }

  // 登录成功回调
  const handleLoginSuccess = (qqNum: string) => {
    console.log('登录成功:', qqNum)
    fetchStatus()
  }

  if (loading && !status) {
    return (
      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          检测 NapCat 服务状态...
        </div>
      </div>
    )
  }

  // NapCat 未安装
  if (status && !status.napcat_installed) {
    return (
      <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 mb-4">
        <p className="text-xs text-amber-800 font-medium mb-2">⚠️ NapCat 未安装</p>
        <p className="text-xs text-amber-700">
          请下载 NapCat.Shell.zip 并解压到项目根目录的 NapCat 文件夹
        </p>
        <a 
          href="https://github.com/NapNeko/NapCatQQ/releases" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:underline inline-flex items-center gap-0.5 mt-2"
        >
          下载 NapCat <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    )
  }

  // QQ 未安装
  if (status && !status.qq_installed) {
    return (
      <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 mb-4">
        <p className="text-xs text-amber-800 font-medium mb-2">⚠️ QQNT 未安装</p>
        <p className="text-xs text-amber-700">
          NapCat 需要配合 QQNT 客户端使用，请先安装 QQ
        </p>
        <a 
          href="https://im.qq.com/pcqq/index.shtml" 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:underline inline-flex items-center gap-0.5 mt-2"
        >
          下载 QQ <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    )
  }

  // 检测到 QQ 手动启动的情况
  const isManualQQ = status?.qq_running && !status?.onebot_available

  return (
    <>
      <div className={`p-3 rounded-lg border mb-4 space-y-3 ${
        isManualQQ 
          ? 'bg-amber-50 border-amber-200' 
          : 'bg-green-50 border-green-200'
      }`}>
        <div className="flex items-center justify-between">
          <p className={`text-xs font-medium ${
            isManualQQ ? 'text-amber-800' : 'text-green-800'
          }`}>
            {isManualQQ ? '⚠️ 检测到手动启动的 QQ' : '✅ 内置 NapCat 服务'}
          </p>
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={fetchStatus}>
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        
        {/* 手动启动 QQ 的警告提示 */}
        {isManualQQ && (
          <div className="text-xs text-amber-700 space-y-1">
            <p>检测到 QQ 进程正在运行，但 NapCat 服务未启动。</p>
            <p className="font-medium">QQ 支持多开，您可以：</p>
            <ul className="list-disc list-inside pl-2 space-y-0.5">
              <li>直接启动 NapCat（会启动新的 QQ 实例）</li>
              <li>或关闭手动启动的 QQ 后再启动</li>
            </ul>
          </div>
        )}
        
        {/* 服务状态 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">NapCat 状态:</span>
          {status?.is_running ? (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle className="w-3 h-3" />
              运行中 {status?.qq_number && `(QQ: ${status.qq_number})`}
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <XCircle className="w-3 h-3" />
              未运行
            </span>
          )}
        </div>
        
        {/* OneBot API 状态 */}
        {status?.qq_running && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-600">OneBot API:</span>
            {status?.onebot_available ? (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <CheckCircle className="w-3 h-3" />
                可用
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs text-red-500">
                <XCircle className="w-3 h-3" />
                不可用
              </span>
            )}
          </div>
        )}

        {/* QQ号输入（仅在未运行时显示） */}
        {!status?.is_running && (
          <div className="space-y-1">
            <Label className="text-xs">QQ号（可选，用于快速登录）</Label>
            <input
              type="text"
              value={qqNumber}
              onChange={(e) => setQqNumber(e.target.value)}
              placeholder="留空则扫码登录"
              className="w-full px-2 py-1 text-xs border rounded"
            />
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2">
          {!status?.is_running ? (
            <Button 
              size="sm" 
              onClick={startService} 
              disabled={actionLoading}
              className="flex-1"
            >
              {actionLoading ? (
                <Loader2 className="w-3 h-3 animate-spin mr-1" />
              ) : (
                <Play className="w-3 h-3 mr-1" />
              )}
              启动服务
            </Button>
          ) : (
            <Button 
              size="sm" 
              variant="destructive"
              onClick={stopService} 
              disabled={actionLoading}
              className="flex-1"
            >
              {actionLoading ? (
                <Loader2 className="w-3 h-3 animate-spin mr-1" />
              ) : (
                <Square className="w-3 h-3 mr-1" />
              )}
              停止服务
            </Button>
          )}
        </div>

        {/* 消息提示 */}
        {message && (
          <p className={`text-xs ${message.type === 'success' ? 'text-green-600' : 'text-red-500'}`}>
            {message.text}
          </p>
        )}

        {/* 使用说明 */}
        <div className="text-xs text-gray-500">
          <p>启动后会打开 QQ 客户端，首次使用需扫码登录</p>
        </div>
      </div>

      {/* 二维码弹窗 */}
      <QRCodeDialog 
        isOpen={showQRDialog} 
        onClose={() => setShowQRDialog(false)}
        onLoginSuccess={handleLoginSuccess}
        webuiUrl={webuiUrl}
      />
    </>
  )
}


// QQ发送消息配置
export function QQSendMessageConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <p className="text-xs text-muted-foreground">留空则使用默认地址</p>
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="messageType">消息类型</Label>
        <Select
          id="messageType"
          value={(data.messageType as string) || 'private'}
          onChange={(e) => onChange('messageType', e.target.value)}
        >
          <option value="private">私聊消息</option>
          <option value="group">群消息</option>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="targetId">{(data.messageType as string) === 'group' ? '群号' : 'QQ号'}</Label>
        <QQContactSelect
          value={(data.targetId as string) || ''}
          onChange={(v) => onChange('targetId', v)}
          placeholder={(data.messageType as string) === 'group' ? '输入或选择群号' : '输入或选择QQ号'}
          type={(data.messageType as string) === 'group' ? 'group' : 'private'}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="message">消息内容</Label>
        <VariableInput
          value={(data.message as string) || ''}
          onChange={(v) => onChange('message', v)}
          placeholder="要发送的消息内容"
          multiline
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量（可选）</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存发送结果的变量名"
        />
      </div>
    </>
  )
}

// QQ发送图片配置
export function QQSendImageConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="messageType">消息类型</Label>
        <Select
          id="messageType"
          value={(data.messageType as string) || 'private'}
          onChange={(e) => onChange('messageType', e.target.value)}
        >
          <option value="private">私聊</option>
          <option value="group">群聊</option>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="targetId">{(data.messageType as string) === 'group' ? '群号' : 'QQ号'}</Label>
        <QQContactSelect
          value={(data.targetId as string) || ''}
          onChange={(v) => onChange('targetId', v)}
          placeholder={(data.messageType as string) === 'group' ? '输入或选择群号' : '输入或选择QQ号'}
          type={(data.messageType as string) === 'group' ? 'group' : 'private'}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="imagePath">图片路径/URL</Label>
        <ImagePathInput
          value={(data.imagePath as string) || ''}
          onChange={(v) => onChange('imagePath', v)}
          placeholder="从图像资源中选择或输入路径/URL"
        />
        <p className="text-xs text-muted-foreground">支持本地文件路径或网络图片URL</p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="text">附带文字（可选）</Label>
        <VariableInput
          value={(data.text as string) || ''}
          onChange={(v) => onChange('text', v)}
          placeholder="图片附带的文字说明"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量（可选）</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存发送结果的变量名"
        />
      </div>
    </>
  )
}

// QQ发送文件配置
export function QQSendFileConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="messageType">发送类型</Label>
        <Select
          id="messageType"
          value={(data.messageType as string) || 'private'}
          onChange={(e) => onChange('messageType', e.target.value)}
        >
          <option value="private">私聊发送</option>
          <option value="group">群文件上传</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          {(data.messageType as string) === 'group' ? '文件将上传到群文件' : '文件将通过私聊发送'}
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="targetId">{(data.messageType as string) === 'group' ? '群号' : 'QQ号'}</Label>
        <QQContactSelect
          value={(data.targetId as string) || ''}
          onChange={(v) => onChange('targetId', v)}
          placeholder={(data.messageType as string) === 'group' ? '输入或选择群号' : '输入或选择QQ号'}
          type={(data.messageType as string) === 'group' ? 'group' : 'private'}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="filePath">文件路径</Label>
        <div className="flex gap-1">
          <VariableInput
            value={(data.filePath as string) || ''}
            onChange={(v) => onChange('filePath', v)}
            placeholder="本地文件路径"
            className="flex-1"
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="shrink-0"
            onClick={async () => {
              try {
                const result = await systemApi.selectFile('选择文件', undefined, [
                  ['所有文件', '*.*']
                ])
                if (result.data?.success && result.data.path) {
                  onChange('filePath', result.data.path)
                }
              } catch (error) {
                console.error('选择文件失败:', error)
              }
            }}
          >
            <FolderOpen className="w-4 h-4" />
          </Button>
        </div>
      </div>
      {(data.messageType as string) === 'group' && (
        <div className="space-y-2">
          <Label htmlFor="folderId">群文件夹ID（可选）</Label>
          <VariableInput
            value={(data.folderId as string) || ''}
            onChange={(v) => onChange('folderId', v)}
            placeholder="留空则上传到根目录"
          />
          <p className="text-xs text-muted-foreground">指定群文件夹ID，留空则上传到群文件根目录</p>
        </div>
      )}
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量（可选）</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存发送结果的变量名"
        />
      </div>
    </>
  )
}

// QQ获取好友列表配置
export function QQGetFriendsConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存好友列表的变量名"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">返回好友列表数组，包含 user_id、nickname 等字段</p>
      </div>
    </>
  )
}

// QQ获取群列表配置
export function QQGetGroupsConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存群列表的变量名"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">返回群列表数组，包含 group_id、group_name 等字段</p>
      </div>
    </>
  )
}

// QQ获取群成员列表配置
export function QQGetGroupMembersConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="groupId">群号</Label>
        <QQContactSelect
          value={(data.groupId as string) || ''}
          onChange={(v) => onChange('groupId', v)}
          placeholder="输入或选择群号"
          type="group"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存群成员列表的变量名"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">返回成员列表数组，包含 user_id、nickname、card 等字段</p>
      </div>
    </>
  )
}

// QQ获取登录信息配置
export function QQGetLoginInfoConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存登录信息的变量名"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">返回对象，包含 user_id 和 nickname 字段</p>
      </div>
    </>
  )
}

// QQ等待消息配置
export function QQWaitMessageConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const apiUrl = (data.apiUrl as string) || 'http://127.0.0.1:3000'
  
  return (
    <>
      <NapCatServiceManager />
      <div className="space-y-2">
        <Label htmlFor="apiUrl">OneBot API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="http://127.0.0.1:3000"
        />
        <QQServiceStatus apiUrl={apiUrl} />
      </div>
      <div className="space-y-2">
        <Label htmlFor="sourceType">消息来源</Label>
        <Select
          id="sourceType"
          value={(data.sourceType as string) || 'any'}
          onChange={(e) => onChange('sourceType', e.target.value)}
        >
          <option value="any">任意消息</option>
          <option value="private">仅私聊</option>
          <option value="group">仅群聊</option>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="senderId">发送者QQ号（可选）</Label>
        <QQContactSelect
          value={(data.senderId as string) || ''}
          onChange={(v) => onChange('senderId', v)}
          placeholder="留空则不限制发送者"
          type="private"
        />
        <p className="text-xs text-muted-foreground">只接收指定QQ号发送的消息</p>
      </div>
      {((data.sourceType as string) === 'group' || (data.sourceType as string) === 'any') && (
        <div className="space-y-2">
          <Label htmlFor="groupId">群号（可选）</Label>
          <QQContactSelect
            value={(data.groupId as string) || ''}
            onChange={(v) => onChange('groupId', v)}
            placeholder="留空则不限制群"
            type="group"
          />
          <p className="text-xs text-muted-foreground">只接收指定群的消息</p>
        </div>
      )}
      <div className="space-y-2">
        <Label htmlFor="matchMode">匹配模式</Label>
        <Select
          id="matchMode"
          value={(data.matchMode as string) || 'contains'}
          onChange={(e) => onChange('matchMode', e.target.value)}
        >
          <option value="any">任意消息（不匹配内容）</option>
          <option value="contains">包含关键词</option>
          <option value="equals">完全匹配</option>
          <option value="regex">正则表达式</option>
        </Select>
      </div>
      {(data.matchMode as string) !== 'any' && (
        <div className="space-y-2">
          <Label htmlFor="matchContent">匹配内容</Label>
          <VariableInput
            value={(data.matchContent as string) || ''}
            onChange={(v) => onChange('matchContent', v)}
            placeholder={(data.matchMode as string) === 'regex' ? '正则表达式' : '要匹配的文本'}
          />
          <p className="text-xs text-muted-foreground">
            {(data.matchMode as string) === 'contains' && '消息中包含此文本时触发'}
            {(data.matchMode as string) === 'equals' && '消息内容完全等于此文本时触发'}
            {(data.matchMode as string) === 'regex' && '消息匹配此正则表达式时触发'}
          </p>
        </div>
      )}
      <div className="space-y-2">
        <Label htmlFor="waitTimeout">等待超时（秒）</Label>
        <VariableInput
          value={String((data.waitTimeout as number) ?? 0)}
          onChange={(v) => {
            const num = parseInt(v)
            onChange('waitTimeout', isNaN(num) ? 0 : num)
          }}
          placeholder="0"
        />
        <p className="text-xs text-muted-foreground">0 表示无限等待（默认）</p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="pollInterval">轮询间隔（秒）</Label>
        <VariableInput
          value={String((data.pollInterval as number) ?? 0.3)}
          onChange={(v) => {
            const num = parseFloat(v)
            onChange('pollInterval', isNaN(num) || num < 0.1 ? 0.3 : num)
          }}
          placeholder="0.3"
        />
        <p className="text-xs text-muted-foreground">建议 0.3 秒以实现近乎实时响应，最小 0.1 秒</p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="resultVariable">结果变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存收到消息的变量名"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">
          返回对象包含: message_id, sender_id, sender_nickname, group_id, raw_message 等字段
        </p>
      </div>
    </>
  )
}
