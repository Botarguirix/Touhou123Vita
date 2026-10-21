# Iteración 2.179: inventario de las tres campañas Story del DAT 12.3

Se recorrieron los `story.csv` presentes bajo `artifacts/extracted/data/csv`. El manifiesto/index del `th123a.dat` contiene los tres recursos: `chirno/story.cv1`, `meirin/story.cv1` y `sanae/story.cv1`. Cada tabla tiene cinco stages numerados 0–4 (15 enfrentamientos):

| Campaña | Rivales por stage 0–4 |
|---|---|
| Cirno | Sanae, Meiling, Marisa, Utsuho, Alice |
| Meiling | Patchouli, Alice, Marisa, Reimu, Namazu |
| Sanae | Cirno, Meiling, Reimu, Utsuho, Suwako |

Namazu aparece una sola vez en estas tablas: final de Meiling, stage 4, con cinco cartas y variante 3. Es la ruta de contenido concreta para probarlo como rival Story y mantiene separado su acceso de la selección regular de personajes. El parser PE `0x432bb0` carga los `story.csv` por nombre de personaje; falta seleccionar dinámicamente Meiling/stage 4, comprobar qué registro se entrega al constructor `0x45ef50` y ejecutar el combate original o un harness fiel.

La regresión `tests/test_story_namazu_source.py` valida las 15 entradas, los tres recursos en el manifiesto, la fila especial, el enum 21 y los flujos PE de loader/factory. Sin cambio runtime/VPK; fuente de tablas: DAT local del usuario y su extracción de trabajo.
