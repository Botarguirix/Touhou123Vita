# Iteración 2.00: aceptación/rechazo diferencial en el gate 2C

La sonda de la Iteración 1.99 ahora corre dos fixtures sobre el mismo fragmento original desde `0x59dd97`, justo antes de `moveLock(412)`:

- Lock 0, comparación `BX=0`: `0x489610` recibe 412 y retorna 0; la comparación deja pasar, llama al setter y alcanza action 412 / seq.0 / pose 0 / 12 poses PAT.
- Lock 0, comparación `BX=1`: el condicional rechaza 412 y la ruta consulta moveLock(410); no alcanza el setter 412 y el action permanece 0 en el objeto controlado.

Ambos casos se ejecutan con el helper original de moveLock, setter/reset/initializer originales y fixtures de mapas controlados. El segundo caso demuestra el borde rechazo del compare, además del éxito anterior. Reporte actualizado: `artifacts/kernel/remilia-412-input-gate.json` (ignorado).

Alcance: el punto de entrada ya está dentro de una rama de handler y omite sus guards anteriores de estado, movimiento y recurso; la comparación BX se fija en el fixture. El lookup asociativo de PAT y la callback pose/render son controlados. No demuestra input natural, update por frame, colisión, daño ni combate. Próximo: alimentar el handler desde su entrada y resolver los servicios necesarios, o instrumentar el update dinámico tras 412; continuar hasta detectar el primer objeto/contacto que explique el daño de PAT 750. Ver [ITERATION98.md](ITERATION98.md) y [ITERATION99.md](ITERATION99.md).
