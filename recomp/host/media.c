/* DirectInput8 and DirectSound8 objects created through CoCreateInstance.
 * Input: keyboard state is reported empty until the SDL mapping lands (F2.3).
 * Sound: buffers are voices of the mixer (audio_mix.c), played by audio_out_*.c. */
#include "audio_mix.h"
#include "com.h"
#include "render.h"

#include <pthread.h>

#include <stdio.h>
#include <string.h>

#define API(name) static void name(Cpu *c)

static ComClass dinput_class = COM_CLASS(IDirectInput8A);
static ComClass didevice_class = COM_CLASS(IDirectInputDevice8A);
static ComClass dsound_class = COM_CLASS(IDirectSound8);
static ComClass dsbuffer_class = COM_CLASS(IDirectSoundBuffer);

/* -- DirectInput8 --------------------------------------------------------------------- */
API(DI_CreateDevice) {
    uint32_t guid = ARG(c, 1);
    uint32_t kind = rd32(guid) == 0x6F1D2B61u ? 1 /* GUID_SysKeyboard */ : 2 /* mouse */;
    trace("IDirectInput8A::CreateDevice(%08x-...)", rd32(guid));
    wr32(ARG(c, 2), com_new(&didevice_class, kind, 0));
    ret_stdcall(c, S_OK, 4);
}
API(DI_EnumDevices) { ret_stdcall(c, S_OK, 5); } /* no game controllers yet */
/* Keyboard: the renderer's input (SDL scancodes on PC, buttons on the Vita) mapped to
   DIK codes by input_map.c (Codex T9). The mouse stays still. */
API(DID_GetDeviceState) {
    uint32_t size = ARG(c, 1), out = ARG(c, 2);
    memset(G(out), 0, size);
    if (com_index(ARG(c, 0)) == 1 && size >= 256)
        render_keyboard_state(G(out));
    ret_stdcall(c, S_OK, 3);
}

/* -- DirectSound8 -------------------------------------------------------------------- */
/* Each buffer is a voice of the mixer (audio_mix.c, Codex T12) reading its PCM straight
   from the guest heap; audio_out_*.c plays the mix. The buffer, its Buffer8 and 3D
   interfaces share one slot, freed when the last of them is released. */
typedef struct { uint32_t bytes, data, rate, block; AudioVoice *voice; unsigned objects, next_free; } SoundBuffer;
enum { MAX_BUFFERS = 1024 };
static SoundBuffer buffers[MAX_BUFFERS];
static unsigned buffer_count = 1, free_buffer;
static pthread_mutex_t sound_lock = PTHREAD_MUTEX_INITIALIZER;

API(DS_GetCaps) {
    uint32_t p = ARG(c, 1), size = rd32(p);
    memset(G(p), 0, size ? size : 96);
    wr32(p, size);
    ret_stdcall(c, S_OK, 2);
}
API(DS_CreateSoundBuffer) {
    uint32_t desc = ARG(c, 1), bytes = rd32(desc + 8), wfx = rd32(desc + 16);
    pthread_mutex_lock(&sound_lock);
    unsigned i = free_buffer;
    if (i) free_buffer = buffers[i].next_free;
    else if (buffer_count < MAX_BUFFERS) i = buffer_count++;
    pthread_mutex_unlock(&sound_lock);
    if (!i) {
        trace("# DirectSound: out of buffer slots");
        ret_stdcall(c, E_FAIL, 4);
        return;
    }
    SoundBuffer *b = &buffers[i];
    memset(b, 0, sizeof *b);
    b->bytes = bytes;
    b->objects = 1;
    b->data = bytes ? heap_alloc(bytes, 1) : 0; /* 0 bytes: the primary buffer, silent */
    if (b->data && wfx) {
        int channels = rd16(wfx + 2), bits = rd16(wfx + 14);
        b->rate = rd32(wfx + 4);
        b->block = rd16(wfx + 12);
        b->voice = audio_voice_new((const uint8_t *)G(b->data), bytes, b->rate, channels, bits);
        audio_out_start();
    }
    wr32(ARG(c, 2), com_new(&dsbuffer_class, i, 0));
    ret_stdcall(c, S_OK, 4);
}
/* QueryInterface must hand out an object with the requested vtable: answering with
   the buffer itself made a 3-argument IDirectSound3DBuffer::SetMinDistance land on the
   2-argument SetFrequency and broke the guest stack (caught by the CRT cookie). */
static ComClass dsbuffer8_class = COM_CLASS(IDirectSoundBuffer8);
static ComClass ds3dbuffer_class = COM_CLASS(IDirectSound3DBuffer);
static ComClass ds3dlistener_class = COM_CLASS(IDirectSound3DListener);

