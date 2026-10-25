#include "audio_mix.h"
#include <math.h>
#include <pthread.h>
#include <stdlib.h>

struct AudioVoice {
    struct AudioVoice *next;
    const uint8_t *pcm;
    uint32_t bytes, count, rate, frequency, stride;
    int channels, bits, playing, looping;
    int32_t volume, pan;
    double position, left, right;
};
static AudioVoice *voices;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static int32_t clamp(int32_t n, int32_t lo, int32_t hi) {
    return n < lo ? lo : n > hi ? hi : n;
}
static double gain(int32_t cb) {
    /* DirectSound define -10000 como silencio, no una señal residual. */
    return cb <= -10000 ? 0.0 : pow(10.0, cb / 2000.0);
}
static void gains(AudioVoice *v) {
    double g = gain(v->volume);
    v->left = g * gain(v->pan > 0 ? -v->pan : 0);
    v->right = g * gain(v->pan < 0 ? v->pan : 0);
}
AudioVoice *audio_voice_new(const uint8_t *pcm, uint32_t bytes, uint32_t rate, int channels, int bits) {
    if (!pcm || !rate || (channels != 1 && channels != 2) || (bits != 8 && bits != 16)) return NULL;
    uint32_t stride = (uint32_t)channels * (uint32_t)(bits / 8);
    if (!bytes || bytes % stride) return NULL;
    AudioVoice *v = calloc(1, sizeof *v);
    if (!v) return NULL;
    v->pcm = pcm; v->bytes = bytes; v->count = bytes / stride;
    v->rate = v->frequency = rate; v->stride = stride;
    v->channels = channels; v->bits = bits; gains(v);
    pthread_mutex_lock(&mutex); v->next = voices; voices = v; pthread_mutex_unlock(&mutex);
    return v;
}
void audio_voice_free(AudioVoice *v) {
    if (!v) return;
    pthread_mutex_lock(&mutex);
    AudioVoice **p = &voices;
    while (*p && *p != v) p = &(*p)->next;
    if (*p) { *p = v->next; free(v); }
    pthread_mutex_unlock(&mutex);
}
void audio_voice_play(AudioVoice *v, int looping) {
    if (!v) return;
    pthread_mutex_lock(&mutex);
    if (v->position >= v->count) v->position = 0;
    v->looping = !!looping; v->playing = 1;
    pthread_mutex_unlock(&mutex);
}
void audio_voice_stop(AudioVoice *v) {
    if (!v) return;
    pthread_mutex_lock(&mutex); v->playing = 0; pthread_mutex_unlock(&mutex);
}
void audio_voice_set_position(AudioVoice *v, uint32_t offset) {
    if (!v) return;
    pthread_mutex_lock(&mutex);
    /* Alineación a muestra inferior; offsets fuera del buffer vuelven al inicio. */
    v->position = offset < v->bytes ? offset / v->stride : 0;
    pthread_mutex_unlock(&mutex);
}
void audio_voice_set_volume(AudioVoice *v, int32_t cb) {
    if (!v) return;
    pthread_mutex_lock(&mutex); v->volume = clamp(cb, -10000, 0); gains(v); pthread_mutex_unlock(&mutex);
}
void audio_voice_set_pan(AudioVoice *v, int32_t cb) {
    if (!v) return;
    pthread_mutex_lock(&mutex); v->pan = clamp(cb, -10000, 10000); gains(v); pthread_mutex_unlock(&mutex);
}
void audio_voice_set_frequency(AudioVoice *v, uint32_t hz) {
    if (!v) return;
    pthread_mutex_lock(&mutex); v->frequency = hz ? hz : v->rate; pthread_mutex_unlock(&mutex);
}
void audio_voice_position(const AudioVoice *v, uint32_t *play, uint32_t *write) {
    pthread_mutex_lock(&mutex);
    uint32_t pos = v ? (v->position >= v->count ? v->bytes : (uint32_t)v->position * v->stride) : 0;
    if (play) *play = pos;
    if (write) *write = pos;
    pthread_mutex_unlock(&mutex);
}
int audio_voice_playing(const AudioVoice *v) {
    pthread_mutex_lock(&mutex); int active = v && v->playing; pthread_mutex_unlock(&mutex); return active;
}
static double sample(const AudioVoice *v, uint32_t frame, unsigned channel) {
    uint32_t offset = frame * v->stride + (v->channels == 2 ? channel : 0) * (uint32_t)(v->bits / 8);
    const uint8_t *p = v->pcm + offset;
    if (v->bits == 8) return ((int)p[0] - 128) * 256;
    /* LE explícito, sin acceso desalineado ni conversión unsigned->signed fuera de rango. */
    int x = p[0] | ((int)p[1] << 8);
    return x >= 32768 ? x - 65536 : x;
}
static int16_t saturate(double x) {
    if (x >= 32767) return 32767;
    if (x <= -32768) return -32768;
    return (int16_t)lround(x);
}
void audio_mix(int16_t *out, uint32_t frames, uint32_t out_rate) {
    if (!out) return;
    pthread_mutex_lock(&mutex);
    for (uint32_t f = 0; f < frames; ++f) {
        double l = 0, r = 0;
        if (out_rate) for (AudioVoice *v = voices; v; v = v->next) {
            if (!v->playing) continue;
            uint32_t a = (uint32_t)v->position, b = a + 1;
            if (b == v->count) b = v->looping ? 0 : a;
            double t = v->position - a;
            l += (sample(v, a, 0) * (1-t) + sample(v, b, 0) * t) * v->left;
            r += (sample(v, a, 1) * (1-t) + sample(v, b, 1) * t) * v->right;
            v->position += (double)v->frequency / out_rate;
            if (v->position >= v->count) {
                if (v->looping) v->position = fmod(v->position, v->count);
                else { v->position = v->count; v->playing = 0; }
            }
        }
        out[(size_t)f*2] = saturate(l); out[(size_t)f*2+1] = saturate(r);
    }
    pthread_mutex_unlock(&mutex);
}
