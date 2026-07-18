import { createContext, useContext } from 'react'
import type { Lang } from './types'

export const DICT = {
  es: {
    tagline: 'Del ruido global al conocimiento accionable',
    pulseOf: 'fecha del pulso',
    refresh: 'Actualizar',
    refreshing: 'Actualizando…',
    updatedAt: 'Generado',
    manual: 'Manual de usuario',
    legendTitle: 'Cómo leer esta vista',
    legendSize: 'Tamaño del círculo = impacto (0–100)',
    legendHalo: 'Halo pulsante = nodo activo del pulso vigente',
    legendLink: 'Línea = relación entre nodos (actores o región compartida)',
    legendSel: 'Borde blanco = nodo seleccionado',
    legendClick: 'Toca o haz clic en un nodo para abrir su detalle y fuentes',
    demoImg: 'Ilustración de demostración',
    downloadNote: 'Nota Obsidian (.md)',
    downloadPulse: 'Descargar notas Obsidian (.md)',
    engineNames: { heuristic: 'heurístico', api: 'LLM (API)' } as Record<string, string>,
    map: 'Mapa',
    graph: 'Grafo',
    list: 'Lista',
    all: 'Todas',
    categories: 'Categoría',
    minImpact: 'Impacto mínimo',
    listen: 'Escuchar el pulso',
    stop: 'Detener',
    verified: 'verificado',
    unverified: 'sin verificar',
    sources: 'Fuentes (Capa 3)',
    actors: 'Actores',
    related: 'Nodos relacionados',
    impact: 'Impacto',
    nodes: 'nodos',
    close: 'Cerrar',
    demoNote: 'Pulso de demostración: datos basados en cobertura pública documentada. Ejecuta el pipeline en modo live para ingesta en tiempo real.',
    offline: 'Sin conexión: mostrando el último pulso válido.',
    install: 'Instalable como app (PWA)',
    engine: 'motor',
    region: 'Región',
    readNode: 'Leer este nodo',
    categoriesNames: {
      geopolitica: 'Geopolítica', economia: 'Economía', ciencia: 'Ciencia',
      clima: 'Clima', tecnologia: 'Tecnología', sociedad: 'Sociedad',
    } as Record<string, string>,
  },
  en: {
    tagline: 'From global noise to actionable knowledge',
    pulseOf: 'pulse date',
    refresh: 'Refresh',
    refreshing: 'Refreshing…',
    updatedAt: 'Generated',
    manual: 'User manual',
    legendTitle: 'How to read this view',
    legendSize: 'Circle size = impact (0–100)',
    legendHalo: 'Pulsing halo = active node in the current pulse',
    legendLink: 'Line = relation between nodes (shared actors or region)',
    legendSel: 'White border = selected node',
    legendClick: 'Tap or click a node to open its detail and sources',
    demoImg: 'Demo illustration',
    downloadNote: 'Obsidian note (.md)',
    downloadPulse: 'Download Obsidian notes (.md)',
    engineNames: { heuristic: 'heuristic', api: 'LLM (API)' } as Record<string, string>,
    map: 'Map',
    graph: 'Graph',
    list: 'List',
    all: 'All',
    categories: 'Category',
    minImpact: 'Min. impact',
    listen: 'Listen to the pulse',
    stop: 'Stop',
    verified: 'verified',
    unverified: 'unverified',
    sources: 'Sources (Layer 3)',
    actors: 'Actors',
    related: 'Related nodes',
    impact: 'Impact',
    nodes: 'nodes',
    close: 'Close',
    demoNote: 'Demo pulse: data based on documented public coverage. Run the pipeline in live mode for real-time ingestion.',
    offline: 'Offline: showing the last valid pulse.',
    install: 'Installable as an app (PWA)',
    engine: 'engine',
    region: 'Region',
    readNode: 'Read this node',
    categoriesNames: {
      geopolitica: 'Geopolitics', economia: 'Economy', ciencia: 'Science',
      clima: 'Climate', tecnologia: 'Technology', sociedad: 'Society',
    } as Record<string, string>,
  },
} as const

export type Dict = (typeof DICT)['es']

export const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({
  lang: 'es',
  setLang: () => {},
})

export function useLang() {
  const { lang, setLang } = useContext(LangContext)
  const t = DICT[lang] as Dict
  return { lang, setLang, t }
}

export function detectLang(): Lang {
  const saved = localStorage.getItem('gp-lang')
  if (saved === 'es' || saved === 'en') return saved
  return navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en'
}
