import { useState } from 'react'
import { useLang } from '../i18n'
import { useSpeech } from '../useSpeech'
import { CATEGORY_COLORS, type Nodo } from '../types'

interface Props {
  nodo: Nodo
  all: Nodo[]
  demo?: boolean
  onClose: () => void
  onSelect: (id: string) => void
}

export default function NodeDetail({ nodo, all, demo, onClose, onSelect }: Props) {
  const { lang, t } = useLang()
  const { speak, stop, speaking, supported } = useSpeech(lang)
  const [imgError, setImgError] = useState<Record<string, boolean>>({})

  const color = CATEGORY_COLORS[nodo.categoria] ?? '#1FA8A0'
  const related = nodo.relaciones
    .map((id) => all.find((n) => n.id === id))
    .filter((n): n is Nodo => Boolean(n))
  const visibleImgs = nodo.imagenes.filter((u) => !imgError[u])

  return (
    <aside className="detail" role="dialog" aria-modal="false">
      <div className="detail-head" style={{ borderColor: color }}>
        <span className="badge" style={{ background: color }}>
          {t.categoriesNames[nodo.categoria] ?? nodo.categoria}
        </span>
        <span className={`badge state ${nodo.estado}`}>
          {nodo.estado === 'verificado' ? t.verified : t.unverified}
        </span>
        {nodo.impacto !== null && (
          <span className="badge impact">{t.impact} {nodo.impacto}</span>
        )}
        <button className="icon-btn" onClick={onClose} aria-label={t.close}>✕</button>
      </div>

      <h2>{nodo.titulo[lang] || nodo.titulo.es}</h2>
      <p className="meta-line">{nodo.fecha} · {t.region}: {nodo.geo.region}</p>
      <p className="sintesis">{nodo.sintesis[lang] || nodo.sintesis.es}</p>

      {supported && (
        <button className="chip-btn" onClick={() =>
          speaking ? stop() : speak(
            `${nodo.titulo[lang] || nodo.titulo.es}. ${nodo.sintesis[lang] || nodo.sintesis.es}`)}>
          {speaking ? `■ ${t.stop}` : `🔊 ${t.readNode}`}
        </button>
      )}

      {visibleImgs.length > 0 && (
        <>
          <div className="img-row">
            {visibleImgs.map((u) => (
              <img key={u} src={u} alt={demo ? t.demoImg : ''} loading="lazy"
                   onError={() => setImgError((s) => ({ ...s, [u]: true }))} />
            ))}
          </div>
          {demo && <small className="img-caption">{t.demoImg}</small>}
        </>
      )}

      {nodo.actores.length > 0 && (
        <>
          <h3>{t.actors}</h3>
          <div className="chips">
            {nodo.actores.map((a) => <span key={a} className="chip">{a}</span>)}
          </div>
        </>
      )}

      {related.length > 0 && (
        <>
          <h3>{t.related}</h3>
          <div className="chips">
            {related.map((r) => (
              <button key={r.id} className="chip link" onClick={() => onSelect(r.id)}>
                {(r.titulo[lang] || r.titulo.es).slice(0, 46)}
              </button>
            ))}
          </div>
        </>
      )}

      <h3>{t.sources}</h3>
      <ul className="refs">
        {nodo.referencias.map((r) => (
          <li key={r.id}>
            <a href={r.url} target="_blank" rel="noopener noreferrer">
              {r.fuente}
            </a>
            <span> — {r.titulo}</span>
            <code>{r.id}</code>
          </li>
        ))}
      </ul>
    </aside>
  )
}
