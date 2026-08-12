import { useCallback, useEffect, useMemo, useState } from 'react'
import MapView from './components/MapView'
import GraphView from './components/GraphView'
import NodeDetail from './components/NodeDetail'
import Legend from './components/Legend'
import Manual from './components/Manual'
import TrendsView from './components/TrendsView'
import { DICT, LangContext, detectLang, useLang } from './i18n'
import { useSpeech } from './useSpeech'
import { CATEGORY_COLORS, type Lang, type Pulse } from './types'
import { downloadMarkdown, pulseDigest } from './markdown'

type View = 'map' | 'graph' | 'list' | 'trends'

function Header({ pulse, onManual }: { pulse: Pulse | null; onManual: () => void }) {
  const { lang, setLang, t } = useLang()
  const { speak, stop, speaking, supported } = useSpeech(lang)

  const listen = () => {
    if (!pulse) return
    if (speaking) { stop(); return }
    const top = pulse.nodos.slice(0, 6)
    const intro = lang === 'es'
      ? `Pulso global del ${pulse.meta.fecha}. ${top.length} nodos principales.`
      : `Global pulse for ${pulse.meta.fecha}. Top ${top.length} nodes.`
    const bodyText = top.map((n, i) =>
      `${i + 1}. ${n.titulo[lang] || n.titulo.es}. ${n.sintesis[lang] || n.sintesis.es}`,
    ).join(' ')
    speak(`${intro} ${bodyText}`)
  }

  return (
    <header className="topbar">
      <div className="brand">
        <span className="pulse-dot" aria-hidden="true" />
        <div>
          <strong>Global Pulse</strong>
          <small>{t.tagline}</small>
        </div>
      </div>
      <div className="top-actions">
        {supported && (
          <button className="chip-btn" onClick={listen}>
            {speaking ? `■ ${t.stop}` : `🔊 ${t.listen}`}
          </button>
        )}
        <button className="chip-btn ghost" onClick={onManual}
                aria-label={t.manual} title={t.manual}>
          📖 <span className="manual-word">{t.manual}</span>
        </button>
        <div className="lang-toggle" role="group" aria-label="Idioma / Language">
          {(['es', 'en'] as Lang[]).map((l) => (
            <button key={l} className={lang === l ? 'on' : ''}
                    onClick={() => { setLang(l); localStorage.setItem('gp-lang', l) }}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}

function Content() {
  const { lang, t } = useLang()
  const [pulse, setPulse] = useState<Pulse | null>(null)
  const [error, setError] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [showManual, setShowManual] = useState(false)
  const [view, setView] = useState<View>('map')
  const [catSel, setCatSel] = useState<string[]>([])   // vacio = todas
  const [minImpact, setMinImpact] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)

  // Actualizacion de datos: al abrir, al volver a primer plano y bajo demanda
  // (boton). El pulso en si se regenera una vez al dia por el pipeline.
  const loadPulse = useCallback((force = false) => {
    setRefreshing(true)
    fetch('./data/pulse-latest.json', force ? { cache: 'reload' } : undefined)
      .then((r) => r.json())
      .then((p: Pulse) => { setPulse(p); setError(false) })
      .catch(() => setPulse((prev) => { if (!prev) setError(true); return prev }))
      .finally(() => setRefreshing(false))
  }, [])

  useEffect(() => {
    loadPulse()
    const onVisible = () => document.visibilityState === 'visible' && loadPulse()
    document.addEventListener('visibilitychange', onVisible)
    window.addEventListener('focus', onVisible)
    return () => {
      document.removeEventListener('visibilitychange', onVisible)
      window.removeEventListener('focus', onVisible)
    }
  }, [loadPulse])

  const nodos = useMemo(() => {
    if (!pulse) return []
    return pulse.nodos.filter((n) =>
      (catSel.length === 0 || catSel.includes(n.categoria)) &&
      (n.impacto ?? 0) >= minImpact)
  }, [pulse, catSel, minImpact])

  // Categorias presentes en el pulso del dia (dinamicas, no fijas)
  const presentCats = useMemo(() => {
    if (!pulse) return []
    const present = new Set(pulse.nodos.map((n) => n.categoria))
    return Object.keys(CATEGORY_COLORS).filter((c) => present.has(c))
  }, [pulse])

  const toggleCat = (c: string) =>
    setCatSel((prev) => prev.includes(c)
      ? prev.filter((x) => x !== c)
      : [...prev, c])

  const selNode = nodos.find((n) => n.id === selected)
    ?? pulse?.nodos.find((n) => n.id === selected) ?? null

  if (error) return <main className="center"><p>{t.offline}</p></main>
  if (!pulse) return <main className="center"><span className="pulse-dot big" /></main>

  const m = pulse.meta

  return (
    <>
      <Header pulse={pulse} onManual={() => setShowManual(true)} />
      <main>
        <section className="kpis">
          <div className="kpi">
            <strong>{new Date(m.generado).toLocaleDateString(
              lang === 'es' ? 'es' : 'en-US',
              { day: 'numeric', month: 'short', year: 'numeric' })}</strong>
            <span>{t.pulseOf} · {new Date(m.generado).toLocaleTimeString(
              lang === 'es' ? 'es' : 'en-US',
              { hour: '2-digit', minute: '2-digit', hour12: false })} UTC</span>
          </div>
          <div className="kpi"><strong>{nodos.length}</strong><span>{t.nodes}</span></div>
          <div className="kpi"><strong>{m.metricas.verificados}/{m.metricas.nodos}</strong>
            <span>{t.verified}</span></div>
          <div className="kpi">
            <strong>{t.engineNames[m.motor_sintesis] ?? m.motor_sintesis}</strong>
            <span>{t.engine}</span>
          </div>
        </section>

        <div className="update-row">
          <button className="chip-btn" onClick={() => loadPulse(true)}
                  disabled={refreshing}>
            {refreshing ? t.refreshing : `⟳ ${t.refresh}`}
          </button>
          <button className="chip-btn ghost" onClick={() =>
            downloadMarkdown(`global-pulse-${m.fecha}.md`, pulseDigest(pulse, lang))}>
            ⬇ {t.downloadPulse}
          </button>
          <span className="updated-at">
            {t.updatedAt}: {new Date(m.generado).toLocaleString(
              lang === 'es' ? 'es' : 'en-US',
              { dateStyle: 'medium', timeStyle: 'short' })} UTC
          </span>
        </div>

        {m.modo === 'fixture' && <p className="demo-note">{t.demoNote}</p>}

        <section className="controls">
          <div className="view-toggle" role="tablist">
            {(['map', 'graph', 'list', 'trends'] as View[]).map((v) => (
              <button key={v} role="tab" aria-selected={view === v}
                      className={view === v ? 'on' : ''} onClick={() => setView(v)}>
                {t[v as 'map' | 'graph' | 'list' | 'trends']}
              </button>
            ))}
          </div>
          {view !== 'trends' && (
            <div className="cat-chips" role="group" aria-label={t.categories}>
              <button className={`fchip${catSel.length === 0 ? ' on' : ''}`}
                      onClick={() => setCatSel([])}>
                {t.all}
              </button>
              {presentCats.map((c) => (
                <button key={c}
                        className={`fchip${catSel.includes(c) ? ' on' : ''}`}
                        aria-pressed={catSel.includes(c)}
                        onClick={() => toggleCat(c)}>
                  <span className="cat-dot"
                        style={{ background: CATEGORY_COLORS[c] }} />
                  {t.categoriesNames[c] ?? c}
                </button>
              ))}
            </div>
          )}
          {view !== 'trends' && (
            <label className="impact-filter">
              {t.minImpact}: <strong>{minImpact}</strong>
              <input type="range" min={0} max={100} step={5} value={minImpact}
                     onChange={(e) => setMinImpact(Number(e.target.value))} />
            </label>
          )}
        </section>

        {view === 'trends' ? <TrendsView /> : (
        <section className="stage">
          {view === 'map' && (
            <MapView nodos={nodos} selected={selected} onSelect={setSelected} />
          )}
          {view === 'graph' && (
            <GraphView nodos={nodos} lang={lang} selected={selected}
                       onSelect={setSelected} />
          )}
          {view === 'list' && (
            <ul className="node-list">
              {nodos.map((n) => (
                <li key={n.id}>
                  <button onClick={() => setSelected(n.id)}
                          className={selected === n.id ? 'sel' : ''}>
                    <span className="cat-dot"
                          style={{ background: CATEGORY_COLORS[n.categoria] }} />
                    <span className="nl-title">{n.titulo[lang] || n.titulo.es}</span>
                    <span className="nl-impact">{n.impacto ?? '—'}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
        )}

        {view !== 'trends' && <Legend view={view} />}

        {selNode && (
          <NodeDetail nodo={selNode} all={pulse.nodos} demo={m.modo === 'fixture'}
                      onClose={() => setSelected(null)} onSelect={setSelected} />
        )}
        {showManual && <Manual onClose={() => setShowManual(false)} />}
      </main>
      <footer>
        <span>Global Pulse · schema {m.schema} · {t.install}</span>
        <button className="link-btn" onClick={() => setShowManual(true)}>
          📖 {t.manual}
        </button>
      </footer>
    </>
  )
}

export default function App() {
  const [lang, setLang] = useState<Lang>(detectLang())
  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])
  void DICT
  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <Content />
    </LangContext.Provider>
  )
}
