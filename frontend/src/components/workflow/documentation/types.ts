import type { LucideIcon } from 'lucide-react'

export interface DocumentItem {
  id: string
  title: string
  icon: LucideIcon
  description: string
}

export interface DocumentationDialogProps {
  isOpen: boolean
  onClose: () => void
}
