# Iteración 1.97: despacho dinámico del initializer de Remilia 412

Se amplió `tools/x86_remilia_412_initializer_probe.py`: ahora comienza en el selector original `0x59ab40`, coloca action 412 en EAX y ejecuta el mapa de grupos y el jump table del PE, en vez de entrar directamente al cuerpo `0x59ad64`. Un hook de instrucción confirma que se alcanzó ese destino exactamente una vez. Después corre el helper original `0x4636b0` y se verifican de nuevo los resets de estado, counters y movimiento.

El resultado reproducible está en `artifacts/kernel/remilia-412-initializer.json`: action 412 → índice 195 → grupo 15 → `0x59ad64`; se alcanzó el destino, y todos los campos centinela previstos quedaron en cero. Esto confirma el despacho y efecto del initializer; aún no ejecuta el setter público que cambia la acción desde el handler de input, el update completo, la fábrica de objetos ni un impacto.

Siguiente: seguir los callers del selector y ejecutar la transición real desde la ruta de input de Remilia, conservando sus virtual calls y detectando cualquier factory/manager alcanzado. La ruta de colisión normal ya dio cero para la pose 412 analizada, por lo que la investigación sigue buscando el productor real del contacto/daño. Ver [ITERATION94.md](ITERATION94.md), [ITERATION95.md](ITERATION95.md) y [ITERATION96.md](ITERATION96.md).
