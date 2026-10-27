/* Vita audio output: one thread mixes the DirectSound voices (audio_mix.c) and hands
 * 1024-frame periods to the main audio port; sceAudioOutOutput blocks until the port
 * can take the next one, which paces the mixing. */
#include <psp2/audioout.h>
#include <pthread.h>

#include "../host/audio_mix.h"
#include "../host/win32.h"

enum { OUT_RATE = 48000, PERIOD = 1024 };

static void *audio_thread(void *arg) {
    int port = (int)(intptr_t)arg;
    static int16_t mix[2][PERIOD * 2];
    for (unsigned k = 0;; k ^= 1) {
        audio_mix(mix[k], PERIOD, OUT_RATE);
        sceAudioOutOutput(port, mix[k]);
    }
    return NULL;
}

void audio_out_start(void) {
    static int started;
    if (started++)
        return;
    int port = sceAudioOutOpenPort(SCE_AUDIO_OUT_PORT_TYPE_MAIN, PERIOD, OUT_RATE, SCE_AUDIO_OUT_MODE_STEREO);
    if (port < 0) {
        trace("# audio: sceAudioOutOpenPort failed (%08x)", (unsigned)port);
        return;
    }
    pthread_t id;
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, 64 * 1024);
    if (pthread_create(&id, &attr, audio_thread, (void *)(intptr_t)port))
        trace("# audio: cannot start the audio thread");
    else
        trace("# audio: Vita output %d Hz stereo, %d frames per period", OUT_RATE, PERIOD);
    pthread_attr_destroy(&attr);
}
