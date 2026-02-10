import type { NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { NumberInput } from '@/components/ui/number-input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { VariableInput } from '@/components/ui/variable-input'
import { VariableNameInput } from '@/components/ui/variable-name-input'
import { PathInput } from '@/components/ui/path-input'
import { PhoneCoordinateInput } from '@/components/ui/phone-coordinate-input'
import { ImagePathInput } from '@/components/ui/image-path-input'
import { Checkbox } from '@/components/ui/checkbox'

// 点击坐标配置
export function PhoneTapConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label>点击坐标</Label>
        <PhoneCoordinateInput
          xValue={(data.x as string) || ''}
          yValue={(data.y as string) || ''}
          onXChange={(v) => onChange('x', v)}
          onYChange={(v) => onChange('y', v)}
        />
        <p className="text-xs text-muted-foreground">
          点击「拾取」按钮启动手机镜像窗口，在镜像中点击要获取坐标的位置
        </p>
      </div>
    </>
  )
}

// 滑动配置
export function PhoneSwipeConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const swipeMode = (data.swipeMode as string) || 'coordinate' // coordinate 或 offset
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="swipeMode">滑动模式</Label>
        <Select
          id="swipeMode"
          value={swipeMode}
          onChange={(e) => onChange('swipeMode', e.target.value)}
        >
          <option value="coordinate">坐标模式</option>
          <option value="offset">偏移模式</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          坐标模式：指定起点和终点坐标<br />
          偏移模式：指定起点坐标和滑动距离
        </p>
      </div>

      {swipeMode === 'coordinate' ? (
        <>
          <div className="space-y-2">
            <Label>起点坐标</Label>
            <PhoneCoordinateInput
              xValue={(data.x1 as string) || ''}
              yValue={(data.y1 as string) || ''}
              onXChange={(v) => onChange('x1', v)}
              onYChange={(v) => onChange('y1', v)}
            />
          </div>
          <div className="space-y-2">
            <Label>终点坐标</Label>
            <PhoneCoordinateInput
              xValue={(data.x2 as string) || ''}
              yValue={(data.y2 as string) || ''}
              onXChange={(v) => onChange('x2', v)}
              onYChange={(v) => onChange('y2', v)}
            />
          </div>
        </>
      ) : (
        <>
          <div className="space-y-2">
            <Label>起点坐标</Label>
            <PhoneCoordinateInput
              xValue={(data.x1 as string) || ''}
              yValue={(data.y1 as string) || ''}
              onXChange={(v) => onChange('x1', v)}
              onYChange={(v) => onChange('y1', v)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="offsetX">水平偏移（像素）</Label>
            <NumberInput
              id="offsetX"
              value={(data.offsetX as number) ?? 0}
              onChange={(v) => onChange('offsetX', v)}
              defaultValue={0}
              min={-2000}
              max={2000}
            />
            <p className="text-xs text-muted-foreground">
              正数向右，负数向左
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="offsetY">垂直偏移（像素）</Label>
            <NumberInput
              id="offsetY"
              value={(data.offsetY as number) ?? 0}
              onChange={(v) => onChange('offsetY', v)}
              defaultValue={0}
              min={-3000}
              max={3000}
            />
            <p className="text-xs text-muted-foreground">
              正数向下，负数向上
            </p>
          </div>
        </>
      )}

      <div className="space-y-2">
        <Label htmlFor="duration">滑动时长（毫秒）</Label>
        <NumberInput
          id="duration"
          value={(data.duration as number) ?? 300}
          onChange={(v) => onChange('duration', v)}
          defaultValue={300}
          min={100}
          max={5000}
        />
        <p className="text-xs text-muted-foreground">
          滑动动作的持续时间，值越大滑动越慢
        </p>
      </div>
    </>
  )
}

