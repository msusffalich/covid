import type { Language } from '../types'

interface Props {
  value: Language
  onChange: (lang: Language) => void
  disabled?: boolean
}

export default function LanguageSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-brand-700">
        {value === 'es' ? 'Idioma del informe' : 'Report language'}
      </span>
      <div className="flex rounded-lg overflow-hidden border border-brand-200 shadow-sm">
        {(['es', 'en'] as Language[]).map((lang) => (
          <button
            key={lang}
            onClick={() => onChange(lang)}
            disabled={disabled}
            className={[
              'px-4 py-1.5 text-sm font-semibold transition-all duration-200',
              value === lang
                ? 'bg-brand-700 text-white'
                : 'bg-white text-brand-700 hover:bg-brand-50',
              disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
            ].join(' ')}
          >
            {lang === 'es' ? '🇪🇸 Español' : '🇬🇧 English'}
          </button>
        ))}
      </div>
    </div>
  )
}
