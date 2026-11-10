/* The game's UDP networking on the Vita (see host/net.h and docs/TECLADO_Y_ADHOC.md).
 *
 * th123.exe imports only 14 WS2_32 functions and uses plain UDP: socket, bind, sendto and a
 * blocking recvfrom in its own thread. They are mapped one to one onto SceNet sockets.
 *
 * adhoc.txt: the Vita's ad-hoc network is IP based (169.254.x.x). Two Vitas running the game
 * start SceNetAdhocMatching in P2P mode, find each other through its hello packets and pair;
 * the paired Vita's address is then the destination of every datagram, whatever IP the
 * player typed in the game's network menu (any text works), and datagrams that arrive from
 * it are reported with the address the game used, so the game's own checks still hold.
 *
 * Nothing here has run on hardware yet: the log lines "# adhoc: ..." in the trace are meant
 * to show every step (return codes, matching events, the addresses) so it can be corrected. */
#include <psp2/kernel/threadmgr.h>
#include <psp2/net/adhoc_matching.h>
#include <psp2/net/net.h>
#include <psp2/net/netctl.h>
#include <psp2/pspnet_adhoc.h>
#include <psp2/pspnet_adhocctl.h>
#include <psp2/sysmodule.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../host/net.h"
#include "../host/win32.h"

enum { MAX_SOCKETS = 8, NET_MEMORY = 128 * 1024, MATCHING_POOL = 128 * 1024, MATCHING_PORT = 0x3a5a };
/* SceNetAdhocMatching event numbers (the SDK header leaves them out; these are the PSP ones) */
enum { M_HELLO = 1, M_REQUEST, M_LEAVE, M_DENY, M_CANCEL, M_ACCEPT, M_ESTABLISHED, M_TIMEOUT, M_ERROR, M_BYE,
       M_DATA, M_DATA_ACK, M_DATA_TIMEOUT, M_PING };

static int mode_adhoc = -1, mode_wifi;
static uint32_t manual_peer; /* peer-ip.txt (Wi-Fi mode): where every datagram goes, network order */
static int net_ready;
static int sockets[MAX_SOCKETS];   /* SceNet socket ids, -1 = free */
static volatile int shut[MAX_SOCKETS];
static volatile int paired, requested;
static volatile uint32_t peer_ip;  /* network order */
static volatile uint32_t game_dst; /* the address the game last sent to (network order) */
static int match_id = -1;

int net_enabled(void) {
    if (mode_adhoc < 0) {
        FILE *a = fopen("ux0:data/touhou123vita/adhoc.txt", "rb");
        FILE *w = fopen("ux0:data/touhou123vita/wifi.txt", "rb");
        mode_adhoc = a != NULL;
        mode_wifi = !mode_adhoc && w != NULL;
        if (a) fclose(a);
        if (w) fclose(w);
        trace("# net: %s", mode_adhoc ? "ad-hoc mode (adhoc.txt)" : mode_wifi ? "Wi-Fi mode (wifi.txt)" : "off (no adhoc.txt or wifi.txt)");
        /* peer-ip.txt holds the other Vita's address ("192.168.1.50"): with it the address typed
           in the game's menu does not matter, so no keyboard is needed to set it */
        FILE *p = mode_wifi ? fopen("ux0:data/touhou123vita/peer-ip.txt", "rb") : NULL;
        if (p) {
            char text[64] = "";
            unsigned a, b, c, d;
            if (fgets(text, sizeof text, p) && sscanf(text, "%u.%u.%u.%u", &a, &b, &c, &d) == 4 && (a | b | c | d) < 256) {
                manual_peer = a | b << 8 | c << 16 | d << 24;
                trace("# net: every datagram goes to %u.%u.%u.%u (peer-ip.txt), whatever address the game is given", a, b, c, d);
            } else {
                trace("# net: peer-ip.txt does not hold an address like 192.168.1.50");
            }
            fclose(p);
        }
    }
    return mode_adhoc || mode_wifi;
}