// 长按配置
export function PhoneLongPressConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label>长按坐标</Label>
        <PhoneCoordinateInput
          xValue={(data.x as string) || ''}
          yValue={(data.y as string) || ''}
          onXChange={(v) => onChange('x', v)}
          onYChange={(v) => onChange('y', v)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="duration">长按时长（毫秒）</Label>
        <NumberInput
          id="duration"
          value={(data.duration as number) ?? 1000}
          onChange={(v) => onChange('duration', v)}
          defaultValue={1000}
          min={500}
          max={10000}
        />
        <p className="text-xs text-muted-foreground">
          长按的持续时间
        </p>
      </div>
    </>
  )
}

// 输入文本配置
export function PhoneInputTextConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="text">输入文本</Label>
        <VariableInput
          value={(data.text as string) || ''}
          onChange={(v) => onChange('text', v)}
          placeholder="要输入的文本内容"
          multiline
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          在当前焦点输入框中输入文本，支持变量引用
        </p>
      </div>
      
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-amber-900">
          ⚠️ 重要提示
        </p>
        <p className="text-xs text-amber-800">
          • 使用前请先用「📱 点击」模块点击输入框，确保输入框已获得焦点
        </p>
        <p className="text-xs text-amber-800">
          • 仅支持输入英文、数字和符号
        </p>
        <p className="text-xs text-amber-800">
          • <strong>不支持输入中文</strong>（Android 系统限制）
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 输入中文的替代方案
        </p>
        <p className="text-xs text-blue-800">
          1. 安装 ADBKeyboard 应用（推荐）
        </p>
        <p className="text-xs text-blue-700 ml-3">
          下载: github.com/senzhk/ADBKeyBoard
        </p>
        <p className="text-xs text-blue-800">
          2. 使用「📱 点击」+ 手动输入
        </p>
        <p className="text-xs text-blue-700 ml-3">
          先点击输入框，暂停工作流，手动输入中文
        </p>
        <p className="text-xs text-blue-800">
          3. 使用剪贴板（如果手机支持）
        </p>
        <p className="text-xs text-blue-700 ml-3">
          先复制中文到剪贴板，再用「📱 按键操作」粘贴
        </p>
      </div>
    </>
  )
}

// 按键操作配置
export function PhonePressKeyConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="keycode">按键类型</Label>
        <Select
          id="keycode"
          value={(data.keycode as string) || 'KEYCODE_HOME'}
          onChange={(e) => onChange('keycode', e.target.value)}
        >
          <option value="KEYCODE_HOME">Home键（主屏幕）</option>
          <option value="KEYCODE_BACK">Back键（返回）</option>
          <option value="KEYCODE_APP_SWITCH">Recent键（最近任务）</option>
          <option value="KEYCODE_POWER">Power键（电源）</option>
          <option value="KEYCODE_VOLUME_UP">音量+</option>
          <option value="KEYCODE_VOLUME_DOWN">音量-</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          模拟按下手机的物理按键或虚拟按键
        </p>
      </div>
    </>
  )
}

// 截图配置
export function PhoneScreenshotConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="savePath">保存路径（可选）</Label>
        <PathInput
          value={(data.savePath as string) || ''}
          onChange={(v) => onChange('savePath', v)}
          placeholder="留空则保存到默认目录"
          type="file"
        />
        <p className="text-xs text-muted-foreground">
          指定截图保存的完整路径，如：C:\screenshots\phone.png
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="variableName">存储路径到变量</Label>
        <VariableNameInput
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="保存文件路径的变量名"
          isStorageVariable={true}
        />
      </div>
    </>
  )
}

