/* UDP networking behind the game's WS2_32 calls (socket, bind, sendto, recvfrom, ...).
 * On the Vita (vita/net_vita.c) it runs on SceNet sockets, in one of two modes chosen by
 * a file in the data directory:
 *   adhoc.txt  two Vitas find each other over the Vita's ad-hoc network (SceNetAdhocMatching)
 *              and every datagram goes to the paired Vita, whatever IP the game was given
 *   wifi.txt   plain sockets over the infrastructure Wi-Fi; the IP typed in the game is real
 * Without either file networking stays off (WSAENETDOWN), as before. On PC it is always off.
 * Addresses and ports are in network byte order, exactly as the game keeps them. */
#ifndef T123_NET_H
#define T123_NET_H

#include <stdint.h>

int net_enabled(void);   /* adhoc.txt or wifi.txt present */
/* Once per presented frame: starts SceNet and the ad-hoc search at the first call (the
 * other Vita has to be found before anyone opens the network menu) and reports the state
 * in the trace every 5 s. */
void net_poll(void);
/* This Vita's address on the Wi-Fi router ("192.168.1.20"), or "" when it is not known or not
 * connected; shown in the title of the on-screen keyboard so it can be typed on the other Vita. */
const char *net_own_ip(void);
int net_open(void);      /* a UDP socket (>= 0), or -1 */
int net_bind(int s, uint16_t port_be);
int net_send(int s, const void *data, int len, uint32_t addr_be, uint16_t port_be);
/* Blocks until a datagram arrives; -1 once the socket was shut down or closed. */
int net_recv(int s, void *buf, int len, uint32_t *addr_be, uint16_t *port_be);
int net_shutdown(int s);
int net_close(int s);

#endif
