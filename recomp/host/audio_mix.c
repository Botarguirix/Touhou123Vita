#include "audio_mix.h"
#include <math.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
uint64_t platform_ticks_us(void);

struct AudioVoice {
    struct AudioVoice *next;
    const uint8_t *pcm;
    uint32_t bytes, count, rate, frequency, stride;
    int channels, bits, playing, looping;
    int32_t volume, pan;
    double position, left, right;
    uint32_t gen; /* bumped when the game plays, stops or moves the voice */
};
static AudioVoice *voices;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t mix_done = PTHREAD_COND_INITIALIZER;
static int mixing; /* audio_mix is reading PCM outside the lock */
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
    while (mixing) pthread_cond_wait(&mix_done, &mutex); /* the caller frees the PCM next */
    AudioVoice **p = &voices;
    while (*p && *p != v) p = &(*p)->next;
    if (*p) { *p = v->next; free(v); }
    pthread_mutex_unlock(&mutex);
}
uint64_t audio_play_wait_max, audio_play_wait_sum, audio_play_calls; /* lock wait in Play (us) */
void audio_voice_play(AudioVoice *v, int looping) {
    if (!v) return;
    uint64_t t0 = platform_ticks_us();
    pthread_mutex_lock(&mutex);
    uint64_t w = platform_ticks_us() - t0;
    audio_play_calls++; audio_play_wait_sum += w;
    if (w > audio_play_wait_max) audio_play_wait_max = w;
    if (v->position >= v->count) v->position = 0;
    v->looping = !!looping; v->playing = 1; v->gen++;
    pthread_mutex_unlock(&mutex);
}
void audio_voice_stop(AudioVoice *v) {
    if (!v) return;
    pthread_mutex_lock(&mutex); v->playing = 0; v->gen++; pthread_mutex_unlock(&mutex);
}
void audio_voice_set_position(AudioVoice *v, uint32_t offset) {
    if (!v) return;
    pthread_mutex_lock(&mutex);
    /* Alineación a muestra inferior; offsets fuera del buffer vuelven al inicio. */
    v->position = offset < v->bytes ? offset / v->stride : 0;
    v->gen++;
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
/* Overload limiter: while the sum of the voices fits in 16 bits nothing is touched
 * (gain 1.0, bit-exact). When it would not fit, the gain drops at once so the peak
 * lands on full scale and recovers over ~50 ms, instead of cutting the waveform flat,
 * which is what made loud music plus a sound effect sound harsh and "saturated". */
static AudioStats stats;
static double limiter_gain = 1.0;
static int16_t saturate(double x) {
    if (x >= 32767) return 32767;
    if (x <= -32768) return -32768;
    return (int16_t)lround(x);
}
void audio_advance(uint32_t frames, uint32_t out_rate) {
    if (!out_rate) return;
    pthread_mutex_lock(&mutex);
    for (AudioVoice *v = voices; v; v = v->next) {
        if (!v->playing) continue;
        v->position += (double)frames * (double)v->frequency / out_rate;
        if (v->position >= v->count) {
            if (v->looping) v->position = fmod(v->position, v->count);
            else { v->position = v->count; v->playing = 0; }
        }
    }
    pthread_mutex_unlock(&mutex);
}
void audio_mix_stats(AudioStats *out) {
    pthread_mutex_lock(&mutex);
    if (out) *out = stats;
    stats = (AudioStats){0};
    pthread_mutex_unlock(&mutex);
}
/* The mix runs WITHOUT the lock. Holding it for a whole period (5-7 ms of every 21 ms on
 * the Vita, measured) blocked every DirectSound call of the game thread behind it:
 * IDirectSoundBuffer8::Play averaged 10 ms per call in a fight. Now the playing voices
 * are copied under the lock, mixed (voice by voice, in float) outside it, and their new
 * positions written back under the lock unless the game moved them meanwhile (gen).
 * audio_voice_free waits for a running mix, so the PCM it reads stays allocated. */
enum { MAX_MIX_VOICES = 64, MAX_FRAMES = 4096 };
typedef struct {
    AudioVoice *v;
    const uint8_t *pcm;
    uint32_t count, stride, gen;
    int channels, bits, looping, ended;
    double pos, step;
    float l, r;
} Snap;

static int16_t read_sample(const Snap *s, uint32_t frame, unsigned channel) {
    const uint8_t *p = s->pcm + frame * s->stride + (s->channels == 2 ? channel : 0) * (uint32_t)(s->bits / 8);
    if (s->bits == 8) return (int16_t)(((int)p[0] - 128) * 256);
    return (int16_t)(uint16_t)(p[0] | (p[1] << 8));
}

static void mix_voice(Snap *s, float *acc, uint32_t frames) {
    double pos = s->pos;
    for (uint32_t f = 0; f < frames; ++f) {
        uint32_t a = (uint32_t)pos, b = a + 1;
        if (b >= s->count) b = s->looping ? 0 : a;
        float t = (float)(pos - a);
        float l0 = read_sample(s, a, 0), l1 = read_sample(s, b, 0);
        float r0 = s->channels == 2 ? read_sample(s, a, 1) : l0, r1 = s->channels == 2 ? read_sample(s, b, 1) : l1;
        acc[2 * f] += (l0 + (l1 - l0) * t) * s->l;
        acc[2 * f + 1] += (r0 + (r1 - r0) * t) * s->r;
        pos += s->step;
        if (pos >= s->count) {
            if (s->looping) pos = fmod(pos, s->count);
            else { pos = s->count; s->ended = 1; break; }
        }
    }
    s->pos = pos;
}

void audio_mix(int16_t *out, uint32_t frames, uint32_t out_rate) {
    if (!out) return;
    if (frames > MAX_FRAMES) frames = MAX_FRAMES;
    static Snap snaps[MAX_MIX_VOICES];
    static float acc[MAX_FRAMES * 2];
    unsigned n = 0;
    pthread_mutex_lock(&mutex);
    if (out_rate)
        for (AudioVoice *v = voices; v && n < MAX_MIX_VOICES; v = v->next) {
            if (!v->playing || !v->count) continue;
            snaps[n++] = (Snap){v, v->pcm, v->count, v->stride, v->gen, v->channels, v->bits, v->looping, 0,
                                v->position, (double)v->frequency / out_rate, (float)v->left, (float)v->right};
        }
    mixing = 1;
    pthread_mutex_unlock(&mutex);

    memset(acc, 0, sizeof(float) * 2 * frames);
    for (unsigned i = 0; i < n; i++) mix_voice(&snaps[i], acc, frames);

    AudioStats local = {0};
    local.max_voices = (int)n;
    for (uint32_t f = 0; f < frames; ++f) {
        double l = acc[2 * f], r = acc[2 * f + 1];
        double pk = fabs(l) > fabs(r) ? fabs(l) : fabs(r);
        if (n) {
            local.frames++;
            if (pk > 32768.0) local.clipped++; /* the sum alone does not fit in 16 bits */
            if (limiter_gain < 0.999) local.limited++;
            if (pk > local.peak) local.peak = pk > 2000000.0 ? 2000000 : (int)pk;
        }
        limiter_gain += (1.0 - limiter_gain) * 0.0004; /* release */
        if (pk * limiter_gain > 32768.0) limiter_gain = 32768.0 / pk; /* attack: at once */
        out[(size_t)f * 2] = saturate(l * limiter_gain);
        out[(size_t)f * 2 + 1] = saturate(r * limiter_gain);
    }

    pthread_mutex_lock(&mutex);
    for (unsigned i = 0; i < n; i++) {
        AudioVoice *v = snaps[i].v;
        if (v->gen != snaps[i].gen) continue; /* played/stopped/moved by the game meanwhile */
        v->position = snaps[i].pos;
        if (snaps[i].ended) v->playing = 0;
    }
    if (local.max_voices > stats.max_voices) stats.max_voices = local.max_voices;
    stats.frames += local.frames; stats.clipped += local.clipped; stats.limited += local.limited;
    if (local.peak > stats.peak) stats.peak = local.peak;
    mixing = 0;
    pthread_cond_broadcast(&mix_done);
    pthread_mutex_unlock(&mutex);
}
