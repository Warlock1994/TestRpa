import type React from 'react'
import type { NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { NumberInput } from '@/components/ui/number-input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { VariableInput } from '@/components/ui/variable-input'
import { VariableNameInput } from '@/components/ui/variable-name-input'
import { VariableRefInput } from '@/components/ui/variable-ref-input'

type RenderSelectorInput = (id: string, label: string, placeholder: string) => React.ReactNode

// AI大脑配置
export function AIChatConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="apiUrl">API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="https://api.openai.com/v1/chat/completions，支持 {变量名}"
        />
        <p className="text-xs text-muted-foreground">
          支持 OpenAI、智谱、Deepseek 等兼容接口
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="apiKey">API密钥</Label>
        <VariableInput
          value={(data.apiKey as string) || ''}
          onChange={(v) => onChange('apiKey', v)}
          placeholder="sk-xxx 或其他API密钥，支持 {变量名}"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="model">模型名称</Label>
        <VariableInput
          value={(data.model as string) || ''}
          onChange={(v) => onChange('model', v)}
          placeholder="gpt-3.5-turbo / glm-4 / deepseek-chat，支持 {变量名}"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="systemPrompt">系统提示词 (可选)</Label>
        <VariableInput
          value={(data.systemPrompt as string) || ''}
          onChange={(v) => onChange('systemPrompt', v)}
          placeholder="设定AI的角色和行为，支持 {变量名}"
          multiline
          rows={3}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="userPrompt">用户提示词</Label>
        <VariableInput
          value={(data.userPrompt as string) || ''}
          onChange={(v) => onChange('userPrompt', v)}
          placeholder="发送给AI的内容，支持 {变量名}"
          multiline
          rows={4}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="variableName">存储回复到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="temperature">温度 (0-2)</Label>
        <NumberInput
          id="temperature"
          value={(data.temperature as number) ?? 0.7}
          onChange={(v) => onChange('temperature', v)}
          defaultValue={0.7}
          min={0}
          max={2}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="maxTokens">最大Token数</Label>
        <NumberInput
          id="maxTokens"
          value={(data.maxTokens as number) ?? 2000}
          onChange={(v) => onChange('maxTokens', v)}
          defaultValue={2000}
          min={1}
        />
      </div>
    </>
  )
}

