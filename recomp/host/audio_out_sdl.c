/* PC audio output: SDL2 pulls the DirectSound mix (audio_mix.c) at 48 kHz stereo. */
#define SDL_MAIN_HANDLED
#include <SDL2/SDL.h>

#include <stdio.h>
#include <stdlib.h>

#include "audio_mix.h"
#include "win32.h"

enum { OUT_RATE = 48000 };

/* T123_AUDIO_DUMP=<file.wav>: also writes the first 60 s of the mix there (checks). */
static FILE *dump;
static uint32_t dumped;

static void callback(void *user, Uint8 *stream, int len) {
    (void)user;
    audio_mix((int16_t *)stream, (uint32_t)len / 4, OUT_RATE);
    if (dump && dumped < OUT_RATE * 4u * 60u) {
        fwrite(stream, 1, (size_t)len, dump);
        dumped += (uint32_t)len;
        if (dumped >= OUT_RATE * 4u * 60u) {
            uint32_t header[11] = {0x46464952u, 36 + dumped, 0x45564157u, 0x20746d66u, 16, 0x00020001u,
                                   OUT_RATE, OUT_RATE * 4u, 0x00100004u, 0x61746164u, dumped};
            fseek(dump, 0, SEEK_SET);
            fwrite(header, 4, 11, dump);
            fclose(dump);
            dump = NULL;
        }
    }
}

void audio_out_start(void) {
    static int started;
    if (started++)
        return;
    if (SDL_InitSubSystem(SDL_INIT_AUDIO)) {
        trace("# audio: SDL audio unavailable: %s", SDL_GetError());
        return;
    }
    SDL_AudioSpec want = {0}, have;
    want.freq = OUT_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    want.callback = callback;
    SDL_AudioDeviceID dev = SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    if (!dev) {
        trace("# audio: cannot open the output: %s", SDL_GetError());
        return;
    }
    trace("# audio: SDL output %d Hz, %d channels, %d frames per period", have.freq, have.channels, have.samples);
    const char *path = getenv("T123_AUDIO_DUMP");
    if (path && (dump = fopen(path, "wb"))) {
        static const uint8_t blank[44];
        fwrite(blank, 1, sizeof blank, dump); /* header written when the minute is complete */
    }
    SDL_PauseAudioDevice(dev, 0);
}
