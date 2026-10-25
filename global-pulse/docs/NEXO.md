# Generador diario: El Nexo

El modo `live` usa `pipeline/gp/daily.py` y el prompt maestro completo de
`pipeline/prompts/nexo.md`. Mantiene los JSON y la ruta de Markdown existentes:
`data/global-brain/Global Brain/00 · Pulso Diario/AAAA-MM-DD — Pulso.md`.
La web recibe ese mismo texto en `reporte_markdown` y en `/data/AAAA-MM-DD — Pulso.md`.
Su SHA-256 se publica en `meta.reporte_sha256`.

Solo se admiten documentos del dominio de la institución registrada y con fecha
oficial, hora y zona horaria dentro de las 24 horas anteriores al corte UTC.
No se reemplaza la fecha de publicación por la de recolección o actualización.
Las fuentes, su dimensión y sus dominios están en `gp/official.py`.
Las fallas se registran en `cobertura` y en el reporte: una fuente caída no prueba
ausencia de novedades. Si todas fallan se conserva la edición publicada.

El generador selecciona hasta cinco hechos por dimensión. La fecha, fuente y URL
proceden del registro original; el modelo solo selecciona, traduce y sintetiza.
El Nexo es una segunda etapa, limitada a los hechos seleccionados. Se rechazan
citas desconocidas, estados inválidos y movimientos sin evidencia de al menos
dos dimensiones del flujo o bucle. Una relación causal sigue siendo una
interpretación del modelo; la presencia de citas no garantiza por sí sola su corrección.

Requiere el secreto existente `ANTHROPIC_API_KEY`. La síntesis oficial no cae al
motor heurístico ni rellena con prensa. El modo `fixture` queda para pruebas
locales y no publica mediante el workflow diario.

Los checkpoints en `data/checkpoints/AAAA-MM-DD.json` guardan documentos, hechos,
cobertura y análisis. Una repetición conserva el corte, retoma la etapa pendiente
y no repite una edición ya completada. GitHub Actions serializa las corridas y
guarda el checkpoint incluso si falla la etapa de análisis. El reporte parcial
declara «análisis pendiente». No borrar checkpoints para forzar otra edición.

El adaptador de ORIA en `integrations/archivar-global-brain.py` reemplaza la
reconstrucción editorial por el Markdown canónico. Acepta días oficiales sin
nodos, verifica la huella y conserva el original exacto en
`Global Brain/Fuentes/AAAA-MM-DD/reporte.md`. La nota de lectura conserva su
ruta en `Global Brain/Reportes`, los metadatos y las anotaciones personales.
El sincronizador existente replica esas rutas a Drive; no se crea otra tarea.

Los reportes históricos conservan su formato y sus fuentes originales. Las
correcciones requieren evidencia oficial: el nuevo generador no las inventa.

Validación: `python -m unittest discover -s tests -p test_nexo.py`,
`python -m tests.test_pipeline` (desde `pipeline`) y `npm run build` (desde `app`).