// 启动屏幕镜像配置
export function PhoneStartMirrorConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="bitRate">视频比特率（Mbps）</Label>
        <NumberInput
          id="bitRate"
          value={(data.bitRate as number) ?? 8}
          onChange={(v) => onChange('bitRate', v)}
          defaultValue={8}
          min={1}
          max={50}
        />
        <p className="text-xs text-muted-foreground">
          比特率越高画质越好，但占用带宽越大。建议：WiFi连接用8-16，USB连接可用更高值
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="maxSize">最大分辨率</Label>
        <NumberInput
          id="maxSize"
          value={(data.maxSize as number) ?? 1920}
          onChange={(v) => onChange('maxSize', v)}
          defaultValue={1920}
          min={480}
          max={2560}
        />
        <p className="text-xs text-muted-foreground">
          限制镜像画面的最大分辨率（长边），降低可提升性能
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="stayAwake"
          checked={(data.stayAwake as boolean) ?? true}
          onCheckedChange={(checked) => onChange('stayAwake', checked)}
        />
        <Label htmlFor="stayAwake" className="cursor-pointer">保持屏幕常亮</Label>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="turnScreenOff"
          checked={(data.turnScreenOff as boolean) ?? false}
          onCheckedChange={(checked) => onChange('turnScreenOff', checked)}
        />
        <Label htmlFor="turnScreenOff" className="cursor-pointer">关闭手机屏幕（仅镜像显示）</Label>
      </div>
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          💡 屏幕镜像会打开一个新窗口显示手机画面，可以在电脑上直接操作手机
        </p>
      </div>
    </>
  )
}

// 停止屏幕镜像配置
export function PhoneStopMirrorConfig() {
  return (
    <p className="text-xs text-muted-foreground">
      关闭当前正在运行的屏幕镜像窗口
    </p>
  )
}

// 安装应用配置
export function PhoneInstallAppConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="apkPath">APK文件路径</Label>
        <PathInput
          value={(data.apkPath as string) || ''}
          onChange={(v) => onChange('apkPath', v)}
          placeholder="C:\apps\example.apk"
          type="file"
        />
        <p className="text-xs text-muted-foreground">
          选择要安装的APK文件，支持变量引用
        </p>
      </div>
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-xs text-amber-800">
          ⚠️ 安装过程可能需要几秒到几十秒，请耐心等待
        </p>
      </div>
    </>
  )
}

// 启动应用配置
export function PhoneStartAppConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="packageName">应用包名或名称</Label>
        <VariableInput
          value={(data.packageName as string) || ''}
          onChange={(v) => onChange('packageName', v)}
          placeholder="com.tencent.mm 或 微信"
        />
        <p className="text-xs text-muted-foreground">
          支持两种方式：包名（如 com.tencent.mm）或应用名称（如 微信）
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="activityName">Activity名称（可选）</Label>
        <VariableInput
          value={(data.activityName as string) || ''}
          onChange={(v) => onChange('activityName', v)}
          placeholder=".ui.LauncherUI"
        />
        <p className="text-xs text-muted-foreground">
          指定要启动的Activity，留空则启动默认Activity
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 两种启动方式
        </p>
        <p className="text-xs text-blue-800">
          <strong>方式1：使用包名（推荐）</strong>
        </p>
        <p className="text-xs text-blue-700 ml-3">
          • 输入完整包名，如：com.tencent.mm
        </p>
        <p className="text-xs text-blue-700 ml-3">
          • 精确、快速、不会出错
        </p>
        <p className="text-xs text-blue-800 mt-2">
          <strong>方式2：使用应用名称</strong>
        </p>
        <p className="text-xs text-blue-700 ml-3">
          • 输入应用名称，如：微信、抖音
        </p>
        <p className="text-xs text-blue-700 ml-3">
          • 首次使用需要查询应用列表（约5-10秒）
        </p>
        <p className="text-xs text-blue-700 ml-3">
          • 如果有多个匹配，会提示使用包名
        </p>
      </div>
      
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-xs font-semibold text-amber-900">
          ⚠️ 注意事项
        </p>
        <p className="text-xs text-amber-800">
          • 使用应用名称时，只会搜索第三方应用（不包括系统应用）
        </p>
        <p className="text-xs text-amber-800">
          • 如果应用名称匹配到多个结果，请改用包名
        </p>
      </div>
    </>
  )
}

// 停止应用配置
export function PhoneStopAppConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="packageName">应用包名或名称</Label>
        <VariableInput
          value={(data.packageName as string) || ''}
          onChange={(v) => onChange('packageName', v)}
          placeholder="com.example.app 或 微信"
        />
        <p className="text-xs text-muted-foreground">
          支持两种方式：包名（如 com.tencent.mm）或应用名称（如 微信）
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-800">
          💡 停止应用会强制关闭应用进程，类似于在系统设置中"强行停止"
        </p>
      </div>
    </>
  )
}

