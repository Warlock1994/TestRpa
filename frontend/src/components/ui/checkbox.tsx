import * as React from 'react'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

export interface CheckboxProps {
  id?: string
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ id, checked = false, onCheckedChange, disabled, className }, ref) => {
    const handleClick = () => {
      if (!disabled && onCheckedChange) {
        onCheckedChange(!checked)
      }
    }

    return (
      <button
        type="button"
        role="checkbox"
        aria-checked={checked}
        id={id}
        ref={ref as React.Ref<HTMLButtonElement>}
        disabled={disabled}
        onClick={handleClick}
        className={cn(
          'h-4 w-4 shrink-0 rounded-sm border-2 shadow-sm transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50',
          'disabled:cursor-not-allowed disabled:opacity-50',
          checked 
            ? 'bg-blue-600 border-blue-600' 
            : 'bg-white border-gray-300 hover:border-blue-400',
          'flex items-center justify-center cursor-pointer',
          className
        )}
      >
        {checked && <Check className="h-3 w-3 text-white" strokeWidth={3} />}
      </button>
    )
  }
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }
