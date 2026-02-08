import { ScheduledTasksPage } from './ScheduledTasksPage'

interface ScheduledTasksDialogProps {
  open: boolean
  onClose: () => void
}

export function ScheduledTasksDialog({ open, onClose }: ScheduledTasksDialogProps) {
  if (!open) return null
  
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4 animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-[1400px] max-h-[90vh] flex flex-col overflow-hidden animate-scale-in" onClick={(e) => e.stopPropagation()}>
        <ScheduledTasksPage onClose={onClose} />
      </div>
    </div>
  )
}
