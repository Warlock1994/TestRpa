import type React from 'react'
import type { NodeData } from '@/store/workflowStore'
import { Label } from '@/components/ui/label'
import { NumberInput } from '@/components/ui/number-input'
import { SelectNative as Select } from '@/components/ui/select-native'
import { VariableInput } from '@/components/ui/variable-input'
import { VariableNameInput } from '@/components/ui/variable-name-input'
import { VariableRefInput } from '@/components/ui/variable-ref-input'

type RenderSelectorInput = (id: string, label: string, placeholder: string) => React.ReactNode

export function ConditionConfig({ 
  data, 
  onChange, 
  renderSelectorInput 
}: { 
  data: NodeData
  onChange: (key: string, value: unknown) => void
  renderSelectorInput: RenderSelectorInput
}) {
  const conditionType = (data.conditionType as string) || 'variable'
  const isElementCondition = conditionType === 'element_exists' || conditionType === 'element_visible'
  const isBooleanCondition = conditionType === 'boolean'
  const isLogicCondition = conditionType === 'logic'
  const operator = (data.operator as string) || '=='
  const isUnaryOperator = operator === 'isEmpty' || operator === 'isNotEmpty'
  const logicOperator = (data.logicOperator as string) || 'and'

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="conditionType">条件类型</Label>
        <Select
          id="conditionType"
          value={conditionType}
          onChange={(e) => onChange('conditionType', e.target.value)}
        >
          <option value="variable">变量比较</option>
          <option value="boolean">布尔值</option>
          <option value="logic">逻辑运算</option>
          <option value="element_exists">元素存在</option>
          <option value="element_visible">元素可见</option>
        </Select>
      </div>
      {isLogicCondition ? (
        <>
          <div className="space-y-2">
            <Label htmlFor="logicOperator">逻辑运算符</Label>
            <Select
              id="logicOperator"
              value={logicOperator}
              onChange={(e) => onChange('logicOperator', e.target.value)}
            >
              <option value="and">与（AND）</option>
              <option value="or">或（OR）</option>
              <option value="not">非（NOT）</option>
            </Select>
          </div>
          {logicOperator === 'not' ? (
            <div className="space-y-2">
              <Label htmlFor="condition">条件</Label>
              <VariableInput
                value={(data.condition as string) || ''}
                onChange={(v) => onChange('condition', v)}
                placeholder="输入条件表达式"
              />
              <p className="text-xs text-muted-foreground">
                对条件取反，例如：{'{a} > 5'} 变为 {'{a} <= 5'}
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="condition1">条件1</Label>
                <VariableInput
                  value={(data.condition1 as string) || ''}
                  onChange={(v) => onChange('condition1', v)}
                  placeholder="输入第一个条件"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="condition2">条件2</Label>
                <VariableInput
                  value={(data.condition2 as string) || ''}
                  onChange={(v) => onChange('condition2', v)}
                  placeholder="输入第二个条件"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {logicOperator === 'and' 
                  ? '两个条件都为真时，结果为真'
                  : '任一条件为真时，结果为真'}
              </p>
            </>
          )}
        </>
      ) : isElementCondition ? (
        renderSelectorInput('leftOperand', '元素选择器', '输入CSS选择器')
      ) : isBooleanCondition ? (
        <>
          <div className="space-y-2">
            <Label htmlFor="leftOperand">布尔变量</Label>
            <VariableInput
              value={(data.leftOperand as string) || ''}
              onChange={(v) => onChange('leftOperand', v)}
              placeholder="输入布尔变量，如 {is_success}"
            />
            <p className="text-xs text-muted-foreground">
              判断变量是否为 true
            </p>
          </div>
        </>
      ) : (
        <>
          <div className="space-y-2">
            <Label htmlFor="leftOperand">左操作数</Label>
            <VariableInput
              value={(data.leftOperand as string) || ''}
              onChange={(v) => onChange('leftOperand', v)}
              placeholder="输入变量或值，如 {count}"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="operator">比较运算符</Label>
            <Select
              id="operator"
              value={operator}
              onChange={(e) => onChange('operator', e.target.value)}
            >
              <option value="==">等于（==）</option>
              <option value="!=">不等于（!=）</option>
              <option value=">">大于（&gt;）</option>
              <option value="<">小于（&lt;）</option>
              <option value="contains">包含</option>
              <option value="isEmpty">为空</option>
              <option value="isNotEmpty">不为空</option>
            </Select>
          </div>
          {!isUnaryOperator && (
            <div className="space-y-2">
              <Label htmlFor="rightOperand">右操作数</Label>
              <VariableInput
                value={(data.rightOperand as string) || ''}
                onChange={(v) => onChange('rightOperand', v)}
                placeholder="输入变量或值，如 10"
              />
            </div>
          )}
        </>
      )}
    </>
  )
}

