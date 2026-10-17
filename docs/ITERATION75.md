# Iteración 1.75: datos de ataque PAT del objeto 808

El extractor de acción ahora conserva, por cada pose, daño, chip, stun y las listas separadas de cajas de colisión, hurt y ataque. El test del probe compara estos campos contra el PAT prioritario de Suwako en `th123c.dat`, hash `1e7e06920e9a7a0e8b0ee0fc160a5b2dd3a19f2cdba2ba8144ab969d0a9dc906`.

Acción 808/seq.0: los diez frames tienen daño 100, una caja hurt `[-44,-44,44,44]` y una caja attack `[-32,-32,32,32]`; no hay cajas en la lista collision. Seq.1: el único frame declara daño 150, pero no contiene cajas collision, hurt ni attack en el PAT. Por eso no se puede inferir que el proyectil hijo cause 150 de daño. La hipótesis de que `00438fc0` aplique bounds al handler actual queda retirada: la Iteración 1.76 recorre su CFG desde el handler verificado `0x788d3e` y demuestra que ese adaptador no es alcanzable en esa ruta.

Se extendió el factory probe para guardar EAX del dispatcher y se ejecutó durante 40 callbacks. Secuencia 1 llega a alpha 7; el callback siguiente toma la rama `alpha < 8` y ejecuta el epílogo común que decrementa el entero bruto `object+0x34c` de 1 a 0. El constructor base lo inicializa en 1. El significado de ese campo y la eliminación del nodo deben verificarse siguiendo el update de la lista/manager; las llamadas posteriores del probe, hechas a la fuerza, lo subdesbordan y no son comportamiento del engine. La corrida usa servicios controlados y no establece daño ni contacto.

Las pruebas enfocadas de la factory y parser comprueban hash, loops, duraciones, daño y cajas PAT. Reporte de 40 ticks: `artifacts/x86-suwako-808-factory-probe.json`. El motor Vita no cambió y no se generó un VPK.

## Próximo gate

1. Seguir cómo serializa el loader `004679e0` las tres listas de cajas y cómo las consulta la rutina de colisión asociada al objeto.
2. Resolver la ruta de impacto del hijo seq.1; el adaptador `00438fc0` no pertenece al CFG confirmado de 808. No aplicar daño PAT sin ese contrato.
3. Seguir `object+0x34c`, el iterador de `GameObjectList` y su llamada de update para probar el borrado/reuso del slot.
4. Una vez cerrados spawn→update→hit/delete, portar ese ciclo a C y crear un VPK de regresión Vita3K.
