# Limpieza y conservación de artefactos

`artifacts/` es una carpeta local ignorada por Git. Contiene entradas de usuario (datos de juego), salidas reproducibles y evidencia de análisis; no se debe vaciar completa.

- **Conservar como builds para probar:** `Touhou123Vita-current.vpk` (interactivo) y `Touhou123Vita-current-auto.vpk` (regresión automatizada). Los scripts de build los regeneran.
- **Conservar como evidencia:** `kernel/`, `ghidra/`, `ghidra-input-state/`, `extracted/`, `vanilla-decoded/`, manifests, TSV/JSON de probes y reportes citados en `docs/ITERATION*.md` o `docs/STATUS.md`.
- **Regenerables:** directorios `manual-vita-*`, `continuation-build*`, logs de Vita3K, capturas y `vitafs/`. Mantener el VitaFS activo mientras se usa el runner; `tools/vita3k-test.ps1` actualiza sus capturas/reportes y limpia los respaldos `.previous` de corridas anteriores.
- **VPK experimentales:** son pequeños, pero algunos representan el único resultado de una prueba. No se borran por defecto.

Previsualizar limpieza de respaldos viejos:

```powershell
.\tools\cleanup-artifacts.ps1
```

Moverlos a cuarentena reversible:

```powershell
.\tools\cleanup-artifacts.ps1 -Apply
```

Previsualizar además VPK históricas que no coincidan con nombres protegidos y enviar esa selección a cuarentena solo tras revisar la lista:

```powershell
.\tools\cleanup-artifacts.ps1 -IncludeExperimentalVpk
.\tools\cleanup-artifacts.ps1 -IncludeExperimentalVpk -Apply
```

La cuarentena está en `artifacts/_quarantine/`; el script nunca elimina archivos permanentemente y se restringe a `artifacts/`.
