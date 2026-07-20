# Manual de usuario — Global Pulse · User Manual

> Disponible también dentro de la aplicación (botón «📖 Manual de usuario» en el
> pie de página). / Also available inside the app ("📖 User manual" button in
> the footer).

---

## Español (neutro)

### 1. Qué es Global Pulse
Global Pulse convierte el ruido informativo global en **nodos de impacto**:
unidades de conocimiento sintetizadas, puntuadas (0–100) y siempre trazables a
sus fuentes originales (Capa 3). Cada día el sistema publica un **pulso**: el
conjunto de nodos más relevantes de las últimas 24 horas.

### 2. Instalación (PWA)
La aplicación es instalable en móvil y escritorio: en el navegador, usa
«Añadir a pantalla de inicio» (Android/iOS) o el icono de instalación de la
barra de direcciones (Chrome/Edge). Una vez instalada funciona sin conexión
mostrando el último pulso válido.

### 3. Vistas: Mapa, Grafo y Lista
- **Mapa:** cada círculo es un nodo situado donde ocurre el evento. El color
  indica la categoría y el tamaño el impacto; el halo pulsante señala que
  pertenece al pulso vigente.
- **Grafo:** muestra las relaciones entre nodos; una línea une nodos que
  comparten actores o región.
- **Lista:** ordena los nodos por impacto, con su categoría y puntuación.

La leyenda **«Cómo leer esta vista»** aparece siempre bajo el panel.

### 4. Filtros y categorías
Filtra tocando las categorías (se pueden combinar varias) y por impacto mínimo
con el deslizador. Se aplican a las tres vistas. Las categorías son:

- **Geopolítica** · **Economía** · **Ciencia** · **Tecnología** · **Cultura y Sociedad**
- **Impacto climático:** consecuencias del cambio climático (fenómenos
  extremos, emisiones, deshielo, adaptación).
- **Innovación y dispositivos:** productos nuevos, inventos, prototipos y
  lanzamientos.
- **Salud y bienestar:** medicina, salud pública, salud mental, nutrición y
  bienestar.

### 5. Detalle de un nodo y fuentes (Capa 3)
Toca cualquier nodo para abrir su ficha: síntesis, actores, imágenes, nodos
relacionados y las fuentes originales con su identificador de evidencia
(`ev_…`). «Verificado» significa anclado a evidencia; «sin verificar» indica
que carece de fuente suficiente y no muestra impacto.

### 6. Idiomas
Interfaz y contenido en español neutro e inglés. El idioma se detecta
automáticamente y puede cambiarse con el conmutador ES/EN; la preferencia se
guarda en el dispositivo.

### 7. Audio (multimodal)
«Escuchar el pulso» lee en voz alta los nodos principales del día; en la
ficha, «Leer este nodo» narra ese nodo. Usa la síntesis de voz del navegador
en el idioma activo, sin servicios externos.

### 8. Cuándo se actualiza la información
1. **Generación:** el pipeline produce un pulso nuevo **una vez al día**
   (05:00 UTC mediante GitHub Actions, o al ejecutarlo manualmente:
   `python orchestrator.py run --mode live`).
2. **Carga:** la aplicación descarga el pulso más reciente **al abrirse** y
   **al volver a primer plano**.
3. **Manual:** el botón **«⟳ Actualizar»** fuerza la recarga inmediata.
4. **Sin conexión:** se muestra el último pulso válido guardado. La fecha y
   hora de generación aparecen junto al botón.

### 9. Global Brain: el segundo cerebro (Obsidian)
Global Pulse alimenta cada día una bóveda Obsidian llamada **Global Brain**,
organizada por el **principio de Kardashev** —cada nodo se clasifica por la
escala civilizatoria de su impacto— y el método **PARA**:

- **K0 · Local y Nacional** — impacto contenido en un país o región.
- **K1 · Planetario** — afecta a la civilización global (clima, pandemias,
  gobernanza tecnológica, grandes acuerdos).
- **K2 · Estelar y Energía** — espacio y energía a gran escala.
- **K3 · Frontera Cósmica** — descubrimientos sobre el cosmos profundo.

Estructura: `Global Brain — Inicio` (mapa), `00 · Pulso Diario` (digest por
ciclo), `10 · Nodos` (notas atómicas por categoría = Recursos de PARA),
`20 · Indices` (MOCs por escala K y categoría, con Dataview) y `30 · PARA`
(tus Proyectos/Áreas/Archivo).

**Cómo usarla (alimentación automática diaria):**
1. Clona el repositorio: `git clone https://github.com/msusffalich/covid.git`
2. En Obsidian: «Abrir carpeta como bóveda» →
   `covid/global-pulse/data/global-brain/Global Brain`
3. Instala los plugins **Obsidian Git** (activa el *auto-pull* diario: la
   bóveda se actualiza sola con cada pulso) y **Dataview** (índices dinámicos).

