/**
 * 配置管理服务
 * 统一管理后端 API 地址和端口配置
 */

// 获取后端基础 URL
export function getBackendBaseUrl(): string {
  const hostname = window.location.hostname
  const backendPort = sessionStorage.getItem('backendPort') || '8000'
  
  // 如果是 localhost 或 127.0.0.1，使用 localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `http://localhost:${backendPort}`
  }
  // 否则使用当前访问的主机名（局域网 IP）
  return `http://${hostname}:${backendPort}`
}

// 获取后端端口号
export function getBackendPort(): string {
  return sessionStorage.getItem('backendPort') || '8000'
}

// 获取前端端口号
export function getFrontendPort(): string {
  return window.location.port || '5173'
}

// 设置后端端口号
export function setBackendPort(port: number | string): void {
  sessionStorage.setItem('backendPort', String(port))
}