API(DSB_QueryInterface) {
    uint32_t o = ARG(c, 0), iid = ARG(c, 1), out = ARG(c, 2), d1 = rd32(iid), r = 0;
    unsigned i = com_index(o);
    if (d1 == 0x279AFA85u) {              /* IDirectSoundBuffer */
        wr32(o + 4, rd32(o + 4) + 1);
        r = o;
    } else if (d1 == 0x6825A449u) {       /* IDirectSoundBuffer8: same buffer, extended vtable */
        r = com_new(&dsbuffer8_class, i, 0);
    } else if (d1 == 0x279AFA86u) {       /* IDirectSound3DBuffer */
        r = com_new(&ds3dbuffer_class, i, 0);
    } else if (d1 == 0x279AFA84u) {       /* IDirectSound3DListener */
        r = com_new(&ds3dlistener_class, i, 0);
    }
    if (r && r != o) {
        pthread_mutex_lock(&sound_lock);
        buffers[i].objects++;
        pthread_mutex_unlock(&sound_lock);
    }
    trace("IDirectSoundBuffer::QueryInterface(%08x-...) = %08x", d1, r);
    wr32(out, r);
    ret_stdcall(c, r ? S_OK : E_NOINTERFACE, 3);
}
API(DSB_Release) {
    uint32_t o = ARG(c, 0), n = rd32(o + 4);
    if (n) wr32(o + 4, --n);
    if (!n) {
        unsigned i = com_index(o);
        SoundBuffer *b = &buffers[i];
        pthread_mutex_lock(&sound_lock);
        int last = b->objects && --b->objects == 0;
        pthread_mutex_unlock(&sound_lock);
        heap_free(o);
        if (last) {
            audio_voice_free(b->voice); /* stops reading the PCM before it is freed */
            heap_free(b->data);
            pthread_mutex_lock(&sound_lock);
            memset(b, 0, sizeof *b);
            b->next_free = free_buffer;
            free_buffer = i;
            pthread_mutex_unlock(&sound_lock);
        }
    }
    ret_stdcall(c, n, 1);
}
API(DSB_Lock) {
    SoundBuffer *b = &buffers[com_index(ARG(c, 0))];
    uint32_t off = ARG(c, 1), n = ARG(c, 2), flags = ARG(c, 7);
    if (flags & 1 /* DSBLOCK_FROMWRITECURSOR */ && b->voice) {
        uint32_t play, write;
        audio_voice_position(b->voice, &play, &write);
        off = write % (b->bytes ? b->bytes : 1);
    }
    if (flags & 2 /* DSBLOCK_ENTIREBUFFER */) { off = 0; n = b->bytes; }
    uint32_t first = off + n > b->bytes ? b->bytes - off : n;
    wr32(ARG(c, 3), b->data + off);
    wr32(ARG(c, 4), first);
    if (ARG(c, 5)) wr32(ARG(c, 5), n > first ? b->data : 0);
    if (ARG(c, 6)) wr32(ARG(c, 6), n > first ? n - first : 0);
    ret_stdcall(c, S_OK, 8);
}
API(DSB_Play) {
    SoundBuffer *b = &buffers[com_index(ARG(c, 0))];
    audio_voice_play(b->voice, ARG(c, 3) & 1 /* DSBPLAY_LOOPING */);
    ret_stdcall(c, S_OK, 4);
}
API(DSB_Stop) { audio_voice_stop(buffers[com_index(ARG(c, 0))].voice); ret_stdcall(c, S_OK, 1); }
API(DSB_SetVolume) { audio_voice_set_volume(buffers[com_index(ARG(c, 0))].voice, (int32_t)ARG(c, 1)); ret_stdcall(c, S_OK, 2); }
API(DSB_SetPan) { audio_voice_set_pan(buffers[com_index(ARG(c, 0))].voice, (int32_t)ARG(c, 1)); ret_stdcall(c, S_OK, 2); }
API(DSB_SetFrequency) { audio_voice_set_frequency(buffers[com_index(ARG(c, 0))].voice, ARG(c, 1)); ret_stdcall(c, S_OK, 2); }
API(DSB_SetCurrentPosition) {
    audio_voice_set_position(buffers[com_index(ARG(c, 0))].voice, ARG(c, 1));
    ret_stdcall(c, S_OK, 2);
}
/* The write cursor runs ahead of the play cursor by one mixing period of the output
   (~40 ms), so streamed music is refilled where it will not be played in between. */
