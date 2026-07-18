import { useMemo } from 'react'
import { geoNaturalEarth1, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import type { FeatureCollection } from 'geojson'
import worldData from 'world-atlas/countries-110m.json'
import { CATEGORY_COLORS, type Nodo } from '../types'

const world = feature(
  worldData as any,
  (worldData as any).objects.countries,
) as unknown as FeatureCollection

interface Props {
  nodos: Nodo[]
  selected: string | null
  onSelect: (id: string) => void
}

const W = 960
const H = 480

export default function MapView({ nodos, selected, onSelect }: Props) {
  const { countries, project } = useMemo(() => {
    const projection = geoNaturalEarth1().fitSize([W, H], world)
    const path = geoPath(projection)
    return {
      countries: world.features.map((f, i) => (
        <path key={i} d={path(f) ?? ''} className="country" />
      )),
      project: (lon: number, lat: number) => projection([lon, lat]) ?? [0, 0],
    }
  }, [])

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="map-svg" role="img"
         aria-label="Mapa mundial de nodos de impacto">
      <g>{countries}</g>
      <g>
        {nodos.map((n) => {
          const [x, y] = project(n.geo.lon, n.geo.lat)
          const r = 6 + ((n.impacto ?? 20) / 100) * 14
          const color = CATEGORY_COLORS[n.categoria] ?? '#1FA8A0'
          const isSel = selected === n.id
          return (
            <g key={n.id} transform={`translate(${x},${y})`}
               className={`node-dot${isSel ? ' sel' : ''}`}
               onClick={() => onSelect(n.id)} role="button" tabIndex={0}
               onKeyDown={(e) => e.key === 'Enter' && onSelect(n.id)}>
              <circle r={r + 6} fill={color} opacity={0.18}>
                <animate attributeName="r" values={`${r + 3};${r + 10};${r + 3}`}
                         dur="2.6s" repeatCount="indefinite" />
              </circle>
              <circle r={r} fill={color} opacity={0.85}
                      stroke={isSel ? '#fff' : 'none'} strokeWidth={2} />
            </g>
          )
        })}
      </g>
    </svg>
  )
}
