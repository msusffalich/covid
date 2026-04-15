/**
 * ResearchPanel
 * Phase 1 — topic input + research kickoff
 */

import { type FormEvent, useState } from 'react'
import type { Language } from '../types'
import { UI_STRINGS } from '../types'
import LanguageSelector from './LanguageSelector'

interface Props {
  language: Language
  onLanguageChange: (l: Language) => void
  onSubmit: (topic: string) => void
  loading?: boolean
}

export default function ResearchPanel({ language, onLanguageChange, onSubmit, loading }: Props) {
  const [topic, setTopic] = useState('')
  const t = UI_STRINGS[language]

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = topic.trim()
    if (trimmed.length >= 3) onSubmit(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 animate-slide-in">
      {/* Language selector */}
      <LanguageSelector value={language} onChange={onLanguageChange} disabled={loading} />

      {/* Topic input */}
      <div className="space-y-2">
        <label htmlFor="topic" className="block text-sm font-semibold text-brand-800">
          {t.topicLabel}
        </label>
        <textarea
          id="topic"
          rows={3}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder={t.topicPlaceholder}
          disabled={loading}
          maxLength={500}
          className="w-full rounded-xl border border-brand-200 px-4 py-3 text-sm text-gray-800
                     focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent
                     resize-none placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-sm transition"
        />
        <p className="text-xs text-gray-400">
          {t.topicHint} {topic.length}/500
        </p>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading || topic.trim().length < 3}
        className="w-full py-3 rounded-xl bg-brand-700 text-white font-bold text-base
                   hover:bg-brand-800 active:scale-[0.98] transition-all shadow-md
                   disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full inline-block" />
            {t.researching}
          </>
        ) : (
          <>
            <span>🔍</span> {t.startButton}
          </>
        )}
      </button>
    </form>
  )
}
