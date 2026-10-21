#include "t123/replay.h"

#include <string.h>

typedef struct {
    const uint8_t *bytes;
    size_t size;
    size_t offset;
} replay_reader;

static bool take(replay_reader *reader, size_t count, const uint8_t **out)
{
    if (count > reader->size - reader->offset) return false;
    *out = reader->bytes + reader->offset;
    reader->offset += count;
    return true;
}

static bool read_u8(replay_reader *reader, uint8_t *out)
{
    const uint8_t *p;
    if (!take(reader, 1u, &p)) return false;
    *out = p[0];
    return true;
}

static bool read_u32(replay_reader *reader, uint32_t *out)
{
    const uint8_t *p;
    if (!take(reader, 4u, &p)) return false;
    *out = (uint32_t)p[0] |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
    return true;
}

static bool skip_u16_vector(replay_reader *reader, uint32_t count)
{
    const uint8_t *ignored;
    if (count > T123_REPLAY_MAX_VALUES || count > (reader->size - reader->offset) / 2u)
        return false;
    return take(reader, (size_t)count * 2u, &ignored);
}

static bool read_character_channel(replay_reader *reader, uint8_t *character_id)
{
    uint8_t reserved;
    uint8_t flags[3];
    uint32_t count;
    if (!read_u8(reader, character_id) || !read_u8(reader, &reserved) ||
        !read_u32(reader, &count) || !skip_u16_vector(reader, count) ||
        !read_u8(reader, &flags[0]) || !read_u8(reader, &flags[1]) ||
        !read_u8(reader, &flags[2]))
        return false;
    return true;
}

bool t123_replay_parse(t123_replay_file *out, const uint8_t *bytes, size_t size)
{
    replay_reader reader;
    t123_replay_file parsed;
    const uint8_t *header;
    uint32_t count;
    uint32_t i;
    uint8_t signed_count;

    if (!out || !bytes || size < 14u) return false;
    memset(&parsed, 0, sizeof(parsed));
    reader.bytes = bytes;
    reader.size = size;
    reader.offset = 0u;

    if (!read_u32(&reader, &parsed.version) ||
        (parsed.version != 0x000000c8u && parsed.version != 0x000100c8u) ||
        !take(&reader, 10u, &header))
        return false;
    signed_count = header[7];
    if (signed_count == 0u || signed_count > T123_REPLAY_MAX_RECORDS) return false;
    parsed.record_count = signed_count;

    for (i = 0; i < parsed.record_count; ++i) {
        t123_replay_record *record = &parsed.records[i];
        uint8_t trailer[3];
        uint32_t trailer_word;

        if (!read_character_channel(&reader, &record->character_id[0]) ||
            !read_character_channel(&reader, &record->character_id[1]) ||
            !read_u8(&reader, &trailer[0]) || !read_u8(&reader, &trailer[1]) ||
            !read_u8(&reader, &trailer[2]) || !read_u32(&reader, &trailer_word) ||
            !read_u32(&reader, &count) || count > T123_REPLAY_MAX_VALUES ||
            count > (reader.size - reader.offset) / 2u)
            return false;

        record->input_words_offset = reader.offset;
        record->input_word_count = count;
        if (!skip_u16_vector(&reader, count)) return false;
    }
    if (reader.offset != size) return false;

    parsed.bytes = bytes;
    parsed.size = size;
    *out = parsed;
    return true;
}

bool t123_replay_cursor_init(t123_replay_cursor *cursor,
                             const t123_replay_file *file,
                             uint8_t record_index)
{
    if (!cursor || !file || !file->bytes || record_index >= file->record_count)
        return false;
    cursor->file = file;
    cursor->record_index = record_index;
    cursor->word_index = 0u;
    return true;
}

bool t123_replay_peek(const t123_replay_cursor *cursor, uint16_t *word)
{
    const t123_replay_record *record;
    size_t offset;
    if (!cursor || !word || !cursor->file ||
        cursor->record_index >= cursor->file->record_count)
        return false;
    record = &cursor->file->records[cursor->record_index];
    if (cursor->word_index >= record->input_word_count) return false;
    offset = record->input_words_offset + (size_t)cursor->word_index * 2u;
    if (offset > cursor->file->size || cursor->file->size - offset < 2u) return false;
    *word = (uint16_t)cursor->file->bytes[offset] |
            ((uint16_t)cursor->file->bytes[offset + 1u] << 8);
    return true;
}

bool t123_replay_next(t123_replay_cursor *cursor, uint16_t *word)
{
    uint16_t current;
    if (!t123_replay_peek(cursor, &current)) return false;
    *word = current;
    cursor->word_index++;
    return true;
}

bool t123_replay_decode_input(uint16_t word, t123_replay_input *out)
{
    static const struct {
        uint16_t bit;
        uint8_t input_id;
    } map[T123_REPLAY_INPUT_ID_COUNT] = {
        {0x8000u, 0x3bu}, {0x4000u, 0x3cu}, {0x2000u, 0x3du},
        {0x1000u, 0x3fu}, {0x0800u, 0x40u}, {0x0400u, 0x41u},
    };
    unsigned i;
    if (!out) return false;
    out->button_mask = word & 0x03ffu;
    out->input_count = 0u;
    for (i = 0; i < T123_REPLAY_INPUT_ID_COUNT; ++i) {
        if (word & map[i].bit) out->input_ids[out->input_count++] = map[i].input_id;
    }
    return true;
}

bool t123_replay_decode_secondary_input(uint16_t word, t123_replay_input *out)
{
    if (!out) return false;
    out->button_mask = word & 0x03ffu;
    out->input_count = 0u;
    return true;
}

bool t123_replay_next_input_pair(t123_replay_cursor *cursor,
                                 t123_replay_input *primary,
                                 t123_replay_input *secondary)
{
    t123_replay_cursor next;
    uint16_t primary_word;
    uint16_t secondary_word;
    t123_replay_input decoded_primary;
    t123_replay_input decoded_secondary;

    if (!cursor || !primary || !secondary) return false;
    next = *cursor;
    if (!t123_replay_next(&next, &primary_word) ||
        !t123_replay_next(&next, &secondary_word) ||
        !t123_replay_decode_input(primary_word, &decoded_primary) ||
        !t123_replay_decode_secondary_input(secondary_word, &decoded_secondary))
        return false;

    *cursor = next;
    *primary = decoded_primary;
    *secondary = decoded_secondary;
    return true;
}