// 循环执行配置
export function LoopConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  const loopType = (data.loopType as string) || 'count'
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="loopType">循环类型</Label>
        <Select
          id="loopType"
          value={loopType}
          onChange={(e) => onChange('loopType', e.target.value)}
        >
          <option value="count">固定次数</option>
          <option value="range">范围循环</option>
          <option value="while">条件循环</option>
        </Select>
      </div>
      
      {loopType === 'count' && (
        <div className="space-y-2">
          <Label htmlFor="count">循环次数</Label>
          <VariableInput
            value={String(data.count ?? '')}
            onChange={(v) => {
              // 如果是空字符串或只包含变量引用，直接保存字符串
              if (v === '' || v.includes('{')) {
                onChange('count', v)
              } else {
                // 尝试解析为数字
                const num = parseInt(v)
                onChange('count', isNaN(num) ? v : num)
              }
            }}
            placeholder="输入循环次数，如 10 或 {count}"
          />
        </div>
      )}
      
      {loopType === 'range' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="startValue">起始值</Label>
            <VariableInput
              value={String(data.startValue ?? '')}
              onChange={(v) => {
                if (v === '' || v.includes('{')) {
                  onChange('startValue', v)
                } else {
                  const num = parseInt(v)
                  onChange('startValue', isNaN(num) ? v : num)
                }
              }}
              placeholder="输入起始值，如 1"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="endValue">结束值</Label>
            <VariableInput
              value={String(data.endValue ?? '')}
              onChange={(v) => {
                if (v === '' || v.includes('{')) {
                  onChange('endValue', v)
                } else {
                  const num = parseInt(v)
                  onChange('endValue', isNaN(num) ? v : num)
                }
              }}
              placeholder="输入结束值，如 10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="stepValue">步长</Label>
            <NumberInput
              id="stepValue"
              value={(data.stepValue as number) ?? 1}
              onChange={(v) => onChange('stepValue', v)}
              defaultValue={1}
            />
            <p className="text-xs text-muted-foreground">
              每次循环增加的值，默认为 1
            </p>
          </div>
        </>
      )}
      
      {loopType === 'while' && (
        <div className="space-y-2">
          <Label htmlFor="condition">循环条件</Label>
          <VariableRefInput
            id="condition"
            value={(data.condition as string) || ''}
            onChange={(v) => onChange('condition', v)}
            placeholder="输入条件，如 {count} < 10"
          />
          <p className="text-xs text-muted-foreground">
            当条件为真时继续循环
          </p>
        </div>
      )}
      
      <div className="space-y-2">
        <Label htmlFor="indexVariable">索引变量名</Label>
        <VariableNameInput
          id="indexVariable"
          value={(data.indexVariable as string) || ''}
          onChange={(v) => onChange('indexVariable', v)}
          placeholder="输入变量名，如 i"
          isStorageVariable={true}
        />
        <p className="text-xs text-muted-foreground">
          {loopType === 'range' 
            ? `当前循环的值（从 ${(data.startValue as number) ?? 1} 到 ${(data.endValue as number) ?? 10}）`
            : '当前循环的索引（从 0 开始）'}
        </p>
      </div>
    </>
  )
}

// 遍历列表配置
export function ForeachConfig({ data, onChange }: { data: NodeData; onChange: (key: string, value: unknown) => void }) {
  
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="dataSource">数据源</Label>
        <VariableRefInput
          id="dataSource"
          value={(data.dataSource as string) || ''}
          onChange={(v) => onChange('dataSource', v)}
          placeholder="输入列表变量，如 {my_list}"
        />
        <p className="text-xs text-muted-foreground">
          要遍历的列表或数组
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="itemVariable">元素变量名</Label>
        <VariableNameInput
          id="itemVariable"
          value={(data.itemVariable as string) || ''}
          onChange={(v) => onChange('itemVariable', v)}
          placeholder="输入变量名，如 item"
          isStorageVariable={true}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="indexVariable">索引变量名</Label>
        <VariableNameInput
          id="indexVariable"
          value={(data.indexVariable as string) || ''}
          onChange={(v) => onChange('indexVariable', v)}
          placeholder="输入变量名，如 index"
          isStorageVariable={true}
        />
      </div>
    </>
  )
}

