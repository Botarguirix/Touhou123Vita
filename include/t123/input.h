#ifndef T123_INPUT_H
#define T123_INPUT_H

#include <stdint.h>

enum { T123_INPUT_HISTORY_CAPACITY = 90 };

typedef struct {
    uint16_t samples[T123_INPUT_HISTORY_CAPACITY];
    uint8_t count;
    uint8_t next;
} T123InputHistory;

void t123_input_history_reset(T123InputHistory *history, uint16_t sample);
void t123_input_history_push(T123InputHistory *history, uint16_t sample);
/* Read by chronological index (0 is the oldest retained sample). */
uint16_t t123_input_history_get(const T123InputHistory *history, unsigned index);

/* Return the game's matcher result (0=no match, 1=match, 1..4 for X's
 * configured A/B/C/D button). This isolated implementation is provisional:
 * see docs/INPUT_STATE.md for the currently verified scope. */
uint8_t t123_input_match(const T123InputHistory *history, const char *pattern,
                         unsigned max_history, int8_t facing);

#endif
