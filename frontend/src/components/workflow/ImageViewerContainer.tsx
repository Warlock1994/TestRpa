import { useState, useEffect } from 'react'
import { ImageViewerDialog, setImageViewerCallback } from './ImageViewerDialog'

interface ImageViewerProps {
  imageUrl: string
  requestId: string
  autoClose: boolean
  displayTime: number
  onClose: (success: boolean, error?: string) => void
}

export function ImageViewerContainer() {
  const [viewerProps, setViewerProps] = useState<ImageViewerProps | null>(null)

  useEffect(() => {
    setImageViewerCallback((props) => {
      setViewerProps(props)
    })

    return () => {
      setImageViewerCallback(() => {})
    }
  }, [])

  if (!viewerProps) return null

  return <ImageViewerDialog {...viewerProps} />
}
