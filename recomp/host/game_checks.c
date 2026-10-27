/* Checks around game functions that failed under the recompiled host, to find out
 * why before changing anything. Each wrapper inspects the guest state, logs what is
 * unexpected and then runs the translated original (with a logged fallback where
 * noted).
 *
 * 0x465370  an object sets its current action: it looks the action number
 *           ([this+0x13c], int16) up in its pattern map ([this+0x160], an MSVC
 *           std::map<int, ...>) and dereferences the result. In some fights on PC (about 1
 *           run in 5, timing dependent) the key was missing and the checked iterator stopped the game with
 *           "invalid parameter" (0x81ff70). */
#include "win32.h"

#include <stdio.h>
#include <string.h>

static GuestFn set_action_original;

/* MSVC 2008 std::map: +4 head node, +8 size; node: +0 left, +4 parent, +8 right,
   +0xc key, +0x15 isnil. */
static int map_has(uint32_t map, int32_t key) {
    uint32_t head = rd32(map + 4), node = rd32(head + 4);
    for (unsigned depth = 0; depth < 64 && node && !rd8(node + 0x15); depth++) {
        int32_t k = (int32_t)rd32(node + 0xc);
        if (k == key) return 1;
        node = key < k ? rd32(node) : rd32(node + 8);
    }
    return 0;
}

/* Largest key below key, or the smallest key if there is none (-1 if empty). */
static int32_t map_key_below(uint32_t map, int32_t key) {
    uint32_t head = rd32(map + 4), node = rd32(head + 4);
    int32_t below = -1, smallest = -1;
    for (unsigned depth = 0; depth < 64 && node && !rd8(node + 0x15); depth++) {
        int32_t k = (int32_t)rd32(node + 0xc);
        if (k < key) { below = k; node = rd32(node + 8); }
        else { smallest = k; node = rd32(node); }
    }
    return below >= 0 ? below : smallest;
}

static void list_keys(uint32_t node, int32_t from, char *out, size_t size, unsigned *n) {
    if (!node || rd8(node + 0x15) || *n >= 60) return;
    list_keys(rd32(node), from, out, size, n);
    size_t len = strlen(out);
    if (*n < 60 && len + 12 < size && (int32_t)rd32(node + 0xc) >= from) {
        snprintf(out + len, size - len, " %d", (int32_t)rd32(node + 0xc));
        (*n)++;
    }
    list_keys(rd32(node + 8), from, out, size, n);
}

static void set_action_checked(Cpu *c) {
    uint32_t self = c->ecx.d, map = rd32(self + 0x160);
    int32_t action = (int16_t)rd16(self + 0x13c);
    /* first sight of each object type: its map size, to compare PC and Vita */
    static uint32_t seen[64];
    static unsigned seen_count;
    uint32_t vtable = rd32(self);
    unsigned k = 0;
    while (k < seen_count && seen[k] != vtable) k++;
    if (k == seen_count && seen_count < 64 && map) {
        seen[seen_count++] = vtable;
        trace("# set-action: first object with vtable %08x has %u patterns", vtable, rd32(map + 8));
    }
    if (map && !map_has(map, action)) {
        static unsigned reported;
        if (reported++ < 10) {
            char keys[700] = "";
            unsigned n = 0;
            list_keys(rd32(rd32(map + 4) + 4), 500, keys, sizeof keys, &n);
            /* [esp] returns into set_action (0x438ca0), [esp+4] into whoever asked */
            trace("# set-action 0x465370: object %08x (vtable %08x) action %d not in its map %08x "
                  "(%u entries; keys from 500:%s) - requested from %08x via %08x, thread %08x", self,
                  vtable, action, map, rd32(map + 8), keys, rd32(c->esp.d + 4), rd32(c->esp.d + 0x10),
                  rd32(c->fs_base + 0x24));
        }
        /* Fallback chosen by the user over a closed game: run the nearest existing action
           below (a wrong effect for a moment instead of the checked iterator stopping the
           process). The root cause (a card effect the CPU spawns, 0x74c9ca) is still open. */
        int32_t fallback = map_key_below(map, action);
        if (fallback >= 0) {
            static unsigned substituted;
            if (substituted++ < 10)
                trace("# set-action: using action %d instead of %d", fallback, action);
            wr16(self + 0x13c, (uint16_t)fallback);
        }
    }
    set_action_original(c);
}

void game_checks_init(void) {
    set_action_original = guest_lifted(0x00465370u);
    if (set_action_original)
        guest_intercept(0x00465370u, set_action_checked);
}