// AI视觉配置
export function AIVisionConfig({ 
  data, 
  onChange, 
  renderSelectorInput 
}: { 
  data: NodeData
  onChange: (key: string, value: unknown) => void
  renderSelectorInput: RenderSelectorInput
}) {
  const imageSource = (data.imageSource as string) || 'element'
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="apiUrl">API地址</Label>
        <VariableInput
          value={(data.apiUrl as string) || ''}
          onChange={(v) => onChange('apiUrl', v)}
          placeholder="https://open.bigmodel.cn/api/paas/v4/chat/completions，支持 {变量名}"
        />
        <p className="text-xs text-muted-foreground">
          支持 OpenAI、智谱GLM-4V 等视觉模型接口
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="apiKey">API密钥</Label>
        <VariableInput
          value={(data.apiKey as string) || ''}
          onChange={(v) => onChange('apiKey', v)}
          placeholder="API密钥，支持 {变量名}"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="model">模型名称</Label>
        <VariableInput
          value={(data.model as string) || ''}
          onChange={(v) => onChange('model', v)}
          placeholder="glm-4v / gpt-4-vision-preview，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="imageSource">图片来源</Label>
        <Select
          id="imageSource"
          value={imageSource}
          onChange={(e) => onChange('imageSource', e.target.value)}
        >
          <option value="element">页面元素截图</option>
          <option value="screenshot">当前页面截图</option>
          <option value="url">图片URL</option>
          <option value="variable">变量 (Base64/路径)</option>
        </Select>
      </div>
      
      {imageSource === 'element' && (
        renderSelectorInput('imageSelector', '图片元素选择器', 'img.target 或 #image')
      )}
      
      {imageSource === 'url' && (
        <div className="space-y-2">
          <Label htmlFor="imageUrl">图片URL</Label>
          <VariableInput
            value={(data.imageUrl as string) || ''}
            onChange={(v) => onChange('imageUrl', v)}
            placeholder="https://example.com/image.jpg，支持 {变量名}"
          />
        </div>
      )}
      
      {imageSource === 'variable' && (
        <div className="space-y-2">
          <Label htmlFor="imageVariable">图片变量名</Label>
          <VariableRefInput
            id="imageVariable"
            value={(data.imageVariable as string) || ''}
            onChange={(v) => onChange('imageVariable', v)}
            placeholder="填写变量名，如: imageData"
          />
          <p className="text-xs text-muted-foreground">
            直接填写包含Base64或文件路径的变量名
          </p>
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="userPrompt">提问内容</Label>
        <VariableInput
          value={(data.userPrompt as string) || ''}
          onChange={(v) => onChange('userPrompt', v)}
          placeholder="请描述这张图片中的内容，支持 {变量名}"
          multiline
          rows={4}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储回复到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="maxTokens">最大Token数</Label>
        <NumberInput
          id="maxTokens"
          value={(data.maxTokens as number) ?? 1000}
          onChange={(v) => onChange('maxTokens', v)}
          defaultValue={1000}
          min={1}
        />
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          <strong>AI视觉模块</strong>可以让AI"看"图片并回答问题。<br/>
          • 支持识别图片内容、提取文字、分析图表等<br/>
          • 推荐使用智谱GLM-4V或OpenAI GPT-4V模型
        </p>
      </div>
    </>
  )
}

// API请求配置
export function ApiRequestConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="requestUrl">请求地址</Label>
        <VariableInput
          value={(data.requestUrl as string) || ''}
          onChange={(v) => onChange('requestUrl', v)}
          placeholder="https://api.example.com/data，支持 {变量名}"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="requestMethod">请求方法</Label>
        <Select
          id="requestMethod"
          value={(data.requestMethod as string) || 'GET'}
          onChange={(e) => onChange('requestMethod', e.target.value)}
        >
          <option value="GET">GET</option>
          <option value="POST">POST</option>
          <option value="PUT">PUT</option>
          <option value="DELETE">DELETE</option>
          <option value="PATCH">PATCH</option>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="requestHeaders">请求头 (JSON格式，可选)</Label>
        <textarea
          id="requestHeaders"
          className="w-full min-h-[60px] px-3 py-2 text-sm rounded-md border border-input bg-background font-mono text-xs"
          value={(data.requestHeaders as string) || ''}
          onChange={(e) => onChange('requestHeaders', e.target.value)}
          placeholder='{"Content-Type": "application/json", "Authorization": "Bearer {token}"}'
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="requestBody">请求体 (可选)</Label>
        <textarea
          id="requestBody"
          className="w-full min-h-[80px] px-3 py-2 text-sm rounded-md border border-input bg-background font-mono text-xs"
          value={(data.requestBody as string) || ''}
          onChange={(e) => onChange('requestBody', e.target.value)}
          placeholder='{"key": "value", "name": "{变量名}"}'
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="variableName">存储响应到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名（存储完整响应JSON）"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="requestTimeout">超时时间 (秒)</Label>
        <NumberInput
          id="requestTimeout"
          value={(data.requestTimeout as number) ?? 30}
          onChange={(v) => onChange('requestTimeout', v)}
          defaultValue={30}
          min={1}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        发送HTTP请求并将响应存储到变量，可配合JSON解析模块提取数据
      </p>
    </>
  )
}