// 卸载应用配置
export function PhoneUninstallAppConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="packageName">应用包名或名称</Label>
        <VariableInput
          value={(data.packageName as string) || ''}
          onChange={(v) => onChange('packageName', v)}
          placeholder="com.example.app 或 微信"
        />
        <p className="text-xs text-muted-foreground">
          支持两种方式：包名（如 com.tencent.mm）或应用名称（如 微信）
        </p>
      </div>
      
      <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-xs text-red-800">
          ⚠️ 卸载操作不可恢复，请谨慎使用
        </p>
      </div>
    </>
  )
}

// 推送文件配置
export function PhonePushFileConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="localPath">本地文件路径</Label>
        <PathInput
          value={(data.localPath as string) || ''}
          onChange={(v) => onChange('localPath', v)}
          placeholder="C:\files\example.txt"
          type="file"
        />
        <p className="text-xs text-muted-foreground">
          要推送到手机的本地文件路径
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="remotePath">手机目标路径</Label>
        <VariableInput
          value={(data.remotePath as string) || ''}
          onChange={(v) => onChange('remotePath', v)}
          placeholder="/sdcard/Download/example.txt"
        />
        <p className="text-xs text-muted-foreground">
          文件在手机上的保存路径，常用目录：/sdcard/Download/、/sdcard/DCIM/
        </p>
      </div>
    </>
  )
}

// 拉取文件配置
export function PhonePullFileConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="remotePath">手机文件路径</Label>
        <VariableInput
          value={(data.remotePath as string) || ''}
          onChange={(v) => onChange('remotePath', v)}
          placeholder="/sdcard/Download/example.txt"
        />
        <p className="text-xs text-muted-foreground">
          要从手机拉取的文件路径
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="localPath">本地保存路径</Label>
        <PathInput
          value={(data.localPath as string) || ''}
          onChange={(v) => onChange('localPath', v)}
          placeholder="C:\files\example.txt"
          type="file"
        />
        <p className="text-xs text-muted-foreground">
          文件保存到本地的路径
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="variableName">存储路径到变量</Label>
        <VariableNameInput
          value={(data.variableName as string) || ''}
          onChange={(v) => onChange('variableName', v)}
          placeholder="保存文件路径的变量名"
          isStorageVariable={true}
        />
      </div>
    </>
  )
}

// 点击图像配置
export function PhoneClickImageConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="imagePath">图像文件路径</Label>
        <ImagePathInput
          value={(data.imagePath as string) || ''}
          onChange={(v) => onChange('imagePath', v)}
          placeholder="从图像资源中选择或输入路径"
        />
        <p className="text-xs text-muted-foreground">
          从图像资源中选择要查找的目标图片
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="clickType">点击方式</Label>
        <Select
          id="clickType"
          value={(data.clickType as string) || 'click'}
          onChange={(e) => onChange('clickType', e.target.value)}
        >
          <option value="click">单击</option>
          <option value="long_press">长按</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          单击：快速点击一次；长按：按住1秒后松开
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="confidence">匹配置信度</Label>
        <NumberInput
          id="confidence"
          value={(data.confidence as number) ?? 0.8}
          onChange={(v) => onChange('confidence', v)}
          defaultValue={0.8}
          min={0.1}
          max={1.0}
          step={0.05}
        />
        <p className="text-xs text-muted-foreground">
          图像匹配的相似度阈值（0.1-1.0），值越高要求越严格
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="clickPosition">点击位置</Label>
        <Select
          id="clickPosition"
          value={(data.clickPosition as string) || 'center'}
          onChange={(e) => onChange('clickPosition', e.target.value)}
        >
          <option value="center">中心</option>
          <option value="top-left">左上角</option>
          <option value="top-right">右上角</option>
          <option value="bottom-left">左下角</option>
          <option value="bottom-right">右下角</option>
          <option value="top">顶部</option>
          <option value="bottom">底部</option>
          <option value="left">左侧</option>
          <option value="right">右侧</option>
          <option value="random">随机位置</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          在找到的图像区域内的哪个位置点击
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitTimeout">等待超时（秒）</Label>
        <NumberInput
          id="waitTimeout"
          value={(data.waitTimeout as number) ?? 10}
          onChange={(v) => onChange('waitTimeout', v)}
          defaultValue={10}
          min={1}
          max={60}
        />
        <p className="text-xs text-muted-foreground">
          等待图像出现的最长时间
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 使用提示
        </p>
        <p className="text-xs text-blue-800">
          • 图像文件应该是手机屏幕上要查找的元素截图
        </p>
        <p className="text-xs text-blue-800">
          • 如果匹配失败，可以降低置信度或重新截取更清晰的图像
        </p>
        <p className="text-xs text-blue-800">
          • 建议使用PNG格式的图像文件
        </p>
      </div>
    </>
  )
}

