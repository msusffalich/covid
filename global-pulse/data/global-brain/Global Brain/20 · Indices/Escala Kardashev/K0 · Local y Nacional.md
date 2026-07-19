---
tipo: indice
kardashev: K0
origen: global-pulse
---
# K0 · Local y Nacional

Eventos cuyo impacto se contiene en un pais o region.

## Nodos en este nivel
```dataview
TABLE fecha AS Fecha, impacto AS Impacto, categoria AS Categoria
FROM "10 · Nodos"
WHERE kardashev = "K0"
SORT fecha DESC, impacto DESC
```
> Requiere el plugin **Dataview**. Sin el, usa la busqueda: `kardashev: K0`.

[[Global Brain — Inicio|← Inicio]]