static void ip_text(uint32_t ip, char *out) { /* network order */
    snprintf(out, 16, "%u.%u.%u.%u", ip & 255, ip >> 8 & 255, ip >> 16 & 255, ip >> 24);
}

static void match_cb(int id, int type, SceNetInAddr *addr, SceSize len, void *opt) {
    (void)opt;
    uint32_t ip = addr ? addr->s_addr : 0;
    char text[16];
    ip_text(ip, text);
    trace("# adhoc: matching event %d from %s (%u bytes)", type, text, (unsigned)len);
    switch (type) {
    case M_HELLO:
        if (!paired && !requested && addr) {
            /* both Vitas hear each other's hello: the one with the lower address asks, the
               other waits for the request, so the two requests do not cross */
            SceNetInAddr mine = {0};
            int have = sceNetCtlAdhocGetInAddr(&mine) == 0 && mine.s_addr != 0;
            uint32_t a = __builtin_bswap32(mine.s_addr), b = __builtin_bswap32(ip);
            if (!have || a < b) {
                requested = 1;
                int r = sceNetAdhocMatchingSelectTarget(id, addr, 0, NULL);
                trace("# adhoc: asking %s to pair -> %08x", text, (unsigned)r);
            }
        }
        break;
    case M_REQUEST: {
        int r = sceNetAdhocMatchingSelectTarget(id, addr, 0, NULL); /* accept */
        trace("# adhoc: accepting %s -> %08x", text, (unsigned)r);
        break;
    }
    case M_ESTABLISHED:
        peer_ip = ip;
        paired = 1;
        requested = 0;
        trace("# adhoc: PAIRED with %s", text);
        break;
    case M_LEAVE: case M_BYE: case M_CANCEL: case M_DENY: case M_TIMEOUT: case M_ERROR:
        if (paired || requested) trace("# adhoc: pairing ended (event %d)", type);
        paired = 0;
        requested = 0;
        break;
    default:
        break;
    }
}

static int match_started;
static int match_last_result = 1;

/* The first trace of the ad-hoc test showed sceNetAdhocMatchingStart failing with 0x80412108
   (a NetCtl error, not a matching one) while the Vita was joined to a Wi-Fi router, so the
   start is retried every 5 s and the state of the normal connection is logged with it. */
static void match_start(const char *why) {
    static const char hello[] = "TH123";
    int r = sceNetAdhocMatchingStart(match_id, 0x40, 0x4000, 0, (int)sizeof hello, (void *)hello);
    match_started = r >= 0;
    if (r != match_last_result || match_started) {
        int inet = -1;
        sceNetCtlInetGetState(&inet);
        SceNetCtlInfo info;
        memset(&info, 0, sizeof info);
        int has_ssid = sceNetCtlInetGetInfo(SCE_NETCTL_INFO_GET_SSID, &info) == 0;
        trace("# adhoc: sceNetAdhocMatchingStart (%s) -> %08x; the normal Wi-Fi is %s%s%s", why, (unsigned)r,
              inet == SCE_NETCTL_STATE_CONNECTED ? "CONNECTED" : inet == SCE_NETCTL_STATE_DISCONNECTED ? "not connected" : "busy",
              has_ssid && info.ssid[0] ? " to " : "", has_ssid ? info.ssid : "");
    }
    match_last_result = r;
}

static void adhoc_start(void) {
    int r = sceNetAdhocInit();
    trace("# adhoc: sceNetAdhocInit -> %08x", (unsigned)r);
    SceNetAdhocctlAdhocId id;
    memset(&id, 0, sizeof id);
    id.type = SCE_NET_ADHOCCTL_ADHOCTYPE_PRODUCT_ID;
    memcpy(id.data, "THSV12302", 9);
    r = sceNetAdhocctlInit(&id);
    trace("# adhoc: sceNetAdhocctlInit -> %08x", (unsigned)r);
    void *pool = malloc(MATCHING_POOL);
    r = pool ? sceNetAdhocMatchingInit(MATCHING_POOL, pool) : -1;
    trace("# adhoc: sceNetAdhocMatchingInit -> %08x", (unsigned)r);
    match_id = sceNetAdhocMatchingCreate(SCE_NET_ADHOC_MATCHING_MODE_P2P, 2, MATCHING_PORT, 2048, 1000000, 1000000, 5,
                                         500000, match_cb);
    trace("# adhoc: sceNetAdhocMatchingCreate -> %d", match_id);
    if (match_id >= 0) match_start("first try");
}

