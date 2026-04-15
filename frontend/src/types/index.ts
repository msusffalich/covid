// ---------------------------------------------------------------------------
// Domain types shared across the app
// ---------------------------------------------------------------------------

export type Language = 'es' | 'en'

export type OutputFormat = 'pdf' | 'pptx' | 'excel' | 'image'

/**
 * Mirrors the app's session state machine:
 *   idle → researching → awaiting_format → generating → done → error
 */
export type AppPhase =
  | 'idle'
  | 'researching'
  | 'awaiting_format'
  | 'generating'
  | 'done'
  | 'error'

export interface Source {
  title: string
  url: string
  snippet: string
  citation_apa: string
  citation_ieee: string
}

export interface ProgressEvent {
  step: number
  total: number
  detail: string
}

export interface ResearchResult {
  summary: string
  sources: Source[]
}

export interface AppState {
  phase: AppPhase
  language: Language
  topic: string
  sessionId: string | null
  progress: ProgressEvent | null
  statusMessage: string
  result: ResearchResult | null
  outputFormat: OutputFormat | null
  extraInstructions: string
  downloadUrl: string | null
  errorMessage: string | null
}

export const FORMAT_LABELS: Record<OutputFormat, { es: string; en: string; icon: string }> = {
  pdf:   { es: 'Reporte PDF',        en: 'PDF Report',        icon: '📄' },
  pptx:  { es: 'Presentación PPTX',  en: 'PPTX Presentation', icon: '📊' },
  excel: { es: 'Excel de Datos',      en: 'Data Excel',        icon: '📈' },
  image: { es: 'Infografía PNG',      en: 'PNG Infographic',   icon: '🖼️' },
}

export const UI_STRINGS = {
  es: {
    appTitle: 'Investigador Inteligente Multimodal',
    appSubtitle: 'Busca información real y genera documentos profesionales en segundos',
    selectLanguage: 'Idioma del informe',
    topicLabel: 'Tema de investigación',
    topicPlaceholder: 'Ej: Impacto del cambio climático en la agricultura de América Latina',
    topicHint: 'Sé específico para obtener mejores resultados.',
    startButton: 'Investigar',
    researching: 'Investigando…',
    researchDone: '¡Investigación completada!',
    summaryTitle: 'Resumen de Hallazgos',
    sourcesTitle: 'Fuentes Encontradas',
    chooseFormat: '¿Qué tipo de documento deseas generar?',
    extraLabel: 'Instrucciones adicionales (opcional)',
    extraPlaceholder: 'Ej: Incluir gráficas, enfocarse en datos de 2020-2024, tono formal…',
    generateButton: 'Generar Documento',
    generating: 'Generando tu documento…',
    downloadButton: 'Descargar',
    newResearch: 'Nueva Investigación',
    errorTitle: 'Ocurrió un error',
    retry: 'Reintentar',
    sourcesCount: (n: number) => `${n} fuente${n !== 1 ? 's' : ''} encontrada${n !== 1 ? 's' : ''}`,
  },
  en: {
    appTitle: 'Multimodal Intelligent Researcher',
    appSubtitle: 'Find real information and generate professional documents in seconds',
    selectLanguage: 'Report language',
    topicLabel: 'Research topic',
    topicPlaceholder: 'E.g.: Impact of climate change on Latin American agriculture',
    topicHint: 'Be specific for better results.',
    startButton: 'Research',
    researching: 'Researching…',
    researchDone: 'Research complete!',
    summaryTitle: 'Findings Summary',
    sourcesTitle: 'Found Sources',
    chooseFormat: 'What type of document do you want to generate?',
    extraLabel: 'Additional instructions (optional)',
    extraPlaceholder: 'E.g.: Include charts, focus on 2020-2024 data, formal tone…',
    generateButton: 'Generate Document',
    generating: 'Generating your document…',
    downloadButton: 'Download',
    newResearch: 'New Research',
    errorTitle: 'An error occurred',
    retry: 'Retry',
    sourcesCount: (n: number) => `${n} source${n !== 1 ? 's' : ''} found`,
  },
} as const