// AI智能爬虫配置
export function AISmartScraperConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const llmProvider = (data.llmProvider as string) || 'ollama'
  
  return (
    <>
      <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg mb-4">
        <p className="text-sm text-red-900 font-semibold mb-2">
          🧪 实验性功能 - 不推荐生产使用
        </p>
        <p className="text-xs text-red-800 space-y-1">
          <strong>已知问题：</strong><br />
          • 速度极慢（10-30秒），成本高（消耗 API 额度）<br />
          • 准确率低，经常返回错误或无用的分析文本<br />
          • 对复杂网页效果差，容易理解错误<br />
          <br />
          <strong>适用场景：</strong><br />
          • 仅适合提取文章内容、大段文本<br />
          • 不适合结构化数据提取<br />
          • 不适合需要快速响应的场景<br />
          <br />
          <strong>推荐：</strong>使用传统的"获取元素列表"等模块，更快更准确
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="url">目标网页URL</Label>
        <VariableInput
          value={(data.url as string) || ''}
          onChange={(v) => onChange('url', v)}
          placeholder="https://example.com，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="prompt">提取提示词</Label>
        <VariableInput
          value={(data.prompt as string) || ''}
          onChange={(v) => onChange('prompt', v)}
          placeholder='示例：Extract top 10 items. Return JSON: [{"title": "...", "value": 123}]. No explanation.'
          multiline
          rows={4}
        />
        <p className="text-xs text-muted-foreground">
          <strong>重要：</strong>必须用英文，明确指定返回格式（JSON数组等），并强调"No explanation"
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitTime">页面加载等待时间 (秒)</Label>
        <NumberInput
          id="waitTime"
          value={(data.waitTime as number) ?? 3}
          onChange={(v) => onChange('waitTime', v)}
          defaultValue={3}
          min={0}
          max={30}
        />
        <p className="text-xs text-muted-foreground">
          访问网页后等待指定秒数再开始爬取，让页面有时间完全加载（推荐 3-5 秒）
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储结果到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="llmProvider">LLM提供商</Label>
        <Select
          id="llmProvider"
          value={llmProvider}
          onChange={(e) => onChange('llmProvider', e.target.value)}
        >
          <option value="ollama">Ollama (本地免费)</option>
          <option value="openai">OpenAI</option>
          <option value="groq">Groq</option>
          <option value="gemini">Google Gemini</option>
          <option value="azure">Azure OpenAI</option>
          <option value="zhipu">智谱 AI (GLM)</option>
          <option value="deepseek">Deepseek</option>
          <option value="custom">自定义</option>
        </Select>
      </div>
      
      {llmProvider !== 'ollama' && (
        <div className="space-y-2">
          <Label htmlFor="apiUrl">API地址</Label>
          <VariableInput
            value={(data.apiUrl as string) || ''}
            onChange={(v) => onChange('apiUrl', v)}
            placeholder={
              llmProvider === 'openai' ? 'https://api.openai.com/v1' :
              llmProvider === 'zhipu' ? 'https://open.bigmodel.cn/api/paas/v4' :
              llmProvider === 'deepseek' ? 'https://api.deepseek.com' :
              llmProvider === 'groq' ? 'https://api.groq.com/openai/v1' :
              llmProvider === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' :
              '自定义API地址，支持 {变量名}'
            }
          />
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="llmModel">模型名称</Label>
        <VariableInput
          value={(data.llmModel as string) || 'llama3.2'}
          onChange={(v) => onChange('llmModel', v)}
          placeholder={llmProvider === 'ollama' ? 'llama3.2' : 'gpt-4o-mini'}
        />
        <p className="text-xs text-muted-foreground">
          {llmProvider === 'ollama' 
            ? '本地模型，如 llama3.2、qwen2.5 等' 
            : '云端模型名称'}
        </p>
      </div>
      
      {llmProvider !== 'ollama' && (
        <div className="space-y-2">
          <Label htmlFor="apiKey">API Key</Label>
          <VariableInput
            value={(data.apiKey as string) || ''}
            onChange={(v) => onChange('apiKey', v)}
            placeholder="sk-xxx，支持 {变量名}"
          />
        </div>
      )}
      
      {llmProvider === 'azure' && (
        <div className="space-y-2">
          <Label htmlFor="azureEndpoint">Azure Endpoint</Label>
          <VariableInput
            value={(data.azureEndpoint as string) || ''}
            onChange={(v) => onChange('azureEndpoint', v)}
            placeholder="https://your-resource.openai.azure.com/"
          />
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="headless">无头模式</Label>
        <Select
          id="headless"
          value={String(data.headless ?? true)}
          onChange={(e) => onChange('headless', e.target.value === 'true')}
        >
          <option value="true">是（后台运行）</option>
          <option value="false">否（显示浏览器）</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="verbose">详细日志</Label>
        <Select
          id="verbose"
          value={String(data.verbose ?? false)}
          onChange={(e) => onChange('verbose', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg">
        <p className="text-xs text-purple-900">
          <strong>🤖 AI智能爬虫</strong><br/>
          • 优点：用自然语言描述即可提取数据，适应网页结构变化<br/>
          • 缺点：速度比传统爬虫慢，需要LLM支持<br/>
          • 推荐：使用Ollama本地运行，完全免费
        </p>
      </div>
    </>
  )
}

// AI智能元素选择器配置
export function AIElementSelectorConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const llmProvider = (data.llmProvider as string) || 'ollama'
  
  return (
    <>
      <div className="p-3 bg-red-50 border-2 border-red-300 rounded-lg mb-4">
        <p className="text-sm text-red-900 font-semibold mb-2">
          🧪 实验性功能 - 不推荐生产使用
        </p>
        <p className="text-xs text-red-800 space-y-1">
          <strong>已知问题：</strong><br />
          • 准确率极低，经常找不到元素或返回错误选择器<br />
          • 对复杂网页效果差，容易被页面内容干扰<br />
          • 速度慢，成本高（消耗 API 额度）<br />
          <br />
          <strong>推荐：</strong>使用浏览器开发者工具（F12）手动获取选择器，更快更准确
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="url">目标网页URL</Label>
        <VariableInput
          value={(data.url as string) || ''}
          onChange={(v) => onChange('url', v)}
          placeholder="https://example.com，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="elementDescription">元素描述</Label>
        <VariableInput
          value={(data.elementDescription as string) || ''}
          onChange={(v) => onChange('elementDescription', v)}
          placeholder="用自然语言描述要查找的元素，如：登录按钮、搜索输入框"
          multiline
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          用自然语言描述你想找的页面元素（建议用英文，效果更好）
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitTime">页面加载等待时间 (秒)</Label>
        <NumberInput
          id="waitTime"
          value={(data.waitTime as number) ?? 3}
          onChange={(v) => onChange('waitTime', v)}
          defaultValue={3}
          min={0}
          max={30}
        />
        <p className="text-xs text-muted-foreground">
          访问网页后等待指定秒数再开始分析，让页面有时间完全加载（推荐 3-5 秒）
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储选择器到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="变量名"
        />
        <p className="text-xs text-muted-foreground">
          AI找到的CSS选择器将保存到此变量
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="llmProvider">LLM提供商</Label>
        <Select
          id="llmProvider"
          value={llmProvider}
          onChange={(e) => onChange('llmProvider', e.target.value)}
        >
          <option value="ollama">Ollama (本地免费)</option>
          <option value="openai">OpenAI</option>
          <option value="groq">Groq</option>
          <option value="gemini">Google Gemini</option>
          <option value="azure">Azure OpenAI</option>
          <option value="zhipu">智谱 AI (GLM)</option>
          <option value="deepseek">Deepseek</option>
          <option value="custom">自定义</option>
        </Select>
      </div>
      
      {llmProvider !== 'ollama' && (
        <div className="space-y-2">
          <Label htmlFor="apiUrl">API地址</Label>
          <VariableInput
            value={(data.apiUrl as string) || ''}
            onChange={(v) => onChange('apiUrl', v)}
            placeholder={
              llmProvider === 'openai' ? 'https://api.openai.com/v1' :
              llmProvider === 'zhipu' ? 'https://open.bigmodel.cn/api/paas/v4' :
              llmProvider === 'deepseek' ? 'https://api.deepseek.com' :
              llmProvider === 'groq' ? 'https://api.groq.com/openai/v1' :
              llmProvider === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' :
              '自定义API地址，支持 {变量名}'
            }
          />
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="llmModel">模型名称</Label>
        <VariableInput
          value={(data.llmModel as string) || 'llama3.2'}
          onChange={(v) => onChange('llmModel', v)}
          placeholder={llmProvider === 'ollama' ? 'llama3.2' : 'gpt-4o-mini'}
        />
        <p className="text-xs text-muted-foreground">
          {llmProvider === 'ollama' 
            ? '本地模型，如 llama3.2、qwen2.5 等' 
            : '云端模型名称'}
        </p>
      </div>
      
      {llmProvider !== 'ollama' && (
        <div className="space-y-2">
          <Label htmlFor="apiKey">API Key</Label>
          <VariableInput
            value={(data.apiKey as string) || ''}
            onChange={(v) => onChange('apiKey', v)}
            placeholder="sk-xxx，支持 {变量名}"
          />
        </div>
      )}
      
      {llmProvider === 'azure' && (
        <div className="space-y-2">
          <Label htmlFor="azureEndpoint">Azure Endpoint</Label>
          <VariableInput
            value={(data.azureEndpoint as string) || ''}
            onChange={(v) => onChange('azureEndpoint', v)}
            placeholder="https://your-resource.openai.azure.com/"
          />
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="verbose">详细日志</Label>
        <Select
          id="verbose"
          value={String(data.verbose ?? false)}
          onChange={(e) => onChange('verbose', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="p-3 bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900">
          <strong>🎯 AI智能元素选择器</strong><br/>
          • 优点：即使网页结构变化，也能准确找到元素<br />
          • 使用场景：网站频繁改版、选择器不稳定<br />
          • 工作原理：AI 访问指定 URL，分析页面后返回匹配元素的 CSS 选择器<br />
          • 推荐：使用Ollama本地运行，完全免费
        </p>
      </div>
    </>
  )
}


// Firecrawl AI 单页数据抓取配置
export function FirecrawlScrapeConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="url">目标URL</Label>
        <VariableInput
          value={(data.url as string) || ''}
          onChange={(v) => onChange('url', v)}
          placeholder="https://example.com，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储结果到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="scrape_result"
          isStorageVariable={true}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="formats">返回格式</Label>
        <div className="space-y-1">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={(data.formats as string[] || ['markdown']).includes('markdown')}
              onChange={(e) => {
                const formats = (data.formats as string[] || ['markdown'])
                if (e.target.checked) {
                  onChange('formats', [...formats, 'markdown'])
                } else {
                  onChange('formats', formats.filter(f => f !== 'markdown'))
                }
              }}
            />
            <span className="text-sm">Markdown</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={(data.formats as string[] || []).includes('html')}
              onChange={(e) => {
                const formats = (data.formats as string[] || ['markdown'])
                if (e.target.checked) {
                  onChange('formats', [...formats, 'html'])
                } else {
                  onChange('formats', formats.filter(f => f !== 'html'))
                }
              }}
            />
            <span className="text-sm">HTML</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={(data.formats as string[] || []).includes('screenshot')}
              onChange={(e) => {
                const formats = (data.formats as string[] || ['markdown'])
                if (e.target.checked) {
                  onChange('formats', [...formats, 'screenshot'])
                } else {
                  onChange('formats', formats.filter(f => f !== 'screenshot'))
                }
              }}
            />
            <span className="text-sm">Screenshot</span>
          </label>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="onlyMainContent">只提取主要内容</Label>
        <Select
          id="onlyMainContent"
          value={String(data.onlyMainContent ?? true)}
          onChange={(e) => onChange('onlyMainContent', e.target.value === 'true')}
        >
          <option value="true">是</option>
          <option value="false">否</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="includeTags">包含标签 (可选)</Label>
        <VariableInput
          value={(data.includeTags as string) || ''}
          onChange={(v) => onChange('includeTags', v)}
          placeholder="article, main, .content (逗号分隔)"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="excludeTags">排除标签 (可选)</Label>
        <VariableInput
          value={(data.excludeTags as string) || ''}
          onChange={(v) => onChange('excludeTags', v)}
          placeholder="nav, footer, .ads (逗号分隔)"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitFor">等待时间 (毫秒，可选)</Label>
        <VariableInput
          value={(data.waitFor as string) || ''}
          onChange={(v) => onChange('waitFor', v)}
          placeholder="3000"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="timeout">超时时间 (毫秒)</Label>
        <NumberInput
          id="timeout"
          value={(data.timeout as number) ?? 30000}
          onChange={(v) => onChange('timeout', v)}
          defaultValue={30000}
          min={1000}
        />
      </div>
      
      <div className="p-3 bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg">
        <p className="text-xs text-orange-900">
          <strong>🔥 Firecrawl AI 单页数据抓取</strong><br/>
          • 智能提取网页结构化数据<br />
          • 支持 Markdown、HTML、截图等格式<br />
          • 自动处理 JavaScript 渲染<br />
          • 过滤广告和无关内容
        </p>
      </div>
    </>
  )
}

// Firecrawl AI 网站链接抓取配置
export function FirecrawlMapConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="url">目标URL</Label>
        <VariableInput
          value={(data.url as string) || ''}
          onChange={(v) => onChange('url', v)}
          placeholder="https://example.com，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储链接列表到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="map_result"
          isStorageVariable={true}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="search">搜索关键词 (可选)</Label>
        <VariableInput
          value={(data.search as string) || ''}
          onChange={(v) => onChange('search', v)}
          placeholder="只返回包含关键词的链接，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="limit">链接数量限制</Label>
        <NumberInput
          id="limit"
          value={(data.limit as number) ?? 5000}
          onChange={(v) => onChange('limit', v)}
          defaultValue={5000}
          min={1}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="ignoreSitemap">忽略 Sitemap</Label>
        <Select
          id="ignoreSitemap"
          value={String(data.ignoreSitemap ?? false)}
          onChange={(e) => onChange('ignoreSitemap', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="includeSubdomains">包含子域名</Label>
        <Select
          id="includeSubdomains"
          value={String(data.includeSubdomains ?? false)}
          onChange={(e) => onChange('includeSubdomains', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="p-3 bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900">
          <strong>🗺️ Firecrawl AI 网站链接抓取</strong><br/>
          • 智能发现网站的所有链接<br />
          • 可用于构建网站地图<br />
          • 支持关键词过滤<br />
          • 返回链接数组，可配合循环使用
        </p>
      </div>
    </>
  )
}

// Firecrawl AI 全站数据抓取配置
export function FirecrawlCrawlConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="url">目标URL</Label>
        <VariableInput
          value={(data.url as string) || ''}
          onChange={(v) => onChange('url', v)}
          placeholder="https://example.com，支持 {变量名}"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="variableName">存储结果到变量</Label>
        <VariableNameInput
          id="variableName"
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="crawl_result"
          isStorageVariable={true}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="maxDepth">最大爬取深度</Label>
        <NumberInput
          id="maxDepth"
          value={(data.maxDepth as number) ?? 2}
          onChange={(v) => onChange('maxDepth', v)}
          defaultValue={2}
          min={1}
          max={10}
        />
        <p className="text-xs text-muted-foreground">
          深度越大，爬取的页面越多，耗时越长
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="limit">页面数量限制</Label>
        <NumberInput
          id="limit"
          value={(data.limit as number) ?? 100}
          onChange={(v) => onChange('limit', v)}
          defaultValue={100}
          min={1}
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="includePaths">包含路径 (可选)</Label>
        <VariableInput
          value={(data.includePaths as string) || ''}
          onChange={(v) => onChange('includePaths', v)}
          placeholder="/blog, /docs (逗号分隔)"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="excludePaths">排除路径 (可选)</Label>
        <VariableInput
          value={(data.excludePaths as string) || ''}
          onChange={(v) => onChange('excludePaths', v)}
          placeholder="/admin, /login (逗号分隔)"
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="formats">返回格式</Label>
        <div className="space-y-1">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={(data.formats as string[] || ['markdown']).includes('markdown')}
              onChange={(e) => {
                const formats = (data.formats as string[] || ['markdown'])
                if (e.target.checked) {
                  onChange('formats', [...formats, 'markdown'])
                } else {
                  onChange('formats', formats.filter(f => f !== 'markdown'))
                }
              }}
            />
            <span className="text-sm">Markdown</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={(data.formats as string[] || []).includes('html')}
              onChange={(e) => {
                const formats = (data.formats as string[] || ['markdown'])
                if (e.target.checked) {
                  onChange('formats', [...formats, 'html'])
                } else {
                  onChange('formats', formats.filter(f => f !== 'html'))
                }
              }}
            />
            <span className="text-sm">HTML</span>
          </label>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="onlyMainContent">只提取主要内容</Label>
        <Select
          id="onlyMainContent"
          value={String(data.onlyMainContent ?? true)}
          onChange={(e) => onChange('onlyMainContent', e.target.value === 'true')}
        >
          <option value="true">是</option>
          <option value="false">否</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="ignoreSitemap">忽略 Sitemap</Label>
        <Select
          id="ignoreSitemap"
          value={String(data.ignoreSitemap ?? false)}
          onChange={(e) => onChange('ignoreSitemap', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="allowBackwardLinks">允许回退链接</Label>
        <Select
          id="allowBackwardLinks"
          value={String(data.allowBackwardLinks ?? false)}
          onChange={(e) => onChange('allowBackwardLinks', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="allowExternalLinks">允许外部链接</Label>
        <Select
          id="allowExternalLinks"
          value={String(data.allowExternalLinks ?? false)}
          onChange={(e) => onChange('allowExternalLinks', e.target.value === 'true')}
        >
          <option value="false">否</option>
          <option value="true">是</option>
        </Select>
      </div>
      
      <div className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg">
        <p className="text-xs text-purple-900">
          <strong>🕷️ Firecrawl AI 全站数据抓取</strong><br/>
          • 智能爬取整个网站的数据<br />
          • 支持深度爬取和智能过滤<br />
          • 自动处理分页和动态加载<br />
          • ⚠️ 注意：全站爬取可能需要几分钟
        </p>
      </div>
    </>
  )
}