// 点击文本配置
export function PhoneClickTextConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="targetText">目标文本</Label>
        <VariableInput
          value={(data.targetText as string) || ''}
          onChange={(v) => onChange('targetText', v)}
          placeholder="要查找并点击的文本"
          multiline
          rows={2}
        />
        <p className="text-xs text-muted-foreground">
          在手机屏幕上查找并点击包含此文本的位置
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="clickType">点击方式</Label>
        <Select
          id="clickType"
          value={(data.clickType as string) || 'click'}
          onChange={(e) => onChange('clickType', e.target.value)}
        >
          <option value="click">单击</option>
          <option value="long_press">长按</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          单击：快速点击一次；长按：按住1秒后松开
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="matchMode">匹配模式</Label>
        <Select
          id="matchMode"
          value={(data.matchMode as string) || 'contains'}
          onChange={(e) => onChange('matchMode', e.target.value)}
        >
          <option value="contains">包含</option>
          <option value="exact">完全匹配</option>
          <option value="regex">正则表达式</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          包含：文本中包含目标文本即可<br />
          完全匹配：文本必须完全相同<br />
          正则表达式：使用正则表达式匹配
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="occurrence">匹配第几个</Label>
        <NumberInput
          id="occurrence"
          value={(data.occurrence as number) ?? 1}
          onChange={(v) => onChange('occurrence', v)}
          defaultValue={1}
          min={1}
          max={10}
        />
        <p className="text-xs text-muted-foreground">
          如果屏幕上有多个匹配的文本，点击第几个（从1开始）
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitTimeout">等待超时（秒）</Label>
        <NumberInput
          id="waitTimeout"
          value={(data.waitTimeout as number) ?? 10}
          onChange={(v) => onChange('waitTimeout', v)}
          defaultValue={10}
          min={1}
          max={60}
        />
        <p className="text-xs text-muted-foreground">
          等待文本出现的最长时间
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 使用提示
        </p>
        <p className="text-xs text-blue-800">
          • 使用 RapidOCR 进行文本识别，支持中文
        </p>
        <p className="text-xs text-blue-800">
          • 如果识别不准确，可以尝试使用"包含"模式或正则表达式
        </p>
      </div>
    </>
  )
}

