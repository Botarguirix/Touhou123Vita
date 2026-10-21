# Iteración 2.32: auditoría de cobertura de escenarios

Fecha: 2026-10-17.

> Actualización de auditoría, 2026-10-17: el primer TSV trataba las 30 celdas de la cuadrícula del visor como nombres obligatorios del recurso fuente y contaba todos los auxiliares como una sola clase. La auditoría ahora distingue nombres base presentes/faltantes (sin afirmar que cada celda sea requerida por el juego), auxiliares candidatos, bitmaps, sprites y CV2 aún sin consumidor asociado. Para BG34 los 64 candidatos auxiliares se explicitan como 30 tiles superiores, cuatro bitmaps y 30 `objectFa`; sus 94 archivos totales quedan clasificados, sin sobrantes. En los otros escenarios presentes se clasifican los 30 nombres base convencionales, y BG12/BG33/BG36–38 muestran auxiliares conocidos sin elementos CV2 adicionales sin asignar. BG37 tiene 3/4 auxiliares candidatos presentes; BG38, 2/4. Esto convierte la lista en un mapa de cobertura, no en una declaración de que las celdas faltantes sean bugs.

Para mover M5 desde una lista de recursos a contratos comprobables, añadí `tools/audit_stage_resources.py`. Lee el manifiesto local de TH123 y reproduce las rutas que hoy intenta el visor Vita: 30 nombres planos `0000_00..29` antes de `bg30`, y una rejilla `0000[row][col]` de 5×6 desde `bg30`. En `bg34` reconoce además la rejilla superior, cuatro bitmaps y 30 `objectFa`. El TSV conserva por escenario la presencia de carpeta, cobertura de las 30 rutas base, nombres faltantes y CV2 adicionales aún no conectados al visor. Los DAT comerciales no se copian ni empaquetan.

Resultados sobre `artifacts/th123-resource-manifest.tsv`:

- Hay carpetas de escenario en 14 de los 24 nombres que exponía entonces el visor. La Iteración 2.40 añade BG35 tras confirmar su ID en el dispatcher; el catálogo/auditoría ya cubren 25 IDs. Once IDs carecen de carpeta en los DAT TH123 locales; BG35 tampoco aparece en el manifiesto TH105 inspeccionado y su contenido sigue sin localizarse.
- `bg11`, `bg14`, `bg30`, `bg31` y `bg32` contienen los 30 nombres base que espera el cargador actual. `bg10`, `bg12`, `bg13`, `bg17`, `bg33`, `bg34`, `bg36`, `bg37` y `bg38` tienen entre 11 y 29; los huecos pueden ser transparentes/intencionales o rutas que el modelo actual no conoce, todavía no se clasifican como defectos del juego.
- El visor actual reconoce fondos auxiliares solo para `bg34`. La auditoría revela CV2 extra fuera de ese camino: `tori1/2` en `bg12`; `0001/0002` en `bg33`; y nubes, torii y otros recursos en `bg36`–`bg38`. Falta asociar cada archivo al constructor/update correcto antes de dibujarlo.

Artefactos reproducibles: `docs/STAGE_RESOURCE_AUDIT.tsv` y `artifacts/stage-resource-audit.json` (este último es local/ignorado). Regenerar con:

```powershell
python tools/audit_stage_resources.py artifacts/th123-resource-manifest.tsv `
  --output docs/STAGE_RESOURCE_AUDIT.tsv --json artifacts/stage-resource-audit.json
```

Las pruebas de la auditoría validan por separado convenciones de nombres y auxiliares candidatos. Próximo trabajo en M5: mapear constructores/vtables y callbacks de `bg12`, `bg33` y `bg36`–`bg38` con los exportes Ghidra existentes, recuperar transformaciones/animación y conectar solo recursos con evidencia. A continuación ampliar el viewer y comparar capturas/transiciones con la referencia PC. Esta iteración no cambia runtime, VPK ni afirma composición visual o mecánicas completas.


Actualización de alcance de la auditoría (Iteración 2.41): aquella primera tabla consultó sólo TH123. El runtime abre también TH105 como fallback; la nueva unión y procedencia por archivo está documentada en [ITERATION141.md](ITERATION141.md), y la tabla versionada fue regenerada con ambos manifiestos.
