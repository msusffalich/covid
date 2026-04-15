/**
 * App.tsx — Root component and state machine orchestrator
 * --------------------------------------------------------
 * State machine:
 *   idle  →[submit topic]→  researching
 *   researching →[SSE result]→ awaiting_format
 *   awaiting_format →[submit format]→ generating
 *   generating →[SSE done]→ done
 *   any →[error]→ error
 *   done | error →[reset]→ idle
 */

import { useCallback, useRef, useState } from 'react'
import type {
  AppPhase,
  AppState,
  Language,
  OutputFormat,
  ProgressEvent,
  ResearchResult,
} from './types'
import { UI_STRINGS } from './types'

import { useSSE } from './hooks/useSSE'
import { cleanupSession, extractErrorMessage, startGeneration, startSession } from './services/api'

import LanguageSelector from './components/LanguageSelector'
import ResearchPanel from './components/ResearchPanel'
import ProgressBar from './components/ProgressBar'
import DecisionPanel from './components/DecisionPanel'
import { DownloadPanel, ErrorPanel, SummaryCard } from './components/ResultPanel'

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const INITIAL_STATE: AppState = {
  phase: 'idle',
  language: 'es',
  topic: '',
  sessionId: null,
  progress: null,
  statusMessage: '',
  result: null,
  outputFormat: null,
  extraInstructions: '',
  downloadUrl: null,
  errorMessage: null,
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE)
  const sessionIdRef = useRef<string | null>(null)

  const set = useCallback((patch: Partial<AppState>) =>
    setState((prev) => ({ ...prev, ...patch })), [])

  const t = UI_STRINGS[state.language]

  // ---- SSE URL derivation --------------------------------------------------
  // Research SSE active only during 'researching' phase
  const researchSSEUrl =
    state.phase === 'researching' && state.sessionId
      ? `/api/research/stream/${state.sessionId}`
      : null

  // Generation SSE active only during 'generating' phase
  const generateSSEUrl =
    state.phase === 'generating' && state.sessionId
      ? `/api/generate/stream/${state.sessionId}`
      : null

  // ---- Research SSE handlers -----------------------------------------------
  useSSE({
    url: researchSSEUrl,
    handlers: {
      onStatus: (data) => {
        if (data.message === 'awaiting_format') return  // handled by onResult
        set({ statusMessage: data.message ?? '' })
      },
      onProgress: (data: ProgressEvent) => set({ progress: data }),
      onResult: (data) => {
        set({
          phase: 'awaiting_format',
          result: data as ResearchResult,
          statusMessage: t.researchDone,
        })
      },
      onError: (data) =>
        set({ phase: 'error', errorMessage: data.message }),
    },
  })

  // ---- Generation SSE handlers ---------------------------------------------
  useSSE({
    url: generateSSEUrl,
    handlers: {
      onStatus: (data) => set({ statusMessage: data.state ?? '' }),
      onDone: (data) =>
        set({ phase: 'done', downloadUrl: data.download_url }),
      onError: (data) =>
        set({ phase: 'error', errorMessage: data.message }),
    },
  })

  // ---- Actions -------------------------------------------------------------

  const handleTopicSubmit = useCallback(async (topic: string) => {
    try {
      set({ phase: 'researching', topic, progress: null, statusMessage: '' })
      const sessionId = await startSession(state.language, topic)
      sessionIdRef.current = sessionId
      set({ sessionId })
    } catch (err) {
      set({ phase: 'error', errorMessage: extractErrorMessage(err) })
    }
  }, [state.language, set])

  const handleFormatSubmit = useCallback(async (format: OutputFormat, extra: string) => {
    if (!state.sessionId) return
    try {
      set({ phase: 'generating', outputFormat: format, extraInstructions: extra, progress: null })
      await startGeneration(state.sessionId, format, extra)
    } catch (err) {
      set({ phase: 'error', errorMessage: extractErrorMessage(err) })
    }
  }, [state.sessionId, set])

  const handleReset = useCallback(async () => {
    if (sessionIdRef.current) {
      await cleanupSession(sessionIdRef.current)
      sessionIdRef.current = null
    }
    setState(INITIAL_STATE)
  }, [])

  // ---- Render helpers ------------------------------------------------------

  const phase: AppPhase = state.phase

  const isResearching = phase === 'researching'
  const isGenerating = phase === 'generating'

  // ---- UI ------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-brand-100 flex flex-col">
      {/* ---- Header ---- */}
      <header className="bg-brand-900 text-white shadow-lg">
        <div className="max-w-3xl mx-auto px-4 py-5 flex flex-col gap-1">
          <h1 className="text-2xl font-extrabold tracking-tight">{t.appTitle}</h1>
          <p className="text-brand-200 text-sm">{t.appSubtitle}</p>
        </div>
      </header>

      {/* ---- Main card ---- */}
      <main className="flex-1 flex items-start justify-center px-4 py-10">
        <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-8 space-y-8">

          {/* Phase 1 & 2: Input + research in progress */}
          {(phase === 'idle' || phase === 'researching') && (
            <>
              <ResearchPanel
                language={state.language}
                onLanguageChange={(l) => set({ language: l })}
                onSubmit={handleTopicSubmit}
                loading={isResearching}
              />
              {isResearching && state.progress && (
                <ProgressBar
                  step={state.progress.step}
                  total={state.progress.total}
                  detail={state.progress.detail}
                  statusMessage={state.statusMessage}
                />
              )}
              {isResearching && !state.progress && (
                <div className="flex items-center gap-3 text-brand-600">
                  <span className="animate-spin w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full inline-block" />
                  <span className="text-sm">{state.statusMessage || t.researching}</span>
                </div>
              )}
            </>
          )}

          {/* Phase 3: Show summary + format picker */}
          {phase === 'awaiting_format' && state.result && (
            <div className="space-y-6">
              {/* Language switcher stays visible but disabled */}
              <div className="flex items-center justify-between">
                <LanguageSelector
                  value={state.language}
                  onChange={() => {/* locked after research */}}
                  disabled
                />
                <span className="text-xs text-green-600 font-medium bg-green-50 px-3 py-1 rounded-full">
                  {t.researchDone}
                </span>
              </div>
              <SummaryCard result={state.result} language={state.language} />
              <hr className="border-brand-100" />
              <DecisionPanel
                language={state.language}
                onSubmit={handleFormatSubmit}
                loading={isGenerating}
              />
            </div>
          )}

          {/* Phase 4: Generating */}
          {phase === 'generating' && (
            <div className="space-y-6">
              <SummaryCard result={state.result!} language={state.language} />
              <div className="flex items-center gap-3 text-brand-600">
                <span className="animate-spin w-5 h-5 border-2 border-brand-600 border-t-transparent rounded-full inline-block" />
                <span className="text-sm font-medium">{t.generating}</span>
              </div>
            </div>
          )}

          {/* Phase 5: Done — download */}
          {phase === 'done' && state.downloadUrl && (
            <DownloadPanel
              downloadUrl={state.downloadUrl}
              language={state.language}
              onReset={handleReset}
            />
          )}

          {/* Error */}
          {phase === 'error' && (
            <ErrorPanel
              message={state.errorMessage ?? 'Unknown error'}
              language={state.language}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      {/* ---- Footer ---- */}
      <footer className="text-center py-4 text-xs text-brand-400">
        Investigador Inteligente Multimodal &mdash;{' '}
        {state.language === 'es'
          ? 'Información real, documentos profesionales.'
          : 'Real information, professional documents.'}
      </footer>
    </div>
  )
}
