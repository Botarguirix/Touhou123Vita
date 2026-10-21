# Iteración 2.165: análisis inicial del autociclo PAT96 (corregido en 2.166)

**Corrección, Iteración 2.166:** la reutilización de seq0 no es exclusiva de la fixture. El análisis de `PlayerPattern` (`0x4679e0`) confirma que el loader original inicializa el único nodo como `next=0`, `prev=self`; véase [ITERATION266.md](ITERATION266.md). El fixture reproduce esos enlaces para el caso singleton. La incertidumbre pasa a ser qué significado de gameplay tiene ese índice compartiendo frames, no si los frames vienen de otro nodo.

La descompilación existente de `0x4652a0` (manifest Ghidra `function 004652a0 ... true`, archivo `004652a0.c`) muestra que `setSequence(n)` parte del nodo de secuencia del action actual y sigue el puntero `+0x1c` exactamente `n` veces. Después toma el rango de frames del nodo alcanzado.

El PAT efectivo real extraído para Suika action96 contiene un solo nodo: seq0, diez frames. La fixture actual construye los enlaces `+0x18` y `+0x1c` como anillo; para una sola secuencia ambos apuntan a sí mismo. Por eso cuando el updater compartido action96/97 solicita seq3 en `0x4851e7`, la fixture sí actualiza el identificador a 3, pero `setSequence` camina tres veces al mismo nodo y reutiliza el payload gráfico de seq0. Los índices seq1/3 observados son estado PE real; sus frames no son evidencia válida de que la fixture contenga el PAT original para esas secuencias.

En Iteración 2.165 se dejó como pendiente la verificación de los enlaces del loader. La Iteración 2.166 resuelve esa duda mediante el código Ghidra y bytes del PE: la fixture de nodo único coincide con la inicialización original. Sigue pendiente validar la semántica gameplay del índice de secuencia 3 y su salida natural.

Sin cambios al runtime Vita ni VPK.
