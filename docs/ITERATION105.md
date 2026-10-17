# Iteración 2.05: imports del CRT y límite del fixture para Remilia 801

El harness modela imports Windows usados por la ruta 801 y registra su nombre, retorno y argumentos. La primera ejecución dejaba el índice TLS del CRT en `0xffffffff`, pues el proceso PE no había pasado por su inicializador. El stub `0x47dcb0` también se retiró: recibía `ECX=2` desde la ruta de error y no representaba una limpieza de lista del objeto.

La continuación y el diagnóstico se documentan en [ITERATION106.md](ITERATION106.md). El objetivo de esta nota es conservar la evidencia de la hipótesis inicial que resultó incorrecta.