API(DSB_GetCurrentPosition) {
    SoundBuffer *b = &buffers[com_index(ARG(c, 0))];
    uint32_t play = 0, write = 0;
    if (b->voice) {
        audio_voice_position(b->voice, &play, &write);
        if (play >= b->bytes) play = write = 0;
        uint32_t ahead = b->rate / 25 * (b->block ? b->block : 1);
        write = b->bytes ? (play + ahead) % b->bytes : 0;
    }
    if (ARG(c, 1)) wr32(ARG(c, 1), play);
    if (ARG(c, 2)) wr32(ARG(c, 2), write);
    ret_stdcall(c, S_OK, 3);
}
API(DSB_GetStatus) {
    SoundBuffer *b = &buffers[com_index(ARG(c, 0))];
    wr32(ARG(c, 1), audio_voice_playing(b->voice) ? 1 /* DSBSTATUS_PLAYING */ : 0);
    ret_stdcall(c, S_OK, 2);
}
/* -- CoCreateInstance -------------------------------------------------------------------- */
static int guid_is(uint32_t g, uint32_t d1) { return rd32(g) == d1; }

API(CoCreateInstance) {
    uint32_t clsid = ARG(c, 0), out = ARG(c, 4), object = 0;
    if (guid_is(clsid, 0x25E609E4u))      /* CLSID_DirectInput8 */
        object = com_new(&dinput_class, 0, 0);
    else if (guid_is(clsid, 0x3901CC3Fu)) /* CLSID_DirectSound8 */
        object = com_new(&dsound_class, 0, 0);
    trace("CoCreateInstance(%08x-...) = %08x", rd32(clsid), object);
    wr32(out, object);
    ret_stdcall(c, object ? S_OK : 0x80040154u, 5);
}

void media_init(void) {
    static int done;
    if (done) return;
    done = 1;
    com_bind_ok(&dinput_class, "Initialize");
    com_bind(&dinput_class, "CreateDevice", DI_CreateDevice);
    com_bind(&dinput_class, "EnumDevices", DI_EnumDevices);
    const char *dev_ok[] = {"SetDataFormat", "SetCooperativeLevel", "SetProperty", "Acquire", "Unacquire", "Poll"};
    for (unsigned i = 0; i < 6; i++) com_bind_ok(&didevice_class, dev_ok[i]);
    com_bind(&didevice_class, "GetDeviceState", DID_GetDeviceState);
    com_bind_ok(&dsound_class, "Initialize");
    com_bind_ok(&dsound_class, "SetCooperativeLevel");
    com_bind(&dsound_class, "GetCaps", DS_GetCaps);
    com_bind(&dsound_class, "CreateSoundBuffer", DS_CreateSoundBuffer);
    ComClass *buffer_classes[] = {&dsbuffer_class, &dsbuffer8_class};
    for (unsigned k = 0; k < 2; k++) {
        ComClass *b = buffer_classes[k];
        com_bind(b, "QueryInterface", DSB_QueryInterface);
        com_bind(b, "Lock", DSB_Lock);
        com_bind(b, "GetCurrentPosition", DSB_GetCurrentPosition);
        com_bind(b, "GetStatus", DSB_GetStatus);
        com_bind(b, "Release", DSB_Release);
        com_bind(b, "Play", DSB_Play);
        com_bind(b, "Stop", DSB_Stop);
        com_bind(b, "SetVolume", DSB_SetVolume);
        com_bind(b, "SetPan", DSB_SetPan);
        com_bind(b, "SetFrequency", DSB_SetFrequency);
        com_bind(b, "SetCurrentPosition", DSB_SetCurrentPosition);
        com_bind_ok(b, "Unlock");
    }
    /* 3D sound parameters are accepted (positional audio comes with F2.3). */
    com_bind(&ds3dbuffer_class, "Release", DSB_Release);
    for (unsigned i = 0; i < ds3dbuffer_class.count; i++)
        if (!strncmp(ds3dbuffer_class.methods[i].name, "Set", 3))
            com_bind_ok(&ds3dbuffer_class, ds3dbuffer_class.methods[i].name);
    for (unsigned i = 0; i < ds3dlistener_class.count; i++)
        if (!strncmp(ds3dlistener_class.methods[i].name, "Set", 3) ||
            !strcmp(ds3dlistener_class.methods[i].name, "CommitDeferredSettings"))
            com_bind_ok(&ds3dlistener_class, ds3dlistener_class.methods[i].name);
}

#define E(name) {#name, name}
const ApiEntry win32_media[] = {
    E(CoCreateInstance),
    {NULL, NULL},
};
