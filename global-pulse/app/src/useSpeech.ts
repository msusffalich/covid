import { useCallback, useEffect, useRef, useState } from 'react'
import type { Lang } from './types'

/** Multimodalidad de salida: lectura del pulso con Web Speech API (sin servicios externos). */
export function useSpeech(lang: Lang) {
  const [speaking, setSpeaking] = useState(false)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const queue = useRef<SpeechSynthesisUtterance | null>(null)

  const stop = useCallback(() => {
    if (!supported) return
    window.speechSynthesis.cancel()
    setSpeaking(false)
  }, [supported])

  const speak = useCallback((text: string) => {
    if (!supported || !text) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang === 'es' ? 'es-ES' : 'en-US'
    u.rate = 1.0
    u.onend = () => setSpeaking(false)
    u.onerror = () => setSpeaking(false)
    queue.current = u
    setSpeaking(true)
    window.speechSynthesis.speak(u)
  }, [lang, supported])

  useEffect(() => stop, [stop])
  return { speak, stop, speaking, supported }
}
