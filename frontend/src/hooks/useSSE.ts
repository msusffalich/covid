/**
 * useSSE — Server-Sent Events hook
 * ----------------------------------
 * Connects to an SSE endpoint and calls typed event handlers.
 * Handles:
 *   - automatic reconnection on network errors (up to maxRetries)
 *   - cleanup on unmount
 *   - heartbeat detection (backend sends comments to keep connection alive)
 */

import { useCallback, useEffect, useRef } from 'react'

export interface SSEHandlers {
  onStatus?: (data: { message?: string; state?: string }) => void
  onProgress?: (data: { step: number; total: number; detail: string }) => void
  onResult?: (data: { summary: string; sources: unknown[] }) => void
  onDone?: (data: { download_url: string }) => void
  onError?: (data: { message: string }) => void
}

interface UseSSEOptions {
  url: string | null          // null = don't connect
  handlers: SSEHandlers
  maxRetries?: number
}

export function useSSE({ url, handlers, maxRetries = 5 }: UseSSEOptions) {
  const esRef = useRef<EventSource | null>(null)
  const retriesRef = useRef(0)
  const handlersRef = useRef(handlers)

  // Keep handlers ref up to date without re-triggering the effect
  useEffect(() => {
    handlersRef.current = handlers
  })

  const connect = useCallback(() => {
    if (!url) return

    const es = new EventSource(url)
    esRef.current = es

    const dispatch = (event: string, raw: string) => {
      try {
        const data = JSON.parse(raw)
        const h = handlersRef.current
        if (event === 'status'    && h.onStatus)   h.onStatus(data)
        if (event === 'progress'  && h.onProgress) h.onProgress(data)
        if (event === 'result'    && h.onResult)   h.onResult(data)
        if (event === 'done'      && h.onDone)     h.onDone(data)
        if (event === 'error'     && h.onError)    h.onError(data)
      } catch {
        // Malformed JSON from server — ignore silently
      }
    }

    // sse-starlette sends typed events
    for (const evtName of ['status', 'progress', 'result', 'done', 'error'] as const) {
      es.addEventListener(evtName, (e: MessageEvent) => dispatch(evtName, e.data))
    }

    es.onerror = () => {
      es.close()
      esRef.current = null
      if (retriesRef.current < maxRetries) {
        const delay = Math.min(2 ** retriesRef.current * 1000, 30_000)
        retriesRef.current += 1
        setTimeout(connect, delay)
      } else {
        handlersRef.current.onError?.({ message: 'Connection lost after max retries.' })
      }
    }

    es.onopen = () => {
      retriesRef.current = 0   // reset on successful open
    }
  }, [url, maxRetries])

  useEffect(() => {
    connect()
    return () => {
      esRef.current?.close()
      esRef.current = null
    }
  }, [connect])

  const close = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
  }, [])

  return { close }
}
