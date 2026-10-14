#ifndef T123_FIGHT_H
#define T123_FIGHT_H
#include <stdint.h>
enum { IN_LEFT=1, IN_RIGHT=2, IN_JUMP=4, IN_MELEE=8, IN_SHOT=16, IN_GUARD=32, IN_RESET=64, IN_CONFIRM=128, IN_BACK=256, IN_AI=512 };
enum { SCENE_MENU, SCENE_PRACTICE, SCENE_FIGHT };
typedef struct { int x,y,vy,face,hp,attack,cooldown,stun,guard; unsigned hits; } Fighter;
typedef struct { int active,x,y,vx,owner; } Shot;
typedef struct { int scene,ai,frame,rounds; uint32_t previous; Fighter p[2]; Shot shots[16]; } Fight;
void fight_init(Fight *g);
void fight_reset(Fight *g);
void fight_step(Fight *g, uint32_t input);
uint32_t fight_digest(const Fight *g);
#endif