// 定时执行配置
export function ScheduledTaskConfig({
  data,
  onChange,
}: {
  data: NodeData
  onChange: (key: string, value: unknown) => void
}) {
  const scheduleType = (data.scheduleType as string) || 'datetime'

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="scheduleType">定时类型</Label>
        <Select
          id="scheduleType"
          value={scheduleType}
          onChange={(e) => onChange('scheduleType', e.target.value)}
        >
          <option value="datetime">指定时间</option>
          <option value="delay">延迟执行</option>
        </Select>
      </div>

      {scheduleType === 'datetime' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="targetDate">目标日期</Label>
            <VariableInput
              value={(data.targetDate as string) || ''}
              onChange={(v) => onChange('targetDate', v)}
              placeholder="2024-12-31"
            />
            <p className="text-xs text-muted-foreground">
              格式：YYYY-MM-DD，如 2024-12-31
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="targetTime">目标时间</Label>
            <VariableInput
              value={(data.targetTime as string) || ''}
              onChange={(v) => onChange('targetTime', v)}
              placeholder="14:30:00"
            />
            <p className="text-xs text-muted-foreground">
              格式：HH:MM:SS，如 14:30:00
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            在指定的日期和时间执行后续模块
          </p>
        </>
      )}

      {scheduleType === 'delay' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="delayHours">延迟小时数</Label>
            <NumberInput
              id="delayHours"
              value={(data.delayHours as number) ?? 0}
              onChange={(v) => onChange('delayHours', v)}
              defaultValue={0}
              min={0}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="delayMinutes">延迟分钟数</Label>
            <NumberInput
              id="delayMinutes"
              value={(data.delayMinutes as number) ?? 0}
              onChange={(v) => onChange('delayMinutes', v)}
              defaultValue={0}
              min={0}
              max={59}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="delaySeconds">延迟秒数</Label>
            <NumberInput
              id="delaySeconds"
              value={(data.delaySeconds as number) ?? 0}
              onChange={(v) => onChange('delaySeconds', v)}
              defaultValue={0}
              min={0}
              max={59}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            延迟指定时间后执行后续模块
          </p>
        </>
      )}

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mt-4">
        <p className="text-xs text-blue-800">
          <strong>💡 使用说明</strong><br />
          • 定时执行会暂停工作流，直到指定时间到达<br />
          • 可用于定时任务、延迟操作等场景<br />
          • 支持变量引用，如 {'{target_time}'}
        </p>
      </div>
    </>
  )
}


// 子流程配置 - 从画布中选择子流程分组
import { useWorkflowStore } from '@/store/workflowStore'
import { Workflow, AlertCircle } from 'lucide-react'

export function SubflowConfig({
  data,
  onChange,
}: {
  data: NodeData
  onChange: (key: string, value: unknown) => void
}) {
  // 获取画布中所有的子流程分组和子流程头
  const nodes = useWorkflowStore((state) => state.nodes)
  const subflowGroups = nodes.filter(
    (n) => (n.type === 'groupNode' && n.data.isSubflow === true && n.data.subflowName) ||
           (n.type === 'subflowHeaderNode' && n.data.subflowName)
  )

  // 使用 subflowName 作为主要标识（而不是 ID，因为导入后 ID 会变）
  const selectedName = (data.subflowName as string) || ''
  const selectedGroup = subflowGroups.find((g) => g.data.subflowName === selectedName)

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="subflowName">子流程名称</Label>
        <Select
          id="subflowName"
          value={selectedName}
          onChange={(e) => {
            onChange('subflowName', e.target.value)
            // 同时保存 ID 用于当前会话的快速查找（但导入后会失效）
            const group = subflowGroups.find((g) => g.data.subflowName === e.target.value)
            onChange('subflowGroupId', group?.id || '')
          }}
        >
          <option value="">请选择子流程</option>
          {subflowGroups.map((group) => (
            <option key={group.id} value={group.data.subflowName as string}>
              📦 {(group.data.subflowName as string) || '未命名子流程'}
            </option>
          ))}
        </Select>
        {subflowGroups.length === 0 && (
          <p className="text-xs text-amber-600 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            画布中没有可用的子流程，请先创建子流程分组
          </p>
        )}
      </div>

      {selectedGroup && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
          <div className="flex items-center gap-2 text-emerald-800">
            <Workflow className="w-4 h-4" />
            <span className="text-sm font-medium">
              {(selectedGroup.data.subflowName as string) || '未命名子流程'}
            </span>
          </div>
          <p className="text-xs text-emerald-600 mt-1">
            将执行此子流程中的所有模块
          </p>
        </div>
      )}

      {!selectedGroup && selectedName && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-xs text-red-600 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            找不到名为 "{selectedName}" 的子流程
          </p>
        </div>
      )}

      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg mt-4">
        <p className="text-xs text-blue-800 leading-relaxed">
          <strong>💡 变量作用域</strong><br />
          • <strong>全局变量</strong>：子流程可以读取和修改<br />
          • <strong>局部变量</strong>：子流程内创建的变量仅在子流程内有效<br />
          • <strong>返回值</strong>：子流程执行完毕后，全局变量的修改会保留<br />
          • <strong>嵌套调用</strong>：子流程可以调用其他子流程<br />
          • <strong>递归调用</strong>：子流程可以调用自己（注意设置退出条件）
        </p>
      </div>

      <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-xs text-amber-800 leading-relaxed">
          <strong>📦 创建子流程</strong><br />
          1. 在画布中添加"分组"模块<br />
          2. 将需要复用的模块拖入分组内<br />
          3. 在分组配置中开启"作为子流程"<br />
          4. 设置子流程名称<br />
          5. 在其他地方使用"子流程"模块调用
        </p>
      </div>

      <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
        <p className="text-xs text-purple-800 leading-relaxed">
          <strong>🎯 使用场景</strong><br />
          • <strong>代码复用</strong>：将重复的操作封装成子流程<br />
          • <strong>模块化</strong>：将复杂流程拆分成多个子流程<br />
          • <strong>条件执行</strong>：根据条件选择执行不同的子流程<br />
          • <strong>循环调用</strong>：在循环中调用子流程处理每个元素
        </p>
      </div>
    </>
  )
}