static void net_start(void) {
    if (net_ready || !net_enabled()) return;
    net_ready = 1;
    for (int i = 0; i < MAX_SOCKETS; i++) sockets[i] = -1;
    int r = sceSysmoduleLoadModule(SCE_SYSMODULE_NET);
    trace("# net: sceSysmoduleLoadModule(NET) -> %08x", (unsigned)r);
    SceNetInitParam p;
    p.memory = malloc(NET_MEMORY);
    p.size = NET_MEMORY;
    p.flags = 0;
    r = p.memory ? sceNetInit(&p) : -1;
    trace("# net: sceNetInit -> %08x", (unsigned)r);
    r = sceNetCtlInit();
    trace("# net: sceNetCtlInit -> %08x", (unsigned)r);
    if (mode_adhoc) {
        /* the ad-hoc libraries are separate system modules: without them their imports
           resolve to address 0 and the first call (sceNetAdhocInit) crashed the game at start */
        int a = sceSysmoduleLoadModule(SCE_SYSMODULE_PSPNET_ADHOC);
        int m = sceSysmoduleLoadModule(SCE_SYSMODULE_NET_ADHOC_MATCHING);
        trace("# net: sceSysmoduleLoadModule(PSPNET_ADHOC) -> %08x, (NET_ADHOC_MATCHING) -> %08x", (unsigned)a, (unsigned)m);
        if (a >= 0 && m >= 0) adhoc_start();
        else {
            trace("# adhoc: unavailable (a system module did not load); the game goes on without it");
            mode_adhoc = 0;
        }
    }
}

static unsigned hello_events;

const char *net_own_ip(void) {
    static char text[20];
    text[0] = 0;
    if (!net_ready) return text;
    SceNetCtlInfo info;
    memset(&info, 0, sizeof info);
    if (sceNetCtlInetGetInfo(SCE_NETCTL_INFO_GET_IP_ADDRESS, &info) == 0) {
        strncpy(text, info.ip_address, sizeof text - 1);
        text[sizeof text - 1] = 0;
    }
    return text;
}

void net_poll(void) {
    static uint64_t next, next_wifi;
    if (!net_enabled()) return;
    net_start(); /* at the first frame: the search for the other Vita begins here, not at the first socket() */
    uint64_t now = platform_ticks_us();
    if (mode_wifi && now >= next_wifi) {
        next_wifi = now + 10000000;
        const char *ip = net_own_ip();
        trace("# net: Wi-Fi mode: this Vita's address is %s", *ip ? ip : "(not connected to a router)");
    }
    if (!mode_adhoc || now < next) return;
    next = now + 5000000;
    if (match_id >= 0 && !match_started) match_start("retry");
    int state = -1;
    SceNetInAddr mine = {0};
    int s = sceNetCtlAdhocGetState(&state);
    int a = sceNetCtlAdhocGetInAddr(&mine);
    char own[16], other[16];
    ip_text(mine.s_addr, own);
    ip_text(peer_ip, other);
    trace("# adhoc: %s; ctl state %d (%08x), own address %s (%08x), peer %s", paired ? "PAIRED" : requested ? "asking" : "searching",
          state, (unsigned)s, own, (unsigned)a, paired ? other : "-");
    (void)hello_events;
}

int net_open(void) {
    net_start();
    if (!net_ready) return -1;
    for (int i = 0; i < MAX_SOCKETS; i++) {
        if (sockets[i] >= 0) continue;
        int s = sceNetSocket("t123", SCE_NET_AF_INET, SCE_NET_SOCK_DGRAM, 0);
        if (s < 0) {
            trace("# net: sceNetSocket -> %08x", (unsigned)s);
            return -1;
        }
        int timeout = 100000; /* a receive wakes up every 100 ms to notice a shutdown */
        sceNetSetsockopt(s, SCE_NET_SOL_SOCKET, SCE_NET_SO_RCVTIMEO, &timeout, sizeof timeout);
        sockets[i] = s;
        shut[i] = 0;
        trace("# net: socket %d = SceNet socket %d", i, s);
        return i;
    }
    return -1;
}

