/* Solo simbolos ajenos al allocator; support.c y guest.c son los reales. */
#include "win32.h"
#include <stdio.h>
#include <stdlib.h>
const ApiEntry win32_threads[]={{NULL,NULL}};
const ApiEntry win32_d3d9[]={{NULL,NULL}};
const ApiEntry win32_media[]={{NULL,NULL}};
const ApiEntry win32_kernel32[]={{NULL,NULL}};
const ApiEntry win32_other[]={{NULL,NULL}};
void platform_log(const char *line) { (void)line; }
_Noreturn void host_exit(Cpu *c,uint32_t code,const char *why) {
    (void)c;fprintf(stderr,"unexpected host_exit %u: %s\n",code,why);exit(2);
}
