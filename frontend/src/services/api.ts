/**
 * API service layer
 * -----------------
 * Wraps all backend calls. SSE streams are consumed via the useSSE hook;
 * this file handles REST calls only.
 */

import axios, { AxiosError } from 'axios'
import type { Language, OutputFormat } from '../types'

const BASE = '/api'

const http = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Retry helper: up to 3 attempts with exponential backoff
async function withRetry<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  let lastErr: unknown
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn()
    } catch (err) {
      lastErr = err
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, 2 ** i * 1000))
      }
    }
  }
  throw lastErr
}

// ---------------------------------------------------------------------------
// 1. Start session
// ---------------------------------------------------------------------------
export async function startSession(language: Language, topic: string): Promise<string> {
  return withRetry(async () => {
    const { data } = await http.post<{ session_id: string }>('/session/start', {
      language,
      topic,
    })
    return data.session_id
  })
}

// ---------------------------------------------------------------------------
// 2. Start generation (POST; returns 202)
// ---------------------------------------------------------------------------
export async function startGeneration(
  sessionId: string,
  outputFormat: OutputFormat,
  extraInstructions: string,
): Promise<void> {
  return withRetry(async () => {
    await http.post(`/generate/${sessionId}`, {
      output_format: outputFormat,
      extra_instructions: extraInstructions,
    })
  })
}

// ---------------------------------------------------------------------------
// 3. Cleanup session
// ---------------------------------------------------------------------------
export async function cleanupSession(sessionId: string): Promise<void> {
  try {
    await http.delete(`/session/${sessionId}`)
  } catch {
    // Best-effort cleanup; ignore errors
  }
}

// ---------------------------------------------------------------------------
// Error message extractor
// ---------------------------------------------------------------------------
export function extractErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    return err.response?.data?.detail ?? err.message
  }
  if (err instanceof Error) return err.message
  return String(err)
}
