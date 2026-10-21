#ifndef T123_REPLAY_H
#define T123_REPLAY_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define T123_REPLAY_MAX_RECORDS 32u
#define T123_REPLAY_MAX_VALUES 1000000u
#define T123_REPLAY_INPUT_ID_COUNT 6u

typedef struct {
    uint8_t character_id[2];
    size_t input_words_offset;
    uint32_t input_word_count;
} t123_replay_record;

typedef struct {
    const uint8_t *bytes;
    size_t size;
    uint32_t version;
    uint8_t record_count;
    t123_replay_record records[T123_REPLAY_MAX_RECORDS];
} t123_replay_file;

typedef struct {
    const t123_replay_file *file;
    uint8_t record_index;
    uint32_t word_index;
} t123_replay_cursor;

typedef struct {
    uint16_t button_mask;
    uint8_t input_count;
    uint8_t input_ids[T123_REPLAY_INPUT_ID_COUNT];
} t123_replay_input;

/* Parses the compatible 2009 replay schema without copying variable vectors. */
bool t123_replay_parse(t123_replay_file *out, const uint8_t *bytes, size_t size);
bool t123_replay_cursor_init(t123_replay_cursor *cursor,
                             const t123_replay_file *file,
                             uint8_t record_index);
bool t123_replay_peek(const t123_replay_cursor *cursor, uint16_t *word);
bool t123_replay_next(t123_replay_cursor *cursor, uint16_t *word);
/* Decode slot 0: low 10-bit mask plus the six input-state flags. */
bool t123_replay_decode_input(uint16_t word, t123_replay_input *out);
/* Decode slot 1: the original PE uses only the low 10-bit mask here. */
bool t123_replay_decode_secondary_input(uint16_t word, t123_replay_input *out);
/* Consume one original two-slot decoder invocation (f0 == 3) atomically. */
bool t123_replay_next_input_pair(t123_replay_cursor *cursor,
                                 t123_replay_input *primary,
                                 t123_replay_input *secondary);

#endif
