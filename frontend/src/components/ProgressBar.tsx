interface Props {
  step: number
  total: number
  detail: string
  statusMessage?: string
}

export default function ProgressBar({ step, total, detail, statusMessage }: Props) {
  const pct = total > 0 ? Math.round((step / total) * 100) : 0

  return (
    <div className="w-full animate-slide-in">
      {statusMessage && (
        <p className="text-sm text-brand-600 mb-2 font-medium">{statusMessage}</p>
      )}
      <div className="w-full bg-brand-100 rounded-full h-3 overflow-hidden">
        <div
          className="h-3 rounded-full bg-gradient-to-r from-brand-500 to-brand-700 transition-all duration-500 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between mt-1.5">
        <p className="text-xs text-brand-600">{detail}</p>
        <p className="text-xs text-brand-400 font-mono">
          {step}/{total} — {pct}%
        </p>
      </div>
    </div>
  )
}
