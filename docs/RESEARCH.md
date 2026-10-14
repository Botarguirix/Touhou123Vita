# Investigación de fuentes

Consulta: 2026-10-13. Se revisaron fuentes primarias y se descargaron herramientas/código de referencia para inspección local.

| Fuente | Aporta | Limitación |
|---|---|---|
| [SokuDev/SokuLib](https://github.com/SokuDev/SokuLib) | Clases, estructuras, vtables y direcciones de funciones recuperadas | Biblioteca de modding Windows/x86; no motor autónomo ni port ARM |
| [SokuDev/SokuMods](https://github.com/SokuDev/SokuMods) | Hooks y ejemplos de uso del motor, práctica y modificaciones | Depende del ejecutable original |
| [enebe-nb/shady-packer](https://github.com/enebe-nb/shady-packer) | Extracción de paquetes y conversión de imágenes/paletas/audio/esquemas | Manipula datos; no reconstruye combate |
| [andry-dev/th123toolkit](https://github.com/andry-dev/th123toolkit) | Herramientas CV0/CV1/CV2/CV3/DAT | La palabra decompilar aquí incluye formatos de recursos, no todo el motor |
| [Hagb/giuroll-hagb](https://github.com/Hagb/giuroll-hagb) | Referencia de rollback y estado de partidas | Mod; netplay queda para una fase posterior |
| [VitaSDK samples](https://github.com/vitasdk/samples) | Toolchain, creación SELF/VPK y APIs de plataforma | Ejemplos; no capa Windows ni emulador x86 |
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Análisis PE/x86, referencias y pseudocódigo | Requiere revisión y validación de cada función |

No se encontró una decompilación completa, verificada y recompilable de Touhou 12.3 entre estas referencias. Esto no prueba que no exista otra; sí impide tratar SokuLib o un toolkit de assets como código fuente completo del juego.

Referencias locales fijadas:

- SokuLib: `0794becf1f578b32329604483be2112fe0afd4ee`.
- Shady Packer fuente: `0f223b68c3c00ef8635fdd016c08a959484c2017`.
- Shady Packer ejecutable descargado: release `v2.11`, `Release.zip`.
- Ghidra instalado: `12.1.4_PUBLIC`, con JDK `21.0.12.1+1`.

Se confirmó extracción local mediante `shady-cli pack -m dir`. `convert` interpreta `.dat` como recurso de interfaz, por lo que no es el comando para descomprimir un paquete. Algunas invocaciones con rutas largas/paréntesis no dieron el resultado esperado; la copia local de `th123a.dat` permitió la extracción.
