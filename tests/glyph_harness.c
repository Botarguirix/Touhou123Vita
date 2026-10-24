#include "glyph.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x); return 1; } } while (0)
extern uint32_t glyph_test_bytes(void),glyph_test_count(void),glyph_test_entry_size(void);
extern const char *glyph_test_family(void);
extern int glyph_test_units(void),glyph_test_ascender(void),glyph_test_descender(void);
static int check_glyph(int height,int weight,uint16_t code) {
    GlyphMetrics gm,second;uint32_t n=glyph_gray4(height,weight,code,&gm,NULL,0);
    CHECK(n!=UINT32_MAX);
    uint32_t pitch=(gm.black_box_x+3)&~3u;
    CHECK(n==pitch*gm.black_box_y);
    uint8_t *buf=malloc(n+16);CHECK(buf);memset(buf,0xab,n+16);
    CHECK(glyph_gray4(height,weight,code,&second,buf,0)==n && buf[0]==0xab);
    CHECK(glyph_gray4(height,weight,code,&second,buf,n)==n);
    CHECK(!memcmp(&gm,&second,sizeof gm));
    for (unsigned y=0;y<gm.black_box_y;++y) {
        for (unsigned x=0;x<pitch;++x) {
            CHECK(buf[y*pitch+x]<=16);
            if (x>=gm.black_box_x) CHECK(buf[y*pitch+x]==0);
        }
    }
    for (unsigned i=0;i<16;++i) CHECK(buf[n+i]==0xab);
    uint8_t *repeat=malloc(n+1);CHECK(repeat);
    CHECK(glyph_gray4(height,weight,code,&second,repeat,n)==n);
    CHECK(!memcmp(buf,repeat,n));
    if (n>1) {
        memset(repeat,0xab,n);
        CHECK(glyph_gray4(height,weight,code,&second,repeat,n-1)==UINT32_MAX);
        for (unsigned i=0;i<n;++i) CHECK(repeat[i]==0xab);
    }
    printf("metrics %d %d U+%04X %u %u %d %d %d %d %u\n",height,weight,code,
           gm.black_box_x,gm.black_box_y,gm.origin_x,gm.origin_y,gm.cell_inc_x,gm.cell_inc_y,n);
    free(buf);free(repeat);return 0;
}
static void *worker(void *arg) {
    unsigned *failed=arg;GlyphMetrics gm;
    for (unsigned i=0;i<100;++i) {
        uint8_t buf[4096];
        if (glyph_gray4(24,400,(uint16_t)(0x4e00+i),&gm,buf,sizeof buf)==UINT32_MAX) *failed=1;
    }
    return NULL;
}
static int image(const char *path) {
    enum { W=640,H=180 };static uint8_t pixels[W*H];memset(pixels,255,sizeof pixels);
    const uint16_t text[]={'T','o','u','h','o','u',' ','V','i','t','a',' ','1','2','3',' ',0x65e5,0x672c,0x8a9e,' ',0x6f22,0x5b57,0};
    for (int row=0;row<3;++row) {
        int x=12,baseline=40+row*55,height=row==0?24:row==1?32:-24;
        for (unsigned i=0;text[i];++i) {
            GlyphMetrics gm;uint8_t buf[8192];
            uint32_t n=glyph_gray4(height,row==1?700:400,text[i],&gm,buf,sizeof buf);
            CHECK(n!=UINT32_MAX);unsigned pitch=(gm.black_box_x+3)&~3u;
            for (unsigned by=0;by<gm.black_box_y;++by) for (unsigned bx=0;bx<gm.black_box_x;++bx) {
                int dx=x+gm.origin_x+(int)bx,dy=baseline-gm.origin_y+(int)by;
                if (dx>=0 && dx<W && dy>=0 && dy<H) pixels[dy*W+dx]=(uint8_t)(255-buf[by*pitch+bx]*255u/16);
            }
            x+=gm.cell_inc_x;
        }
    }
    FILE *f=fopen(path,"wb");CHECK(f);fprintf(f,"P5\n%d %d\n255\n",W,H);
    CHECK(fwrite(pixels,1,sizeof pixels,f)==sizeof pixels);CHECK(!fclose(f));
    puts("PASS glyph image");return 0;
}
int main(int argc,char **argv) {
    CHECK(argc>=2);GlyphMetrics gm;
    CHECK(sizeof(GlyphMetrics)==20);
    CHECK(glyph_gray4(14,400,'A',&gm,NULL,0)==UINT32_MAX);
    CHECK(glyph_init(argv[1])==0);
    printf("font %s units=%d ascender=%d descender=%d entry=%u\n",glyph_test_family(),
           glyph_test_units(),glyph_test_ascender(),glyph_test_descender(),glyph_test_entry_size());
    if (argc==4 && !strcmp(argv[2],"image")) return image(argv[3]);
    if (argc==3 && !strcmp(argv[2],"metrics")) {
        const int heights[]={14,24,-17}; const uint16_t codes[]={'A',' ',0x6f22};
        for (unsigned h=0;h<3;++h) for (unsigned c=0;c<3;++c)
            CHECK(check_glyph(heights[h],400,codes[c])==0);
        return 0;
    }
    if (argc==4 && !strcmp(argv[2],"measure")) {
        FILE *f=fopen(argv[3],"r");CHECK(f);unsigned code,count=0;
        while (fscanf(f,"%x",&code)==1) {
            CHECK(glyph_gray4(24,400,(uint16_t)code,&gm,NULL,0)!=UINT32_MAX);++count;
        }
        CHECK(!fclose(f));CHECK(count==2000 && glyph_test_count()==2000);
        printf("cache glyphs=%u bytes=%u payload=%u\n",count,glyph_test_bytes(),
               glyph_test_bytes()-count*glyph_test_entry_size());return 0;
    }
    CHECK(glyph_init("missing-font-for-test.otf")!=0);
    CHECK(check_glyph(14,400,'A')==0 && check_glyph(24,400,0x6f22)==0);
    CHECK(check_glyph(-17,700,0x6f22)==0 && check_glyph(24,400,' ')==0);
    CHECK(glyph_gray4(24,400,' ',&gm,NULL,0)==0 && gm.cell_inc_x>0);
    uint32_t before=glyph_test_bytes();
    CHECK(glyph_gray4(24,400,0x6f22,&gm,NULL,0)!=UINT32_MAX && glyph_test_bytes()==before);
    CHECK(glyph_gray4(INT32_MIN,400,'A',&gm,NULL,0)==UINT32_MAX);
    CHECK(glyph_gray4(24,400,0xd800,&gm,NULL,0)==UINT32_MAX);
    CHECK(glyph_gray4(24,400,'A',NULL,NULL,0)==UINT32_MAX);
    GlyphMetrics normal,bold;uint8_t a[8192],b[8192];
    uint32_t an=glyph_gray4(24,400,0x6f22,&normal,a,sizeof a),bn=glyph_gray4(24,700,0x6f22,&bold,b,sizeof b);
    CHECK(an!=UINT32_MAX && bn!=UINT32_MAX);
    unsigned ae=0,be=0;for (unsigned i=0;i<an;++i) ae+=a[i];for (unsigned i=0;i<bn;++i) be+=b[i];
    CHECK(be>ae);
    unsigned failed[4]={0};pthread_t threads[4];
    for (unsigned i=0;i<4;++i) CHECK(pthread_create(&threads[i],NULL,worker,&failed[i])==0);
    for (unsigned i=0;i<4;++i) { CHECK(!pthread_join(threads[i],NULL));CHECK(!failed[i]); }
    for (unsigned i=0;i<5000;++i) CHECK(glyph_gray4(24,400,(uint16_t)(0x4e00+i),&gm,NULL,0)!=UINT32_MAX);
    CHECK(glyph_test_bytes()<=8u*1024u*1024u && glyph_test_count()<=4096);
    CHECK(glyph_init(argv[1])==0 && glyph_test_count()==0 && glyph_test_bytes()==0);
    puts("PASS glyph contracts, cache, bold and threads");return 0;
}
