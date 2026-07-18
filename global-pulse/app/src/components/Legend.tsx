import { useLang } from '../i18n'
import { CATEGORY_COLORS } from '../types'

/** Leyenda de lectura del mapa y del grafo (bilingue). */
export default function Legend({ view }: { view: 'map' | 'graph' | 'list' }) {
  const { t } = useLang()
  return (
    <div className="legend" aria-label={t.legendTitle}>
      <strong>{t.legendTitle}</strong>
      <div className="legend-cats">
        {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
          <span key={cat} className="legend-item">
            <span className="cat-dot" style={{ background: color }} />
            {t.categoriesNames[cat] ?? cat}
          </span>
        ))}
      </div>
      <ul>
        <li>
          <span className="legend-sizes" aria-hidden="true">
            <span style={{ width: 8, height: 8 }} />
            <span style={{ width: 13, height: 13 }} />
            <span style={{ width: 18, height: 18 }} />
          </span>
          {t.legendSize}
        </li>
        {view === 'map' && <li><span className="legend-halo" aria-hidden="true" />{t.legendHalo}</li>}
        {view === 'graph' && <li><span className="legend-line" aria-hidden="true" />{t.legendLink}</li>}
        <li><span className="legend-ring" aria-hidden="true" />{t.legendSel}</li>
        <li className="legend-hint">{t.legendClick}</li>
      </ul>
    </div>
  )
}
