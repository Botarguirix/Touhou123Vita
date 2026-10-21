# Iteración 2.163: la única referencia alcanzable a `+0x884` es un reset a cero

Se amplió el escaneo del vtable de Suika a un call graph de llamadas directas. Desde sus 25 entradas ejecutables se alcanzan 392 funciones y se decodifican 29.963 instrucciones. Aparece una referencia a `+0x884`: `0x48b15a: mov word ptr [esi+0x884], ax`, con cadena `slot17 0x608670 → call 0x48b000`.

El bloque `0x48b000` ejecuta `xor eax,eax` antes de borrar una gran región de campos Player; la escritura en `+0x884` y las contiguas `+0x886` y `+0x882` son ceros. Por tanto la referencia confirma inicialización/reset, no el valor positivo que consume action97. `0x608670` llama a ese helper y luego limpia más estado. El barrido lineal anterior lo omitía por el dispatch/entrelazado; el recorrido interprocedural lo recupera.

La sonda reutilizable `tools/scan_pe_vtable_callgraph_field.py` genera `artifacts/suika-field-884-callgraph.json` con el hash de PE, conteos, referencia y cadena de llamadas. Su test fija ese resultado. El escaneo sigue sin resolver tablas de saltos, llamadas virtuales/indirectas ni direcciones de campo calculadas, y no inspecciona managers ajenos al vtable; esos son los siguientes lugares de búsqueda.

La iteración no resuelve el productor positivo ni la semántica de action96. No cambia el runtime Vita ni genera VPK.
