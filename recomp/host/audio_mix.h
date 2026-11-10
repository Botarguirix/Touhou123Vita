#ifndef T123_AUDIO_MIX_H
#define T123_AUDIO_MIX_H
#include <stdint.h>
typedef struct AudioVoice AudioVoice;
/* PCM prestado: debe vivir hasta free. El host sincroniza Lock/Unlock y las
 * escrituras PCM contra audio_mix; este mutex protege voces, no memoria ajena.
 * Sin copia ni asignaciones en el callback. Enlazar pthread y libm. */
AudioVoice *audio_voice_new(const uint8_t *pcm, uint32_t bytes, uint32_t rate, int channels, int bits);
void audio_voice_free(AudioVoice *v);
void audio_voice_play(AudioVoice *v, int looping);
void audio_voice_stop(AudioVoice *v);
void audio_voice_set_position(AudioVoice *v, uint32_t byte_offset);
void audio_voice_set_volume(AudioVoice *v, int32_t centibels);
void audio_voice_set_pan(AudioVoice *v, int32_t centibels);
void audio_voice_set_frequency(AudioVoice *v, uint32_t hz);
/* write = play: no existe cola hardware en este mezclador. El host debe sumar
 * la latencia real de SDL/sceAudioOut si necesita un cursor de escritura seguro.
 * Al acabar sin bucle, play=write=bytes (fin, no una posición reproducible). */
void audio_voice_position(const AudioVoice *v, uint32_t *play, uint32_t *write);
int audio_voice_playing(const AudioVoice *v);
/* Salida estéreo S16; interpolación lineal, suma double y saturación final.
 * out_rate=0 produce silencio sin avanzar. No usar punteros tras free; el
 * propietario coordina la vida de cada handle con los demás hilos de control. */
void audio_mix(int16_t *out, uint32_t frames, uint32_t out_rate);
/* Diagnóstico de nivel desde la última lectura (se reinicia al leer): fotogramas
 * mezclados con alguna voz sonando, fotogramas con el limitador reduciendo la
 * ganancia (limited), fotogramas cuya suma no cabe en 16 bits (clipped), pico de la
 * suma antes de limitar y máximo de voces sonando a la vez. El limitador de
 * sobrecarga no toca nada mientras la suma cabe. */
/* Sin sonido (nosound.txt): hace avanzar las posiciones de las voces como si se hubieran
 * mezclado `frames` fotogramas a out_rate, sin calcular ni producir muestras. El juego
 * sigue viendo cursores que avanzan (rellena la música por ellos). */
void audio_advance(uint32_t frames, uint32_t out_rate);
typedef struct { uint64_t frames, limited, clipped; int peak, max_voices; } AudioStats;
void audio_mix_stats(AudioStats *out);
#endif
