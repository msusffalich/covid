import type { Lang, Nodo, Pulse } from './types'

/** Genera la nota Obsidian (frontmatter PARA) de un nodo — mismo formato
 *  que pipeline/gp/promote.py, para alimentar el segundo cerebro. */
export function noteForNode(n: Nodo): string {
  const actores = n.actores.join(', ')
  const fuentes = n.fuentes.join(', ')
  const enlaces = n.actores.slice(0, 4).map((a) => `[[${a}]]`).join(' · ')
  const refs = n.referencias
    .map((r) => `- [${r.fuente}](${r.url}) — ${r.titulo}`)
    .join('\n')
  return `---
titulo: "${n.titulo.es}"
title_en: "${n.titulo.en}"
fecha: ${n.fecha}
categoria: ${n.categoria}
impacto: ${n.impacto ?? 'null'}
actores: [${actores}]
fuentes: [${fuentes}]
estado: ${n.estado}
para: Recursos
origen: global-pulse
---
## Sintesis
${n.sintesis.es}

## Synthesis (EN)
${n.sintesis.en}

## Enlaces
${enlaces}

## Referencias
${refs}
`
}

/** Digest del pulso completo: todas las notas en un solo .md. */
export function pulseDigest(p: Pulse, lang: Lang): string {
  const head = lang === 'es'
    ? `# Global Pulse — pulso del ${p.meta.fecha}\n\n> ${p.nodos.length} nodos · generado ${p.meta.generado}\n\n`
    : `# Global Pulse — pulse of ${p.meta.fecha}\n\n> ${p.nodos.length} nodes · generated ${p.meta.generado}\n\n`
  return head + p.nodos.map((n) => noteForNode(n)).join('\n---\n\n')
}

export function slug(text: string, max = 60): string {
  return text.normalize('NFKD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-zA-Z0-9 -]/g, '').trim().replace(/\s+/g, '-').slice(0, max)
}

export function downloadMarkdown(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
