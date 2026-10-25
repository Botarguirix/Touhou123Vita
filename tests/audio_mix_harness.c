#include "audio_mix.h"
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>

static void put(uint8_t *p, int x) { unsigned u = (unsigned)x & 65535; p[0]=(uint8_t)u; p[1]=(uint8_t)(u>>8); }
static void positions(AudioVoice *v, unsigned expected) {
    uint32_t p=UINT32_MAX,w=UINT32_MAX; audio_voice_position(v,&p,&w); assert(p==expected && w==p);
}
static void signal_test(void) {
    uint8_t pcm[22050*2]; static int16_t out[48000*2];
    for (int i=0;i<22050;i++) put(pcm+2*i,(int)lround(12000*sin(2*3.141592653589793*1000*i/22050)));
    AudioVoice *v=audio_voice_new(pcm,sizeof pcm,22050,1,16); assert(v);
    audio_voice_play(v,1); audio_mix(out,48000,48000);
    int crossings=0; double energy=0;
    for (int i=1;i<48000;i++) { crossings+=out[2*(i-1)]<=0 && out[2*i]>0; assert(out[2*i]==out[2*i+1]); energy+=(double)out[2*i]*out[2*i]; }
    assert(crossings>=999 && crossings<=1001);
    audio_voice_set_position(v,0); audio_voice_set_volume(v,-600); audio_mix(out,48000,48000);
    double attenuated=0; for (int i=1;i<48000;i++) attenuated+=(double)out[2*i]*out[2*i];
    double ratio=sqrt(attenuated/energy); assert(fabs(ratio-pow(10,-600.0/2000))<0.001);
    audio_voice_set_pan(v,INT32_MAX); audio_mix(out,100,48000); for(int i=0;i<100;i++) assert(out[2*i]==0);
    audio_voice_set_pan(v,INT32_MIN); audio_mix(out,100,48000); for(int i=0;i<100;i++) assert(out[2*i+1]==0);
    audio_voice_set_pan(v,0); audio_voice_set_volume(v,-10000); audio_mix(out,100,48000);
    for(int i=0;i<200;i++) assert(out[i]==0);
    printf("PASS frequency %d Hz, gain %.6f, pan and silence\n",crossings,ratio); audio_voice_free(v);
}
static void cursor_test(void) {
    uint8_t pcm[8]={0}; int16_t out[40]; for(int i=0;i<4;i++) put(pcm+2*i,1000*(i+1));
    AudioVoice *v=audio_voice_new(pcm,8,4,1,16); assert(v); audio_voice_play(v,0);
    audio_mix(out,3,8); positions(v,2); assert(out[0]==1000 && out[2]==1500 && out[4]==2000);
    audio_voice_stop(v); audio_mix(out,3,8); positions(v,2); assert(!audio_voice_playing(v));
    audio_voice_play(v,0); audio_mix(out,5,8); positions(v,8); assert(!audio_voice_playing(v));
    audio_mix(out,1,8); assert(out[0]==0);
    audio_voice_play(v,1); audio_mix(out,7,8); positions(v,6);
    audio_mix(out,1,8); assert(out[0]==2500); positions(v,0);
    audio_voice_set_frequency(v,16); audio_mix(out,3,4); positions(v,0); /* varios bucles por muestra */
    audio_voice_set_frequency(v,0); audio_mix(out,1,4); positions(v,2);
    audio_voice_set_position(v,7); positions(v,6); audio_voice_set_position(v,UINT32_MAX); positions(v,0);
    audio_mix(out,3,0); positions(v,0); for(int i=0;i<6;i++) assert(!out[i]);
    put(pcm,777); audio_mix(out,1,4); assert(out[0]==777); /* PCM prestado, sin copia */
    audio_voice_free(v); puts("PASS resampling, looping, stop, frequency, streaming and cursors");
}
static void formats_test(void) {
    int16_t out[16]; uint8_t pcm[]={0,255,128,128};
    AudioVoice *v=audio_voice_new(pcm,4,48000,2,8); assert(v); audio_voice_play(v,0); audio_mix(out,2,48000);
    assert(out[0]==-32768 && out[1]==32512 && out[2]==0 && out[3]==0); audio_voice_free(v);
    uint8_t stereo[]={0x00,0x80,0xff,0x7f};
    v=audio_voice_new(stereo,4,48000,2,16); AudioVoice *b=audio_voice_new(stereo,4,48000,2,16);
    audio_voice_play(v,1); audio_voice_play(b,1); audio_mix(out,1,48000); assert(out[0]==-32768 && out[1]==32767);
    audio_voice_free(v); audio_voice_free(b);
    assert(!audio_voice_new(NULL,4,1,1,8)); assert(!audio_voice_new(pcm,0,1,1,8));
    assert(!audio_voice_new(pcm,3,1,2,16)); assert(!audio_voice_new(pcm,4,0,1,8));
    assert(!audio_voice_new(pcm,4,1,3,8)); assert(!audio_voice_new(pcm,4,1,1,24));
    audio_voice_free(NULL); audio_voice_play(NULL,1); audio_voice_stop(NULL); audio_voice_set_position(NULL,0);
    audio_voice_set_pan(NULL,0); audio_voice_set_volume(NULL,0); audio_voice_set_frequency(NULL,0);
    positions(NULL,0); assert(!audio_voice_playing(NULL)); audio_mix(NULL,UINT32_MAX,0);
    audio_mix(out,8,48000); for(int i=0;i<16;i++) assert(!out[i]);
    puts("PASS PCM formats, saturation, invalid inputs and empty mixer");
}
static void *mix_thread(void *arg) {
    (void)arg; int16_t out[128]; for(int i=0;i<3000;i++) audio_mix(out,64,48000); return NULL;
}
static void threads_test(void) {
    uint8_t pcm[8]={0}; AudioVoice *v=audio_voice_new(pcm,8,48000,1,16); assert(v);
    pthread_t thread; assert(!pthread_create(&thread,NULL,mix_thread,NULL));
    for(int i=0;i<3000;i++) {
        audio_voice_play(v,1); audio_voice_set_volume(v,-i); audio_voice_set_pan(v,i);
        audio_voice_set_frequency(v,22050); audio_voice_set_position(v,2); positions(NULL,0);
        (void)audio_voice_playing(v); audio_voice_stop(v);
        AudioVoice *temp=audio_voice_new(pcm,8,48000,1,16); assert(temp); audio_voice_play(temp,1); audio_voice_free(temp);
    }
    assert(!pthread_join(thread,NULL)); audio_voice_free(v); puts("PASS concurrent callback and voice controls/lifetime");
}
int main(int argc,char **argv) {
    assert(argc==2);
    if(!strcmp(argv[1],"signal")) signal_test();
    else if(!strcmp(argv[1],"cursor")) cursor_test();
    else if(!strcmp(argv[1],"formats")) formats_test();
    else if(!strcmp(argv[1],"threads")) threads_test();
    else return 2;
    return 0;
}
