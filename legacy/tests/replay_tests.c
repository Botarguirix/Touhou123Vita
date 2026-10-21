#include "t123/replay.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t bytes[256];
    size_t size;
} builder;

static void put_u8(builder *b, uint8_t value)
{
    assert(b->size < sizeof(b->bytes));
    b->bytes[b->size++] = value;
}

static void put_u16(builder *b, uint16_t value)
{
    put_u8(b, (uint8_t)value);
    put_u8(b, (uint8_t)(value >> 8));
}

static void put_u32(builder *b, uint32_t value)
{
    put_u16(b, (uint16_t)value);
    put_u16(b, (uint16_t)(value >> 16));
}

static void put_channel(builder *b, uint8_t character_id)
{
    put_u8(b, character_id);
    put_u8(b, 0u);
    put_u32(b, 2u);
    put_u16(b, 100u);
    put_u16(b, 200u);
    put_u8(b, 1u);
    put_u8(b, 2u);
    put_u8(b, 3u);
}

static builder make_replay(void)
{
    builder b = {{0}, 0u};
    unsigned i;
    put_u32(&b, 0x000100c8u);
    for (i = 0; i < 10u; ++i) put_u8(&b, i == 7u ? 1u : 0u);
    put_channel(&b, 15u);
    put_channel(&b, 16u);
    put_u8(&b, 0u);
    put_u8(&b, 0u);
    put_u8(&b, 0u);
    put_u32(&b, 0xda9d606au);
    put_u32(&b, 3u);
    put_u16(&b, 0xa155u);
    put_u16(&b, 0x8401u);
    put_u16(&b, 0u);
    return b;
}

static void test_parse_and_cursor(void)
{
    builder b = make_replay();
    t123_replay_file replay;
    t123_replay_cursor cursor;
    uint16_t word = 0u;
    assert(t123_replay_parse(&replay, b.bytes, b.size));
    assert(replay.version == 0x000100c8u);
    assert(replay.record_count == 1u);
    assert(replay.records[0].character_id[0] == 15u);
    assert(replay.records[0].character_id[1] == 16u);
    assert(replay.records[0].input_word_count == 3u);
    assert(t123_replay_cursor_init(&cursor, &replay, 0u));
    assert(t123_replay_peek(&cursor, &word) && word == 0xa155u);
    assert(cursor.word_index == 0u);
    assert(t123_replay_next(&cursor, &word) && word == 0xa155u);
    assert(cursor.word_index == 1u);
    assert(t123_replay_next(&cursor, &word) && word == 0x8401u);
    assert(t123_replay_next(&cursor, &word) && word == 0u);
    assert(!t123_replay_peek(&cursor, &word));
    assert(!t123_replay_next(&cursor, &word));
}

static void test_input_mapping(void)
{
    t123_replay_input input;
    static const uint8_t expected[] = {0x3bu, 0x3du, 0x40u};
    assert(t123_replay_decode_input(0xa955u, &input));
    assert(input.button_mask == 0x155u);
    assert(input.input_count == sizeof(expected));
    assert(memcmp(input.input_ids, expected, sizeof(expected)) == 0);

    assert(t123_replay_decode_secondary_input(0xa955u, &input));
    assert(input.button_mask == 0x155u);
    assert(input.input_count == 0u);
    assert(!t123_replay_decode_secondary_input(0u, NULL));
}

static void test_input_pair(void)
{
    builder b = make_replay();
    t123_replay_file replay;
    t123_replay_cursor cursor;
    t123_replay_input primary;
    t123_replay_input secondary;

    assert(t123_replay_parse(&replay, b.bytes, b.size));
    assert(t123_replay_cursor_init(&cursor, &replay, 0u));
    assert(t123_replay_next_input_pair(&cursor, &primary, &secondary));
    assert(primary.button_mask == 0x155u);
    assert(primary.input_count == 2u);
    assert(primary.input_ids[0] == 0x3bu);
    assert(primary.input_ids[1] == 0x3du);
    assert(secondary.button_mask == 1u);
    assert(secondary.input_count == 0u);
    assert(cursor.word_index == 2u);

    /* The third word has no partner; failure must not consume it. */
    assert(!t123_replay_next_input_pair(&cursor, &primary, &secondary));
    assert(cursor.word_index == 2u);
    {
        uint16_t last;
        assert(t123_replay_next(&cursor, &last) && last == 0u);
    }
}

static void test_rejects_invalid_inputs(void)
{
    builder b = make_replay();
    t123_replay_file replay;
    uint8_t saved;
    assert(!t123_replay_parse(&replay, b.bytes, b.size - 1u));
    assert(!t123_replay_parse(&replay, b.bytes, b.size + 1u));
    saved = b.bytes[0];
    b.bytes[0] = 0xd2u;
    assert(!t123_replay_parse(&replay, b.bytes, b.size));
    b.bytes[0] = saved;
    b.bytes[11] = 0xffu;
    assert(!t123_replay_parse(&replay, b.bytes, b.size));
    assert(!t123_replay_cursor_init(NULL, &replay, 0u));
    assert(!t123_replay_decode_input(0u, NULL));
}

int main(void)
{
    test_parse_and_cursor();
    test_input_mapping();
    test_input_pair();
    test_rejects_invalid_inputs();
    puts("replay_contract: ok");
    return 0;
}