Alternativas: los botones **«⬇»** de la app descargan el pulso completo o una
nota individual; y `GP_VAULT_DIR` hace que el pipeline escriba directamente en
una bóveda local (`export GP_VAULT_DIR="/ruta/a/mi/boveda/Global Brain"`).

### 10. Nota sobre la demostración
Si el pulso indica «demostración», los datos provienen de un conjunto fijo
basado en cobertura pública documentada y las imágenes son ilustraciones
generadas. En modo real, el sistema ingiere **más de 30 fuentes RSS gratuitas
y confiables** (BBC, DW, El País, The Guardian, Al Jazeera, NPR, NYT,
Euronews, Noticias ONU, Nature, NASA, OMS, entre otras) más GDELT.

---

## English

### 1. What is Global Pulse
Global Pulse turns global information noise into **impact nodes**: synthesized
knowledge units, scored 0–100 and always traceable to their original sources
(Layer 3). Every day the system publishes a **pulse**: the most relevant nodes
of the last 24 hours.

### 2. Installation (PWA)
The app is installable on mobile and desktop: in your browser use "Add to Home
Screen" (Android/iOS) or the install icon in the address bar (Chrome/Edge).
Once installed it works offline, showing the last valid pulse.

### 3. Views: Map, Graph and List
- **Map:** each circle is a node placed where the event happens. Color is the
  category, size the impact; the pulsing halo marks nodes in the current pulse.
- **Graph:** shows relations between nodes; a line joins nodes sharing actors
  or region.
- **List:** sorts nodes by impact with category and score.

The **"How to read this view"** legend always sits under the panel.

### 4. Filters and categories
Filter by tapping categories (several can be combined) and by minimum impact
with the slider. Filters apply to all views. Categories are:

- **Geopolitics** · **Economy** · **Science** · **Technology** · **Culture & Society**
- **Climate impact:** consequences of climate change (extreme events,
  emissions, ice loss, adaptation).
- **Innovation & devices:** new products, inventions, prototypes and launches.
- **Health & wellness:** medicine, public health, mental health, nutrition and
  well-being.

### 5. Node detail and sources (Layer 3)
Tap any node to open its card: synthesis, actors, images, related nodes and
the original sources with their evidence id (`ev_…`). "Verified" means
anchored to evidence; "unverified" means insufficient sourcing and no impact
score.

### 6. Languages
Interface and content in neutral Spanish and English. Language is
auto-detected and can be switched with the ES/EN toggle; the preference is
stored on the device.

### 7. Audio (multimodal)
"Listen to the pulse" reads the day's top nodes aloud; inside a card, "Read
this node" narrates that node. It uses the browser's speech synthesis in the
active language, with no external services.

### 8. When the information updates
1. **Generation:** the pipeline produces a new pulse **once a day** (05:00 UTC
   via GitHub Actions, or manually: `python orchestrator.py run --mode live`).
2. **Loading:** the app fetches the latest pulse **on open** and **whenever it
   returns to the foreground**.
3. **Manual:** the **"⟳ Refresh"** button forces an immediate reload.
4. **Offline:** the last stored valid pulse is shown. Generation date and time
   appear next to the button.

### 9. Global Brain: the second brain (Obsidian)
Global Pulse feeds a daily Obsidian vault called **Global Brain**, organized
by the **Kardashev principle** —each node is classified by the civilizational
scale of its impact— and the **PARA** method:

- **K0 · Local & National** — impact contained in one country or region.
- **K1 · Planetary** — affects global civilization (climate, pandemics,
  tech governance, major agreements).
- **K2 · Stellar & Energy** — space and large-scale energy.
- **K3 · Cosmic Frontier** — discoveries about the deep cosmos.

Structure: `Global Brain — Inicio` (map), `00 · Pulso Diario` (per-cycle
digest), `10 · Nodos` (atomic notes by category = PARA Resources),
`20 · Indices` (MOCs by K-scale and category, Dataview-powered) and
`30 · PARA` (your Projects/Areas/Archive).

**How to use it (automatic daily feeding):**
1. Clone the repository: `git clone https://github.com/msusffalich/covid.git`
2. In Obsidian: "Open folder as vault" →
   `covid/global-pulse/data/global-brain/Global Brain`
3. Install the **Obsidian Git** plugin (enable daily *auto-pull*: the vault
   updates itself with every pulse) and **Dataview** (dynamic indexes).

Alternatives: the app's **"⬇"** buttons download the full pulse or a single
note; and `GP_VAULT_DIR` makes the pipeline write directly into a local vault.

### 10. About the demo
If the pulse says "demo", data comes from a fixed set based on documented
public coverage and images are generated illustrations. In live mode the
system ingests **30+ free, reliable RSS sources** (BBC, DW, El País, The
Guardian, Al Jazeera, NPR, NYT, Euronews, UN News, Nature, NASA, WHO, among
others) plus GDELT.
