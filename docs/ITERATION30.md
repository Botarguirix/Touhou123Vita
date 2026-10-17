# Iteración 1.26: mapa de cobertura PAT para dash/B/C

## Hallazgo

Crucé `artifacts/pat-detail.tsv` con el roster activo usando el nuevo generador `tools/summarize_dash_dispatch.py`. El reporte completo, incluidos locks por variante y poses con hitbox dañina, es [DASH_DISPATCH_COVERAGE.md](DASH_DISPATCH_COVERAGE.md).

Los 20 personajes tienen acción 200 definida explícitamente en el PAT. Diecinueve tienen 408 y 418; Remilia no define esas acciones. Los locks 408 no son uniformes: el índice 0 usa 20 en Yuyuko, 40 en Alice y 50 en la mayoría. También hay índices alternos de 418 con valores distintos a la variante 0, como Reimu e Iku. Por eso el port debe consultar los datos del personaje/acción y no fijar una constante global.

El ejecutable local está fijado por SHA-256 `f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e`. El slot 20 de cada vtable de personaje (`handleInputs`, según `local/SokuLib/src/Player.cpp`) se extrajo directamente del PE y quedó registrado en `artifacts/kernel/<sha>/character-input/vtable-handlers.tsv`: 20/20 objetivos son únicos y están dentro del rango de código. Reimu `004ae670`, Cirno `006fb8b0` y Remilia `0059c010` coinciden con las referencias conocidas. Las 20 vtables usan el slot 21 compartido `00487020` (`checkAllMotionInputs`). Namazu se excluyó porque no es parte del roster jugable de 20 personajes de la demo. El extractor reproducible es `tools/extract_character_handlers.py`; valida el hash y esas direcciones ancla.

## Alcance de la evidencia

El TSV demuestra contenido y locks empaquetados en los PAT, no que todos los handlers originales usen la misma transición. Ghidra confirma dash→408/418 para Reimu y Cirno; los otros personajes necesitan sus handlers o trazas propias. Remilia necesita una ruta separada porque no tiene esos IDs explícitos. La prueba guest que compara borde y borde+1 con locks PAT reales pasa para Reimu y Cirno en Vita3K; no se extrapola al roster.

## Reproducción y pruebas

```powershell
python tools/summarize_dash_dispatch.py artifacts/pat-detail.tsv docs/DASH_DISPATCH_COVERAGE.md
python -m unittest tests/test_dash_dispatch_summary.py
```

Ambos comandos se ejecutaron correctamente. VPK guest vigente: [Touhou123Vita-real-locks.vpk](../artifacts/Touhou123Vita-real-locks.vpk), SHA-256 `cbc8c8c098f55f2d892ad48158dad7724c15c784c260471d4497831ac383633b`; Vita3K pasó 600 frames y su probe PAT real.

## Siguiente

Desensamblar los 20 handlers desde sus entradas recuperadas, primero buscando bloques de transición desde el state 200, llamadas a `getMoveLock` (`00489610`) y dispatch a IDs PAT; guardar funciones/CFG y cobertura por función con el hash. Contrastar Remilia 2C (412, `ACTION_2C`) por su posible creación de objetos ya que el PAT marca daño/flags sin hitbox explícita. Crear vectores por frame antes de implementar. El mapa de vtables solo descubre entradas virtuales; no demuestra transiciones ni justifica generalizar handlers.

El extractor se probó con `python -m unittest tests.test_character_handlers tests.test_dash_dispatch_summary` (3 pruebas aprobadas); `git diff --check` sin errores.
