/* DirectInput8 and DirectSound8 objects created through CoCreateInstance.
 * Input: keyboard state is reported empty until the SDL mapping lands (F2.3).
 * Sound: buffers accept locks and play calls silently; audio output is F2.3. */
#include "com.h"
#include "render.h"

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
typedef struct { uint32_t bytes, data; } SoundBuffer;
static SoundBuffer buffers[512];
static unsigned buffer_count = 1;

API(DS_GetCaps) {
    uint32_t p = ARG(c, 1), size = rd32(p);
    memset(G(p), 0, size ? size : 96);
    wr32(p, size);
    ret_stdcall(c, S_OK, 2);
}
API(DS_CreateSoundBuffer) {
    uint32_t desc = ARG(c, 1), bytes = rd32(desc + 8);
    unsigned i = buffer_count < 512 ? buffer_count++ : 0;
    buffers[i].bytes = bytes;
    buffers[i].data = bytes ? heap_alloc(bytes, 1) : 0;
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
    if (d1 == 0x279AFA85u) {              /* IDirectSoundBuffer */
        wr32(o + 4, rd32(o + 4) + 1);
        r = o;
    } else if (d1 == 0x6825A449u) {       /* IDirectSoundBuffer8: same buffer, extended vtable */
        r = com_new(&dsbuffer8_class, com_index(o), 0);
    } else if (d1 == 0x279AFA86u) {       /* IDirectSound3DBuffer */
        r = com_new(&ds3dbuffer_class, com_index(o), 0);
    } else if (d1 == 0x279AFA84u) {       /* IDirectSound3DListener */
        r = com_new(&ds3dlistener_class, com_index(o), 0);
    }
    trace("IDirectSoundBuffer::QueryInterface(%08x-...) = %08x", d1, r);
    wr32(out, r);
    ret_stdcall(c, r ? S_OK : E_NOINTERFACE, 3);
}
API(DSB_Lock) {
    SoundBuffer *b = &buffers[com_index(ARG(c, 0))];
    uint32_t off = ARG(c, 1), n = ARG(c, 2), flags = ARG(c, 7);
    if (flags & 2 /* DSBLOCK_ENTIREBUFFER */) { off = 0; n = b->bytes; }
    uint32_t first = off + n > b->bytes ? b->bytes - off : n;
    wr32(ARG(c, 3), b->data + off);
    wr32(ARG(c, 4), first);
    if (ARG(c, 5)) wr32(ARG(c, 5), n > first ? b->data : 0);
    if (ARG(c, 6)) wr32(ARG(c, 6), n > first ? n - first : 0);
    ret_stdcall(c, S_OK, 8);
}
API(DSB_GetCurrentPosition) {
    if (ARG(c, 1)) wr32(ARG(c, 1), 0);
    if (ARG(c, 2)) wr32(ARG(c, 2), 0);
    ret_stdcall(c, S_OK, 3);
}
API(DSB_GetStatus) { wr32(ARG(c, 1), 0); ret_stdcall(c, S_OK, 2); }

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
        const char *buf_ok[] = {"Unlock", "Play", "Stop", "SetVolume", "SetPan", "SetFrequency", "SetCurrentPosition"};
        for (unsigned i = 0; i < 7; i++) com_bind_ok(b, buf_ok[i]);
    }
    /* 3D sound parameters are accepted (positional audio comes with F2.3). */
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
