export type Lang = 'es' | 'en'

export interface Bilingual { es: string; en: string }

export interface Referencia {
  id: string
  titulo: string
  url: string
  fuente: string
  fecha: string
  idioma: string
}

export interface Nodo {
  id: string
  titulo: Bilingual
  sintesis: Bilingual
  categoria: string
  actores: string[]
  geo: { lat: number; lon: number; region: string }
  impacto: number | null
  relaciones: string[]
  fuentes: string[]
  imagenes: string[]
  estado: 'verificado' | 'sin_verificar'
  fecha: string
  referencias: Referencia[]
}

export interface TrendNode {
  fecha: string
  titulo: Bilingual
  impacto: number | null
  categoria: string
  kardashev: string
  url: string
  fuente: string
}

export interface TrendTheme {
  id: string
  nombre: Bilingual
  color: string
  n_nodos: number
  ultima_fecha: string | null
  resumen: Bilingual
  estado: Bilingual
  serie: { fecha: string; max: number; n: number }[]
  nodos: TrendNode[]
}

export interface Trends {
  meta: { generado: string; ventana_dias: number; motor: string; modo: string }
  temas: TrendTheme[]
}

export interface Pulse {
  meta: {
    schema: string
    fecha: string
    generado: string
    modo: string
    motor_sintesis: string
    metricas: Record<string, number>
    descargo: string
  }
  nodos: Nodo[]
}

export const CATEGORY_COLORS: Record<string, string> = {
  geopolitica: '#E4634F',
  economia: '#E4A11B',
  ciencia: '#7C6FE4',
  clima: '#3FA65C',
  tecnologia: '#3D9BE4',
  innovacion: '#1CB0C8',
  salud: '#EE6C9B',
  sociedad: '#C75FA8',
}
