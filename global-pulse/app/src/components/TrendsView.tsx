import { useEffect, useState } from 'react'
import { useLang } from '../i18n'
import type { Trends, TrendTheme } from '../types'

function Sparkline({ theme }: { theme: TrendTheme }) {
  const pts = theme.serie
  if (pts.length < 2) return null
  const W = 240, H = 44, pad = 3
  const xs = (i: number) => pad + (i / (pts.length - 1)) * (W - 2 * pad)
  const ys = (v: number) => H - pad - (v / 100) * (H - 2 * pad)
  const line = pts.map((p, i) => `${xs(i)},${ys(p.max)}`).join(' ')
  const area = `${pad},${H - pad} ${line} ${W - pad},${H - pad}`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="sparkline" preserveAspectRatio="none"
         role="img" aria-label="Serie de impacto por día">
      <polygon points={area} fill={theme.color} opacity={0.15} />
      <polyline points={line} fill="none" stroke={theme.color} strokeWidth={2} />
      {pts.map((p, i) => (
        <circle key={i} cx={xs(i)} cy={ys(p.max)} r={1.6} fill={theme.color} />
      ))}
    </svg>
  )
}

export default function TrendsView() {
  const { lang, t } = useLang()
  const [data, setData] = useState<Trends | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('./data/trends-latest.json', { cache: 'reload' })
      .then((r) => r.json()).then(setData).catch(() => setError(true))
  }, [])

  if (error) return <p className="trends-empty">—</p>
  if (!data) return <div className="center"><span className="pulse-dot big" /></div>

  return (
    <section className="trends">
      <p className="trends-meta">
        {t.trendsWindow}: {data.meta.ventana_dias} {t.trendsDays} ·{' '}
        {t.trendsUpdated}: {new Date(data.meta.generado).toLocaleDateString(
          lang === 'es' ? 'es' : 'en-US',
          { day: 'numeric', month: 'short', year: 'numeric' })} · {data.meta.motor}
      </p>
      <div className="trend-grid">
        {data.temas.map((th) => (
          <article key={th.id} className="trend-card"
                   style={{ borderTopColor: th.color }}>
            <header>
              <h3>{th.nombre[lang] || th.nombre.es}</h3>
              <span className="trend-count" style={{ color: th.color }}>
                {th.n_nodos} <small>{t.trendsNodes}</small>
              </span>
            </header>
            <Sparkline theme={th} />
            <p className="trend-resumen">{th.resumen[lang] || th.resumen.es}</p>
            {th.estado[lang] && th.estado.es !== '-' &&
             !(th.resumen[lang] || '').includes(th.estado[lang] || '') && (
              <p className="trend-estado">
                <strong>{t.trendsStatus}:</strong> {th.estado[lang] || th.estado.es}
              </p>
            )}
            {th.nodos.length > 0 && (
              <>
                <h4>{t.trendsRecent}</h4>
                <ul className="trend-nodes">
                  {th.nodos.slice(0, 6).map((n, i) => (
                    <li key={i}>
                      <span className="tn-date">{n.fecha.slice(5)}</span>
                      {n.impacto != null && (
                        <span className="tn-imp" style={{ color: th.color }}>
                          {n.impacto}
                        </span>
                      )}
                      {n.url ? (
                        <a href={n.url} target="_blank" rel="noopener noreferrer">
                          {(n.titulo[lang] || n.titulo.es).slice(0, 80)}
                        </a>
                      ) : (
                        <span>{(n.titulo[lang] || n.titulo.es).slice(0, 80)}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
