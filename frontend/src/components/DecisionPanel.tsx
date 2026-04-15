/**
 * DecisionPanel
 * Phase 3 — user picks output format and optional instructions
 */

import { useState } from 'react'
import type { Language, OutputFormat } from '../types'
import { FORMAT_LABELS, UI_STRINGS } from '../types'

interface Props {
  language: Language
  onSubmit: (format: OutputFormat, extra: string) => void
  loading?: boolean
}

export default function DecisionPanel({ language, onSubmit, loading }: Props) {
  const [selected, setSelected] = useState<OutputFormat | null>(null)
  const [extra, setExtra] = useState('')
  const t = UI_STRINGS[language]

  const formats: OutputFormat[] = ['pdf', 'pptx', 'excel', 'image']

  return (
    <div className="space-y-6 animate-slide-in">
      <h3 className="text-lg font-bold text-brand-800">{t.chooseFormat}</h3>

      {/* Format cards */}
      <div className="grid grid-cols-2 gap-3">
        {formats.map((fmt) => {
          const info = FORMAT_LABELS[fmt]
          const label = info[language]
          const active = selected === fmt
          return (
            <button
              key={fmt}
              onClick={() => setSelected(fmt)}
              disabled={loading}
              className={[
                'flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all',
                'font-semibold text-sm cursor-pointer disabled:opacity-50',
                active
                  ? 'border-brand-600 bg-brand-50 text-brand-800 shadow-md scale-[1.02]'
                  : 'border-brand-100 bg-white text-brand-700 hover:border-brand-300 hover:bg-brand-50',
              ].join(' ')}
            >
              <span className="text-3xl">{info.icon}</span>
              {label}
            </button>
          )
        })}
      </div>

      {/* Extra instructions */}
      <div className="space-y-1">
        <label className="block text-sm font-medium text-brand-700">{t.extraLabel}</label>
        <textarea
          rows={2}
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          placeholder={t.extraPlaceholder}
          disabled={loading}
          maxLength={1000}
          className="w-full rounded-xl border border-brand-200 px-4 py-2.5 text-sm text-gray-800
                     focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent
                     resize-none placeholder-gray-400 disabled:opacity-50 shadow-sm transition"
        />
      </div>

      {/* Generate button */}
      <button
        onClick={() => selected && onSubmit(selected, extra)}
        disabled={!selected || loading}
        className="w-full py-3 rounded-xl bg-gold text-brand-900 font-bold text-base
                   hover:brightness-95 active:scale-[0.98] transition-all shadow-md
                   disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="animate-spin w-4 h-4 border-2 border-brand-900 border-t-transparent rounded-full inline-block" />
            {t.generating}
          </>
        ) : (
          <>
            <span>⚡</span> {t.generateButton}
          </>
        )}
      </button>
    </div>
  )
}
