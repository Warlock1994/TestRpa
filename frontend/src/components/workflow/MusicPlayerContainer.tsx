import { useState, useEffect } from 'react'
import { MusicPlayerDialog, setMusicPlayerCallback } from './MusicPlayerDialog'

interface MusicPlayerProps {
  audioUrl: string
  requestId: string
  waitForEnd: boolean
  onClose: (success: boolean, error?: string) => void
}

export function MusicPlayerContainer() {
  const [playerProps, setPlayerProps] = useState<MusicPlayerProps | null>(null)

  useEffect(() => {
    // 注册回调
    setMusicPlayerCallback((props) => {
      setPlayerProps(props)
    })

    return () => {
      setMusicPlayerCallback(() => {})
    }
  }, [])

  if (!playerProps) return null

  return <MusicPlayerDialog {...playerProps} />
}
