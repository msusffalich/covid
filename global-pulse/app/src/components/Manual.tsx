import { useLang } from '../i18n'

interface Section { h: string; p: string[] }

const MANUAL: Record<'es' | 'en', { title: string; sections: Section[] }> = {
  es: {
    title: 'Manual de usuario — Global Pulse',
    sections: [
      { h: '1. Qué es Global Pulse',
        p: ['Global Pulse convierte el ruido informativo global en «nodos de impacto»: unidades de conocimiento sintetizadas, puntuadas (0–100) y siempre trazables a sus fuentes originales (Capa 3). Cada día el sistema publica un «pulso»: el conjunto de nodos más relevantes de las últimas 24 horas.'] },
      { h: '2. Instalación (PWA)',
        p: ['La aplicación es instalable en móvil y escritorio: en el navegador, usa «Añadir a pantalla de inicio» (Android/iOS) o el icono de instalación de la barra de direcciones (Chrome/Edge). Una vez instalada funciona sin conexión mostrando el último pulso válido.'] },
      { h: '3. Vistas: Mapa, Grafo y Lista',
        p: ['Mapa: cada círculo es un nodo situado donde ocurre el evento. Su color indica la categoría y su tamaño el impacto; el halo pulsante señala que pertenece al pulso vigente.',
            'Grafo: muestra las relaciones entre nodos; una línea une nodos que comparten actores o región.',
            'Lista: ordena los nodos por impacto, con su categoría y puntuación. La leyenda «Cómo leer esta vista» está siempre bajo el panel.'] },
      { h: '4. Filtros y categorías',
        p: ['Filtra tocando las categorías (se pueden combinar varias) y por impacto mínimo con el deslizador. Los filtros se aplican a las tres vistas.',
            'Categorías: Geopolítica · Economía · Ciencia · Impacto climático (consecuencias del cambio climático: fenómenos extremos, emisiones, adaptación) · Tecnología · Innovación y dispositivos (productos, inventos y lanzamientos) · Salud y bienestar · Sociedad.'] },
      { h: '5. Detalle de un nodo y fuentes (Capa 3)',
        p: ['Toca cualquier nodo para abrir su ficha: síntesis, actores, imágenes, nodos relacionados y las fuentes originales con su identificador de evidencia (ev_…). El distintivo «verificado» significa que el nodo está anclado a evidencia; «sin verificar» indica que carece de fuente suficiente y no muestra impacto.'] },
      { h: '6. Idiomas',
        p: ['La interfaz y el contenido están disponibles en español neutro e inglés. El idioma se detecta automáticamente y puede cambiarse con el conmutador ES/EN; la preferencia queda guardada en el dispositivo.'] },
      { h: '7. Audio (multimodal)',
        p: ['«Escuchar el pulso» lee en voz alta los nodos principales del día; dentro de la ficha, «Leer este nodo» narra ese nodo. Usa la síntesis de voz del navegador en el idioma activo, sin servicios externos.'] },
      { h: '8. Cuándo se actualiza la información',
        p: ['El pipeline genera un pulso nuevo una vez al día (05:00 UTC mediante la automatización programada, o al ejecutarlo manualmente).',
            'La aplicación carga el pulso más reciente al abrirse y cada vez que vuelve a primer plano; el botón «Actualizar» fuerza la recarga inmediata.',
            'Sin conexión, se muestra el último pulso válido guardado; la fecha y hora de generación aparecen junto al botón.'] },
      { h: '9. Exportar al segundo cerebro (Obsidian)',
        p: ['Tres vías para alimentar tu bóveda: (1) el botón «⬇ Descargar notas Obsidian (.md)» junto a «Actualizar» descarga el pulso completo en Markdown; (2) en la ficha de cada nodo, «⬇ Nota Obsidian (.md)» descarga esa nota individual con frontmatter PARA; (3) automático: el pipeline escribe las notas en data/vault/ — define la variable GP_VAULT_DIR con la ruta de tu bóveda para que las cree directamente dentro de ella.'] },
      { h: '10. Nota sobre la demostración',
        p: ['Si el pulso indica «demostración», los datos provienen de un conjunto fijo basado en cobertura pública documentada y las imágenes son ilustraciones generadas. En modo real (live), el sistema ingiere más de 30 fuentes RSS gratuitas y confiables más GDELT.'] },
    ],
  },
  en: {
    title: 'User manual — Global Pulse',
    sections: [
      { h: '1. What is Global Pulse',
        p: ['Global Pulse turns global information noise into “impact nodes”: synthesized knowledge units, scored 0–100 and always traceable to their original sources (Layer 3). Every day the system publishes a “pulse”: the most relevant nodes of the last 24 hours.'] },
      { h: '2. Installation (PWA)',
        p: ['The app is installable on mobile and desktop: in your browser use “Add to Home Screen” (Android/iOS) or the install icon in the address bar (Chrome/Edge). Once installed it works offline, showing the last valid pulse.'] },
      { h: '3. Views: Map, Graph and List',
        p: ['Map: each circle is a node placed where the event happens. Its color is the category and its size the impact; the pulsing halo marks nodes in the current pulse.',
            'Graph: shows relations between nodes; a line joins nodes sharing actors or region.',
            'List: sorts nodes by impact with category and score. The “How to read this view” legend always sits under the panel.'] },
      { h: '4. Filters and categories',
        p: ['Filter by tapping categories (several can be combined) and by minimum impact with the slider. Filters apply to all three views.',
            'Categories: Geopolitics · Economy · Science · Climate impact (consequences of climate change: extreme events, emissions, adaptation) · Technology · Innovation & devices (products, inventions and launches) · Health & wellness · Society.'] },
      { h: '5. Node detail and sources (Layer 3)',
        p: ['Tap any node to open its card: synthesis, actors, images, related nodes and the original sources with their evidence id (ev_…). The “verified” badge means the node is anchored to evidence; “unverified” means it lacks sufficient sourcing and shows no impact score.'] },
      { h: '6. Languages',
        p: ['Interface and content are available in neutral Spanish and English. Language is auto-detected and can be switched with the ES/EN toggle; your preference is stored on the device.'] },
      { h: '7. Audio (multimodal)',
        p: ['“Listen to the pulse” reads the day’s top nodes aloud; inside a card, “Read this node” narrates that node. It uses the browser’s speech synthesis in the active language, with no external services.'] },
      { h: '8. When the information updates',
        p: ['The pipeline generates a new pulse once a day (05:00 UTC via the scheduled automation, or on manual runs).',
            'The app loads the latest pulse when opened and whenever it returns to the foreground; the “Refresh” button forces an immediate reload.',
            'Offline, the last stored valid pulse is shown; the generation date and time appear next to the button.'] },
      { h: '9. Export to your second brain (Obsidian)',
        p: ['Three ways to feed your vault: (1) the "⬇ Download Obsidian notes (.md)" button next to "Refresh" downloads the full pulse as Markdown; (2) inside each node card, "⬇ Obsidian note (.md)" downloads that single note with PARA frontmatter; (3) automatic: the pipeline writes notes to data/vault/ — set the GP_VAULT_DIR variable to your vault path so they are created directly inside it.'] },
      { h: '10. About the demo',
        p: ['If the pulse says “demo”, data comes from a fixed set based on documented public coverage and images are generated illustrations. In live mode the system ingests 30+ free, reliable RSS sources plus GDELT.'] },
    ],
  },
}

export default function Manual({ onClose }: { onClose: () => void }) {
  const { lang, t } = useLang()
  const m = MANUAL[lang]
  return (
    <div className="manual-overlay" role="dialog" aria-modal="true"
         aria-label={m.title} onClick={onClose}>
      <article className="manual" onClick={(e) => e.stopPropagation()}>
        <header>
          <h2>{m.title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label={t.close}>✕</button>
        </header>
        {m.sections.map((s) => (
          <section key={s.h}>
            <h3>{s.h}</h3>
            {s.p.map((par, i) => <p key={i}>{par}</p>)}
          </section>
        ))}
      </article>
    </div>
  )
}