// 等待图像配置
export function PhoneWaitImageConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="imagePath">图像文件路径</Label>
        <ImagePathInput
          value={(data.imagePath as string) || ''}
          onChange={(v) => onChange('imagePath', v)}
          placeholder="从图像资源中选择或输入路径"
        />
        <p className="text-xs text-muted-foreground">
          从图像资源中选择要等待的目标图片
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="confidence">匹配置信度</Label>
        <NumberInput
          id="confidence"
          value={(data.confidence as number) ?? 0.8}
          onChange={(v) => onChange('confidence', v)}
          defaultValue={0.8}
          min={0.1}
          max={1.0}
          step={0.05}
        />
        <p className="text-xs text-muted-foreground">
          图像匹配的相似度阈值（0.1-1.0）
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="waitTimeout">等待超时（秒）</Label>
        <NumberInput
          id="waitTimeout"
          value={(data.waitTimeout as number) ?? 30}
          onChange={(v) => onChange('waitTimeout', v)}
          defaultValue={30}
          min={1}
          max={300}
        />
        <p className="text-xs text-muted-foreground">
          等待图像出现的最长时间
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="checkInterval">检查间隔（秒）</Label>
        <NumberInput
          id="checkInterval"
          value={(data.checkInterval as number) ?? 0.5}
          onChange={(v) => onChange('checkInterval', v)}
          defaultValue={0.5}
          min={0.1}
          max={5}
          step={0.1}
        />
        <p className="text-xs text-muted-foreground">
          每次检查之间的等待时间
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="resultVariable">存储结果到变量</Label>
        <VariableNameInput
          value={(data.resultVariable as string) || ''}
          onChange={(v) => onChange('resultVariable', v)}
          placeholder="保存图像位置和匹配度"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">
          保存图像坐标、匹配度和耗时信息
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 使用提示
        </p>
        <p className="text-xs text-blue-800">
          • 此模块会持续检查手机屏幕，直到图像出现或超时
        </p>
        <p className="text-xs text-blue-800">
          • 适用于等待加载完成、等待按钮出现等场景
        </p>
        <p className="text-xs text-blue-800">
          • 检查间隔越小越灵敏，但会消耗更多资源
        </p>
      </div>
    </>
  )
}

// 设置音量配置
export function PhoneSetVolumeConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="streamType">音频类型</Label>
        <Select
          id="streamType"
          value={(data.streamType as string) || 'music'}
          onChange={(e) => onChange('streamType', e.target.value)}
        >
          <option value="music">媒体音量</option>
          <option value="ring">铃声音量</option>
          <option value="alarm">闹钟音量</option>
          <option value="notification">通知音量</option>
          <option value="system">系统音量</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          选择要调整的音频流类型
        </p>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="volume">音量值（0-15）</Label>
        <NumberInput
          id="volume"
          value={(data.volume as number) ?? 10}
          onChange={(v) => onChange('volume', v)}
          defaultValue={10}
          min={0}
          max={15}
        />
        <p className="text-xs text-muted-foreground">
          0 = 静音，15 = 最大音量
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 使用提示
        </p>
        <p className="text-xs text-blue-800">
          • 媒体音量：影响音乐、视频等媒体播放
        </p>
        <p className="text-xs text-blue-800">
          • 铃声音量：影响来电铃声
        </p>
        <p className="text-xs text-blue-800">
          • 闹钟音量：影响闹钟提醒
        </p>
        <p className="text-xs text-blue-800">
          • 通知音量：影响应用通知声音
        </p>
      </div>
    </>
  )
}

// 设置亮度配置
export function PhoneSetBrightnessConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const brightness = (data.brightness as number) ?? 128
  const percentage = Math.round((brightness / 255) * 100)
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="brightness">亮度值（0-255）</Label>
        <NumberInput
          id="brightness"
          value={brightness}
          onChange={(v) => onChange('brightness', v)}
          defaultValue={128}
          min={0}
          max={255}
        />
        <p className="text-xs text-muted-foreground">
          当前设置: {brightness}/255 ({percentage}%)
        </p>
      </div>
      
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-amber-900">
          ⚠️ 注意事项
        </p>
        <p className="text-xs text-amber-800">
          • 此操作会自动关闭手机的自动亮度功能
        </p>
        <p className="text-xs text-amber-800">
          • 0 = 最暗，255 = 最亮
        </p>
        <p className="text-xs text-amber-800">
          • 建议值：50-200 之间
        </p>
      </div>
      
      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
        <p className="text-xs font-semibold text-blue-900">
          💡 常用亮度值
        </p>
        <p className="text-xs text-blue-800">
          • 最暗：0-50
        </p>
        <p className="text-xs text-blue-800">
          • 较暗：51-100
        </p>
        <p className="text-xs text-blue-800">
          • 中等：101-150
        </p>
        <p className="text-xs text-blue-800">
          • 较亮：151-200
        </p>
        <p className="text-xs text-blue-800">
          • 最亮：201-255
        </p>
      </div>
    </>
  )
}
