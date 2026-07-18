import { useEffect, useMemo, useState } from 'react'
import {
  forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY,
} from 'd3-force'
import { CATEGORY_COLORS, type Lang, type Nodo } from '../types'

interface Props {
  nodos: Nodo[]
  lang: Lang
  selected: string | null
  onSelect: (id: string) => void
}

interface SimNode { id: string; x: number; y: number }

const W = 960
const H = 480

export default function GraphView({ nodos, lang, selected, onSelect }: Props) {
  const [positions, setPositions] = useState<Record<string, [number, number]>>({})

  const links = useMemo(() => {
    const ids = new Set(nodos.map((n) => n.id))
    const out: { source: string; target: string }[] = []
    nodos.forEach((n) =>
      n.relaciones.forEach((r) => {
        if (ids.has(r) && n.id < r) out.push({ source: n.id, target: r })
      }))
    return out
  }, [nodos])

  useEffect(() => {
    const simNodes: SimNode[] = nodos.map((n, i) => ({
      id: n.id,
      x: W / 2 + 120 * Math.cos((2 * Math.PI * i) / Math.max(nodos.length, 1)),
      y: H / 2 + 90 * Math.sin((2 * Math.PI * i) / Math.max(nodos.length, 1)),
    }))
    const sim = forceSimulation(simNodes as any)
      .force('charge', forceManyBody().strength(-140))
      .force('x', forceX(W / 2).strength(0.09))
      .force('y', forceY(H / 2).strength(0.16))
      .force('collide', forceCollide(58))
      .force('link', forceLink(links.map((l) => ({ ...l })) as any)
        .id((d: any) => d.id).distance(130))
      .stop()
    for (let i = 0; i < 200; i++) sim.tick()
    const pos: Record<string, [number, number]> = {}
    simNodes.forEach((s) => {
      pos[s.id] = [
        Math.max(50, Math.min(W - 50, s.x)),
        Math.max(40, Math.min(H - 40, s.y)),
      ]
    })
    setPositions(pos)
  }, [nodos, links])

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="map-svg" role="img"
         aria-label="Grafo de relaciones entre nodos">
      <g>
        {links.map((l, i) => {
          const a = positions[l.source]
          const b = positions[l.target]
          if (!a || !b) return null
          return <line key={i} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                       className="graph-link" />
        })}
      </g>
      <g>
        {nodos.map((n) => {
          const p = positions[n.id]
          if (!p) return null
          const r = 12 + ((n.impacto ?? 20) / 100) * 16
          const color = CATEGORY_COLORS[n.categoria] ?? '#1FA8A0'
          const isSel = selected === n.id
          const label = n.titulo[lang] || n.titulo.es
          return (
            <g key={n.id} transform={`translate(${p[0]},${p[1]})`}
               className={`node-dot${isSel ? ' sel' : ''}`}
               onClick={() => onSelect(n.id)} role="button" tabIndex={0}
               onKeyDown={(e) => e.key === 'Enter' && onSelect(n.id)}>
              <circle r={r} fill={color} opacity={0.85}
                      stroke={isSel ? '#fff' : 'none'} strokeWidth={2} />
              <text y={r + 14} textAnchor="middle" className="graph-label">
                {label.length > 34 ? label.slice(0, 32) + '…' : label}
              </text>
            </g>
          )
        })}
      </g>
    </svg>
  )
}
