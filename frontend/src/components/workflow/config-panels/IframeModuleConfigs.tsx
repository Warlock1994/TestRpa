import type { NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { SelectNative as Select } from '@/components/ui/select-native'
import { VariableInput } from '@/components/ui/variable-input'
import { NumberInput } from '@/components/ui/number-input'

// 切换到iframe配置
export function SwitchIframeConfig({ 
  data, 
  onChange 
}: { 
  data: NodeData
  onChange: (key: string, value: unknown) => void
}) {
  const locateBy = (data.locateBy as string) || 'index'
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="locateBy">定位方式</Label>
        <Select
          id="locateBy"
          value={locateBy}
          onChange={(e) => onChange('locateBy', e.target.value)}
        >
          <option value="index">索引</option>
          <option value="name">名称</option>
          <option value="selector">选择器</option>
        </Select>
        <p className="text-xs text-muted-foreground">
          {locateBy === 'index' && '通过iframe在页面中的索引位置定位（从0开始）'}
          {locateBy === 'name' && '通过iframe的name或id属性定位'}
          {locateBy === 'selector' && '通过CSS选择器定位iframe元素'}
        </p>
      </div>

      {locateBy === 'index' && (
        <div className="space-y-2">
          <Label htmlFor="iframeIndex">iframe索引</Label>
          <NumberInput
            id="iframeIndex"
            value={(data.iframeIndex as number) ?? 0}
            onChange={(v) => onChange('iframeIndex', v)}
            defaultValue={0}
            min={0}
          />
          <p className="text-xs text-muted-foreground">
            页面中第几个iframe（从0开始计数）
          </p>
        </div>
      )}

      {locateBy === 'name' && (
        <div className="space-y-2">
          <Label htmlFor="iframeName">iframe名称</Label>
          <VariableInput
            value={(data.iframeName as string) || ''}
            onChange={(v) => onChange('iframeName', v)}
            placeholder="iframe的name或id属性值"
          />
          <p className="text-xs text-muted-foreground">
            iframe元素的name或id属性值
          </p>
        </div>
      )}

      {locateBy === 'selector' && (
        <div className="space-y-2">
          <Label htmlFor="iframeSelector">iframe选择器</Label>
          <VariableInput
            value={(data.iframeSelector as string) || ''}
            onChange={(v) => onChange('iframeSelector', v)}
            placeholder="例如: iframe.content, #myframe"
          />
          <p className="text-xs text-muted-foreground">
            用于定位iframe的CSS选择器
          </p>
        </div>
      )}

      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-700">
          💡 切换到iframe后，后续的元素操作将在该iframe内执行，直到切换回主页面或切换到其他iframe
        </p>
      </div>
    </>
  )
}

// 切换回主页面配置
export function SwitchToMainConfig() {
  return (
    <div className="space-y-4">
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-xs text-blue-700">
          💡 此模块将操作上下文切换回主页面，后续的元素操作将在主页面执行
        </p>
      </div>
      <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
        <p className="text-xs text-amber-700">
          ⚠️ 如果当前不在iframe中，此操作不会产生任何效果
        </p>
      </div>
    </div>
  )
}
