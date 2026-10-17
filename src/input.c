#include "t123/input.h"

#include <stddef.h>

static uint8_t translate(char token, int8_t facing) {
    static const uint8_t face_positive[10] = {
        0x0b, 0x09, 0x08, 0x0a, 0x01, 0x00, 0x02, 0x05, 0x04, 0x06
    };
    static const uint8_t face_negative[10] = {
        0x0b, 0x0a, 0x08, 0x09, 0x02, 0x00, 0x01, 0x06, 0x04, 0x05
    };
    if (token >= '0' && token <= '9')
        return (facing > 0 ? face_positive : face_negative)[token - '0'];
    switch (token) {
    case 'N': return 0x00;
    case 'R': return 0x02;
    case 'L': return 0x01;
    case 'A': return 0x10;
    case 'B': return 0x20;
    case 'C': return 0x40;
    case 'D': return 0x80;
    case 'X': return 0xf0;
    default: return 0;
    }
}

void t123_input_history_reset(T123InputHistory *history, uint16_t sample) {
    if (!history) return;
    for (unsigned i = 0; i < T123_INPUT_HISTORY_CAPACITY; ++i)
        history->samples[i] = sample;
    history->count = T123_INPUT_HISTORY_CAPACITY;
    history->next = 0;
}

void t123_input_history_push(T123InputHistory *history, uint16_t sample) {
    if (!history) return;
    history->samples[history->next] = sample;
    history->next = (uint8_t)((history->next + 1u) % T123_INPUT_HISTORY_CAPACITY);
    if (history->count < T123_INPUT_HISTORY_CAPACITY) ++history->count;
}

uint16_t t123_input_history_get(const T123InputHistory *history, unsigned index) {
    if (!history || index >= history->count) return 0;
    unsigned oldest = (history->next + T123_INPUT_HISTORY_CAPACITY - history->count) %
                      T123_INPUT_HISTORY_CAPACITY;
    return history->samples[(oldest + index) % T123_INPUT_HISTORY_CAPACITY];
}

static unsigned length(const char *text) {
    unsigned size = 0;
    if (text) while (text[size]) ++size;
    return size;
}

static uint8_t wildcard_result(uint8_t buttons) {
    if (buttons & 0x10u) return 1;
    if (buttons & 0x20u) return 2;
    if (buttons & 0x40u) return 3;
    if (buttons & 0x80u) return 4;
    return 0;
}

uint8_t t123_input_match(const T123InputHistory *history, const char *pattern,
                         unsigned max_history, int8_t facing) {
    unsigned size = length(pattern);
    if (!history || !pattern || !size || !max_history || !history->count)
        return 0;
    if (max_history > history->count) max_history = history->count;

    /* The original retains its pattern cursor while advancing through the
     * candidate input samples. 0x0b is a special down-bit test. A direction
     * immediately followed by a button is the final-input/key-map path. */
    unsigned first = history->count - max_history;
    unsigned pos = 0;
    for (unsigned index = first; index < history->count && pos < size; ++index) {
        uint8_t token = translate(pattern[pos], facing);
        uint16_t sample = t123_input_history_get(history, index);
        uint8_t directions = (uint8_t)(sample & 0x0fu);
        uint8_t buttons = (uint8_t)(sample & 0xf0u);
        if (token == 0x0b) {
            if (directions & 0x08u) ++pos;
            continue;
        }
        if (token < 0x10u) {
            if (directions != token) {
                /* 0046cc90 clears the partial command when a directional
                 * token is missed on a sample that also has a button. */
                if (buttons) pos = 0;
                continue;
            }
            ++pos;
            if (pos == size) return 1;
            uint8_t next = translate(pattern[pos], facing);
            if (next < 0x10u) continue;

            /* A direction may share its sample with the following button.
             * Otherwise keep that button as the next token and keep scanning. */
            if (next == 0xf0u && buttons) {
                if (pos + 1u == size) return wildcard_result(buttons);
                ++pos;
            } else if (next != 0xf0u && buttons == next) {
                if (pos + 1u == size) return 1;
                ++pos;
            }
            continue;
        }
        if (token == 0xf0u) {
            if (!buttons) continue;
            ++pos;
            if (pos != size) continue;
            return wildcard_result(buttons);
        }
        if (buttons == token) ++pos;
    }
    return pos == size ? 1 : 0;
}
