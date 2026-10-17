#include <stdio.h>

int t123_resource_probe_main(int argc, char **argv);

int main(void) {
    char program[] = "resource_probe";
    char data_directory[] = "ux0:data/touhou123vita";
    char mode[] = "--pat-image-decode";
    char output[] = "ux0:data/touhou123vita-pat-image-decode.tsv";
    char *arguments[] = {program, data_directory, mode, output};
    return t123_resource_probe_main(4, arguments);
}
