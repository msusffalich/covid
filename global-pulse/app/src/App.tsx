import { useEffect, useMemo, useState } from 'react'
import MapView from './components/MapView'
import GraphView from './components/GraphView'
import NodeDetail from './components/NodeDetail'
import { DICT, LangContext, detectLang, useLang } from './i18n'
import { useSpeech } from './useSpeech'
import { CATEGORY_COLORS, type Lang, type Pulse } from './types'

type View = 'map' | 'graph' | 'list'

function Header({ pulse }: { pulse: Pulse | null }) {
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
  const [view, setView] = useState<View>('map')
  const [cat, setCat] = useState<string>('all')
  const [minImpact, setMinImpact] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    fetch('./data/pulse-latest.json')
      .then((r) => r.json())
      .then(setPulse)
      .catch(() => setError(true))
  }, [])

  const nodos = useMemo(() => {
    if (!pulse) return []
    return pulse.nodos.filter((n) =>
      (cat === 'all' || n.categoria === cat) &&
      (n.impacto ?? 0) >= minImpact)
  }, [pulse, cat, minImpact])

  const selNode = nodos.find((n) => n.id === selected)
    ?? pulse?.nodos.find((n) => n.id === selected) ?? null

  if (error) return <main className="center"><p>{t.offline}</p></main>
  if (!pulse) return <main className="center"><span className="pulse-dot big" /></main>

  const m = pulse.meta
  const cats = Object.keys(CATEGORY_COLORS)

  return (
    <>
      <Header pulse={pulse} />
      <main>
        <section className="kpis">
          <div className="kpi"><strong>{m.fecha}</strong><span>{t.pulseOf}</span></div>
          <div className="kpi"><strong>{nodos.length}</strong><span>{t.nodes}</span></div>
          <div className="kpi"><strong>{m.metricas.verificados}/{m.metricas.nodos}</strong>
            <span>{t.verified}</span></div>
          <div className="kpi"><strong>{m.motor_sintesis}</strong><span>{t.engine}</span></div>
        </section>

        {m.modo === 'fixture' && <p className="demo-note">{t.demoNote}</p>}

        <section className="controls">
          <div className="view-toggle" role="tablist">
            {(['map', 'graph', 'list'] as View[]).map((v) => (
              <button key={v} role="tab" aria-selected={view === v}
                      className={view === v ? 'on' : ''} onClick={() => setView(v)}>
                {t[v as 'map' | 'graph' | 'list']}
              </button>
            ))}
          </div>
          <select value={cat} onChange={(e) => setCat(e.target.value)}
                  aria-label={t.categories}>
            <option value="all">{t.categories}: {t.all}</option>
            {cats.map((c) => (
              <option key={c} value={c}>{t.categoriesNames[c] ?? c}</option>
            ))}
          </select>
          <label className="impact-filter">
            {t.minImpact}: <strong>{minImpact}</strong>
            <input type="range" min={0} max={100} step={5} value={minImpact}
                   onChange={(e) => setMinImpact(Number(e.target.value))} />
          </label>
        </section>

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

        {selNode && (
          <NodeDetail nodo={selNode} all={pulse.nodos}
                      onClose={() => setSelected(null)} onSelect={setSelected} />
        )}
      </main>
      <footer>
        <span>Global Pulse · schema {m.schema} · {t.install}</span>
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