static int valid(int s) { return s >= 0 && s < MAX_SOCKETS && sockets[s] >= 0; }

int net_bind(int s, uint16_t port_be) {
    if (!valid(s)) return -1;
    SceNetSockaddrIn a;
    memset(&a, 0, sizeof a);
    a.sin_len = sizeof a;
    a.sin_family = SCE_NET_AF_INET;
    a.sin_port = port_be;
    a.sin_addr.s_addr = 0;
    int r = sceNetBind(sockets[s], (SceNetSockaddr *)&a, sizeof a);
    trace("# net: bind socket %d to port %u -> %08x", s, (unsigned)(port_be >> 8 | (port_be & 255) << 8), (unsigned)r);
    return r < 0 ? -1 : 0;
}

int net_send(int s, const void *data, int len, uint32_t addr_be, uint16_t port_be) {
    if (!valid(s)) return -1;
    uint32_t dst = addr_be;
    if (mode_adhoc) {
        game_dst = addr_be;
        if (!paired) {
            static unsigned complained;
            if (complained++ < 5) trace("# adhoc: datagram dropped, not paired yet");
            return -1;
        }
        dst = peer_ip;
    } else if (manual_peer) {
        game_dst = addr_be;
        dst = manual_peer;
    }
    SceNetSockaddrIn a;
    memset(&a, 0, sizeof a);
    a.sin_len = sizeof a;
    a.sin_family = SCE_NET_AF_INET;
    a.sin_port = port_be;
    a.sin_addr.s_addr = dst;
    int r = sceNetSendto(sockets[s], data, (unsigned)len, 0, (SceNetSockaddr *)&a, sizeof a);
    static unsigned sent, failed;
    if (r < 0 && failed++ < 5) trace("# net: sendto %d bytes -> %08x", len, (unsigned)r);
    if (r >= 0 && sent++ < 3) trace("# net: first datagrams sent: %d bytes", len);
    return r;
}

int net_recv(int s, void *buf, int len, uint32_t *addr_be, uint16_t *port_be) {
    unsigned errors = 0;
    while (valid(s) && !shut[s]) {
        SceNetSockaddrIn from;
        unsigned flen = sizeof from;
        memset(&from, 0, sizeof from);
        int r = sceNetRecvfrom(sockets[s], buf, (unsigned)len, 0, (SceNetSockaddr *)&from, &flen);
        if (r >= 0) {
            uint32_t ip = from.sin_addr.s_addr;
            if (mode_adhoc && paired && ip == peer_ip && game_dst) ip = game_dst; /* what the game expects */
            else if (manual_peer && ip == manual_peer && game_dst) ip = game_dst;
            *addr_be = ip;
            *port_be = from.sin_port;
            static unsigned got;
            if (got++ < 3) trace("# net: first datagrams received: %d bytes", r);
            return r;
        }
        /* a timeout (the 100 ms wake-up) is normal; a real error repeats at once, so back off */
        if (++errors > 20) { sceKernelDelayThread(20000); errors = 0; }
    }
    return -1;
}

int net_shutdown(int s) {
    if (!valid(s)) return -1;
    shut[s] = 1;
    sceNetShutdown(sockets[s], SCE_NET_SHUT_RDWR);
    return 0;
}

int net_close(int s) {
    if (!valid(s)) return -1;
    shut[s] = 1;
    sceNetShutdown(sockets[s], SCE_NET_SHUT_RDWR);
    sceKernelDelayThread(150000); /* a receive in progress sees the flag within its 100 ms timeout */
    int r = sceNetSocketClose(sockets[s]);
    trace("# net: closed socket %d -> %08x", s, (unsigned)r);
    sockets[s] = -1;
    return 0;
}
