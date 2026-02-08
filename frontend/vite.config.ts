import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'

/**
 * 加载配置文件
 */
function loadConfig() {
  const configPath = path.resolve(__dirname, '../WebRPAConfig.json')
  try {
    if (fs.existsSync(configPath)) {
      const configContent = fs.readFileSync(configPath, 'utf-8')
      const config = JSON.parse(configContent)
      return config.frontend || {}
    } else {
      console.log('[Config] 配置文件不存在，使用默认配置')
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    console.error('[Config] 读取配置文件失败:', errorMessage, '，使用默认配置')
  }
  
  // 返回默认配置
  return {
    host: '0.0.0.0',
    port: 5173
  }
}

// 加载配置
const config = loadConfig()
console.log(`[Config] 前端服务配置: host=${config.host}, port=${config.port}`)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: config.host || '0.0.0.0', // 允许局域网访问
    port: config.port || 5173,
    strictPort: true, // 端口被占用时报错，而不是自动尝试下一个端口
  },
})
