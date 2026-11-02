# Auditoría de publicación alpha 0.1

Alcance: árbol de archivos versionados (`git ls-files`), incluidos los archivos
nuevos del PR. No se añaden archivos de `artifacts/`, `original/` o `local/`.
Los cuatro commits de main aún no publicados que anteceden a esta rama son
`3fbe061`, `ce1a032`, `5e9f9c9` y `e9ad62d`; también quedan en la historia de la
rama propuesta. Este PR no modifica sus fuentes `recomp/`.

Se revisaron los dos PNG:

- `docs/img/controls.png`: ilustración propia exportada del SVG; sin logotipos,
  imágenes ni recursos del juego. Texto rasterizado con fuente del sistema;
  no se incorpora el archivo de fuente.
- `docs/images/h1-vita3k-boot.png`: pantalla de diagnóstico H1 generada por el
  proyecto, revisada visualmente; solo texto del runtime, sin arte del juego.
  Se conserva como evidencia histórica. No es una captura de gameplay.

Los Markdown `docs/TESTING.md` y `docs/TOUHOU75_REUSE_REVIEW.md` son UTF-8
válido con 1 y 4 NUL literales preexistentes dentro de números hexadecimales.
Se revisaron esos fragmentos: errores tipográficos de documentación propia,
no recursos binarios. No se modificaron en este PR.

No hay archivos mayores de 1.000.000 bytes; no se necesitan excepciones.
La inspección de nombres/tamaños no sustituye una auditoría de autoría histórica:
los directorios de dependencias solo contienen recetas/pruebas propias y sus
fuentes y binarios descargados permanecen ignorados. No se incorporó código
comercial ni fuentes generados para esta publicación.

## Script reproducible

Desde la raíz del worktree, este script examina los archivos que `git ls-files`
realmente enumera. No extrae recursos ni lee los archivos locales ignorados.
La salida detallada JSON permanece en artifacts. Debe ejecutarse tras `git add`.

```python
"""Read-only publication audit of the git index, not ignored local assets."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
paths=[p for p in subprocess.check_output(['git','ls-files','-z']).decode('utf-8').split('\0') if p]
forbidden=[];large=[];unknown_binary=[]
owned_images={'docs/images/h1-vita3k-boot.png':'project-authored H1 diagnostic screen, visually reviewed; no game artwork', 'docs/img/controls.png':'original generic controller drawing exported from own SVG'}
owned_text={'docs/TESTING.md':1,'docs/TOUHOU75_REUSE_REVIEW.md':4}
reviewed_text=[]
for name in paths:
 p=Path(name);base=p.name.lower();ext=p.suffix.lower();data=p.read_bytes()
 if name.split('/')[0] in ('artifacts','original','local') or re.fullmatch(r'th123\.exe|th(?:123|105).*\.dat|th123e\.(?:dat|dll|exe|cache)|eboot\.bin',base) or ext in ('.vpk','.exe','.dll','.dat','.cache','.ttf','.otf','.a','.lib','.so','.o','.elf','.velf','.self','.bin','.cv0','.cv1','.cv2','.pat','.rgba','.ogg','.wav') or re.fullmatch(r'(?:unit_\d+|guest_[0-9a-f]{4,})\.c',base):forbidden.append(name)
 if len(data)>1000000:large.append(dict(path=name,bytes=len(data)))
 if b'\x00' in data and name not in owned_images:
  if name in owned_text and data.count(b'\x00')==owned_text[name]:
   data.decode('utf-8',errors='strict');reviewed_text.append(name)
  else:unknown_binary.append(name)
result=dict(tracked_files=len(paths),forbidden=forbidden,over_1mb_without_justification=large,unreviewed_binary=unknown_binary,owned_images={k:v for k,v in sorted(owned_images.items()) if k in paths})
Path('artifacts/release-0.1-audit.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print('git ls-files: '+str(len(paths))+' tracked files')
print('Forbidden paths/assets: '+str(len(forbidden)))
print('Files > 1,000,000 bytes without justification: '+str(len(large)))
print('Unreviewed binary files: '+str(len(unknown_binary)))
for k,v in sorted(result['owned_images'].items()):print('Own image: '+k+' - '+v)
if forbidden or large or unknown_binary:
 print(json.dumps(result,indent=2));sys.exit(1)
for name in reviewed_text:print('Own UTF-8 document with reviewed pre-existing NUL typo: '+name)
print('PASS: source-only publication audit')
```

## Verificación

Antes: `python -m unittest discover -s tests` (GCC UCRT64 en PATH):
`Ran 222 tests in 558.176s` / `OK`.

Después: `python -m unittest discover -s tests`: `Ran 222 tests in 483.293s` / `OK`.

No se ejecutó una
compilación de juego/VPK ni se probó hardware en esta tarea. Los comandos de
build se comprobaron contra los scripts; se comprobaron enlaces relativos y
la copia íntegra del roadmap histórico (normalizando finales de línea).

Se preparará un PR hacia main. No se hará merge, tag ni release sin aprobación
del usuario en el chat. No se publica el VPK; las notas proponen un release sin
adjuntos, solo los archivos de fuentes automáticos de GitHub.

Salida literal final de la auditoría (antes del push):

```text
git ls-files: 612 tracked files
Forbidden paths/assets: 0
Files > 1,000,000 bytes without justification: 0
Unreviewed binary files: 0
PASS: source-only publication audit
```
