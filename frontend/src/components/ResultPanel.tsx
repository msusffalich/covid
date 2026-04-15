/**
 * ResultPanel
 * Phase 4 — shows research summary + sources, then download
 */

import ReactMarkdown from 'react-markdown'
import type { Language, ResearchResult, Source } from '../types'
import { UI_STRINGS } from '../types'

interface SummaryProps {
  result: ResearchResult
  language: Language
}

export function SummaryCard({ result, language }: SummaryProps) {
  const t = UI_STRINGS[language]

  return (
    <div className="space-y-4 animate-slide-in">
      {/* Summary */}
      <div className="bg-brand-50 border border-brand-200 rounded-xl p-4">
        <h4 className="text-sm font-bold text-brand-700 mb-2 uppercase tracking-wide">
          {t.summaryTitle}
        </h4>
        <div className="prose prose-sm max-w-none text-gray-700">
          <ReactMarkdown>{result.summary}</ReactMarkdown>
        </div>
      </div>

      {/* Sources */}
      {result.sources.length > 0 && (
        <div>
          <h4 className="text-sm font-bold text-brand-700 mb-2 uppercase tracking-wide">
            {t.sourcesTitle} — {t.sourcesCount(result.sources.length)}
          </h4>
          <ul className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {result.sources.map((src, i) => (
              <SourceItem key={i} source={src} index={i + 1} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function SourceItem({ source, index }: { source: Source; index: number }) {
  return (
    <li className="bg-white border border-brand-100 rounded-lg p-3 text-xs space-y-1 shadow-sm">
      <div className="flex gap-2 items-start">
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-brand-600
                         text-white text-xs font-bold flex-shrink-0 mt-0.5">
          {index}
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-brand-800 truncate">{source.title || 'Source'}</p>
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-500 hover:underline truncate block"
            >
              {source.url}
            </a>
          )}
          {source.snippet && (
            <p className="text-gray-500 mt-1 line-clamp-2">{source.snippet}</p>
          )}
          {source.citation_apa && (
            <p className="text-gray-400 italic mt-1">{source.citation_apa}</p>
          )}
        </div>
      </div>
    </li>
  )
}

// ---------------------------------------------------------------------------

interface DownloadProps {
  downloadUrl: string
  language: Language
  onReset: () => void
}

export function DownloadPanel({ downloadUrl, language, onReset }: DownloadProps) {
  const t = UI_STRINGS[language]
  const fullUrl = `${window.location.origin}${downloadUrl}`

  return (
    <div className="text-center space-y-4 animate-slide-in">
      <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center text-3xl">
        ✅
      </div>
      <h3 className="font-bold text-brand-800 text-lg">
        {language === 'es' ? '¡Tu documento está listo!' : 'Your document is ready!'}
      </h3>
      <a
        href={fullUrl}
        download
        className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-brand-700 text-white
                   font-bold text-base hover:bg-brand-800 active:scale-[0.98] transition-all shadow-md"
      >
        ⬇️ {t.downloadButton}
      </a>
      <div>
        <button
          onClick={onReset}
          className="text-sm text-brand-500 hover:underline mt-2"
        >
          {t.newResearch}
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

interface ErrorProps {
  message: string
  language: Language
  onReset: () => void
}

export function ErrorPanel({ message, language, onReset }: ErrorProps) {
  const t = UI_STRINGS[language]

  return (
    <div className="text-center space-y-4 animate-slide-in">
      <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center text-3xl">
        ⚠️
      </div>
      <h3 className="font-bold text-red-700 text-lg">{t.errorTitle}</h3>
      <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3 text-left">{message}</p>
      <button
        onClick={onReset}
        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-brand-700 text-white
                   font-semibold text-sm hover:bg-brand-800 transition-all"
      >
        🔄 {t.retry}
      </button>
    </div>
  )
}
