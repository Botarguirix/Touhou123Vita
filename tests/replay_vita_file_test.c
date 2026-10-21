#include "t123/replay.h"

#include <psp2/io/fcntl.h>
#include <stdlib.h>

int main(void)
{
    static const char path[] =
        "ux0:data/Touhou123Vita/replay/story/090815_2219_sanae_story.rep";
    static const uint8_t expected_characters[3][2] = {
        {15u, 16u}, {15u, 17u}, {15u, 0u}
    };
    static const uint32_t expected_pairs[3] = {4360u, 3466u, 9084u};
    t123_replay_file replay;
    SceUID fd = sceIoOpen(path, SCE_O_RDONLY, 0);
    SceOff size;
    uint8_t *bytes;
    int result = 0;

    if (fd < 0) return 1;
    size = sceIoLseek(fd, 0, SCE_SEEK_END);
    if (size <= 0 || sceIoLseek(fd, 0, SCE_SEEK_SET) < 0) {
        sceIoClose(fd);
        return 2;
    }
    bytes = (uint8_t *)malloc((size_t)size);
    if (!bytes) {
        sceIoClose(fd);
        return 3;
    }
    if (sceIoRead(fd, bytes, (SceSize)size) != size) result = 4;
    sceIoClose(fd);
    if (!result && !t123_replay_parse(&replay, bytes, (size_t)size)) result = 5;
    if (!result && (replay.version != 0x000100c8u || replay.record_count != 3u)) result = 6;

    for (unsigned record_index = 0u; !result && record_index < 3u; ++record_index) {
        const t123_replay_record *record = &replay.records[record_index];
        t123_replay_cursor cursor;
        t123_replay_input primary;
        t123_replay_input secondary;
        uint32_t pairs = 0u;

        if (record->character_id[0] != expected_characters[record_index][0] ||
            record->character_id[1] != expected_characters[record_index][1] ||
            record->input_word_count != expected_pairs[record_index] * 2u ||
            !t123_replay_cursor_init(&cursor, &replay, (uint8_t)record_index)) {
            result = 7;
            break;
        }
        while (t123_replay_next_input_pair(&cursor, &primary, &secondary)) {
            (void)primary;
            (void)secondary;
            ++pairs;
        }
        if (pairs != expected_pairs[record_index] ||
            cursor.word_index != record->input_word_count)
            result = 8;
    }

    free(bytes);
    return result;
}
