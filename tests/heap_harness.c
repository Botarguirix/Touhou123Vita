/* Casos independientes: ejecutar cada modo en un proceso nuevo.
 * No se reinician ni se inspeccionan las listas privadas de support.c.
 * Los casos oversize-* son reproducciones de fallos y DEBEN fallar hasta que
 * Claude corrija el allocator: no se modifica su implementacion desde T10. */
#include "win32.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"FAIL %d: %s\n",__LINE__,#x); return 1; } } while(0)
#define MIB (1024u*1024u)
static uint8_t pattern(unsigned tag,unsigned i) { return (uint8_t)(tag*37u+i*13u+(i>>8)); }
static void fill(uint32_t p,uint32_t n,unsigned tag) {
    for (uint32_t i=0;i<n;++i) wr8(p+i,pattern(tag,i));
}
static int preserved(uint32_t p,uint32_t n,unsigned tag) {
    for (uint32_t i=0;i<n;++i) if (rd8(p+i)!=pattern(tag,i)) return 0;
    return 1;
}
static int alignment(void) {
    const uint32_t sizes[]={0,1,15,16,17,255,256,4095,4096,4097,8192,MIB};
    uint32_t pointers[sizeof sizes/sizeof sizes[0]];
    for (unsigned i=0;i<sizeof sizes/sizeof sizes[0];++i) {
        uint32_t p=heap_alloc(sizes[i],1);pointers[i]=p;
        CHECK(p && !(p&15));CHECK(heap_size(p)==sizes[i]);
        for (uint32_t j=0;j<sizes[i];++j) CHECK(rd8(p+j)==0);
        fill(p,sizes[i],i+1);
    }
    for (unsigned i=0;i<sizeof sizes/sizeof sizes[0];++i) {
        CHECK(preserved(pointers[i],sizes[i],i+1));heap_free(pointers[i]);
        CHECK(heap_size(pointers[i])==UINT32_MAX);
    }
    heap_free(0);CHECK(heap_size(0)==UINT32_MAX);return 0;
}
static int reuse(void) {
    uint32_t a=heap_alloc(3*MIB,0),guard=heap_alloc(8192,0);CHECK(a && guard);
    uint32_t top=heap_used();heap_free(a);
    CHECK(heap_alloc(3*MIB,0)==a && heap_used()==top);
    uint32_t small=heap_alloc(17,0);heap_free(small);
    CHECK(heap_alloc(17,0)==small);return 0;
}
static int split(void) {
    uint32_t a=heap_alloc(4*MIB,0),guard=heap_alloc(8192,0);CHECK(a && guard);
    uint32_t top=heap_used();heap_free(a);
    uint32_t left=heap_alloc(MIB,0),right=heap_alloc(3*MIB-16,0);
    CHECK(left==a && right==a+MIB+16 && heap_used()==top);
    CHECK(heap_size(left)==MIB && heap_size(right)==3*MIB-16);
    fill(left,MIB,1);fill(right,3*MIB-16,2);
    CHECK(preserved(left,MIB,1) && preserved(right,3*MIB-16,2));return 0;
}
static int coalesce(void) {
    uint32_t a=heap_alloc(MIB,0),b=heap_alloc(MIB,0),c=heap_alloc(MIB,0);
    CHECK(a && b && c && heap_alloc(8192,0));uint32_t top=heap_used();
    heap_free(a);heap_free(c);heap_free(b); /* une a ambos vecinos en la misma llamada */
    uint32_t whole=heap_alloc(3*MIB+32,0);CHECK(whole==a && heap_used()==top);
    CHECK(heap_size(whole)==3*MIB+32);heap_free(whole);
    a=heap_alloc(MIB,0);b=heap_alloc(MIB,0);c=heap_alloc(MIB,0);
    heap_free(c);heap_free(b);heap_free(a); /* fusion con vecino superior */
    CHECK(heap_alloc(3*MIB+32,0)==a && heap_used()==top);return 0;
}
static int realloc_case(void) {
    uint32_t a=heap_realloc(0,100,1);CHECK(a && heap_size(a)==100);
    for (unsigned i=0;i<100;++i) CHECK(!rd8(a+i));
    fill(a,100,77);
    uint32_t b=heap_realloc(a,10000,1);CHECK(b && b!=a && heap_size(b)==10000);
    CHECK(preserved(b,100,77));
    for (unsigned i=100;i<10000;++i) CHECK(!rd8(b+i));
    fill(b,10000,89);
    uint32_t c=heap_realloc(b,10,0);CHECK(c==b && heap_size(c)==10 && preserved(c,10,89));
    CHECK(heap_realloc(c,100,1)==c && heap_size(c)==100);
    CHECK(preserved(c,10,89));for (unsigned i=10;i<100;++i) CHECK(!rd8(c+i));
    CHECK(heap_realloc(c,0,0)==c && heap_size(c)==0);heap_free(c);return 0;
}
static int exhaustion(void) {
    uint32_t canary=heap_alloc(64,0);CHECK(canary);fill(canary,64,93);
    uint32_t blocks[100];unsigned count=0;
    while (count<100) {
        uint32_t p=heap_alloc(MIB,0);if (!p) break;
        blocks[count++]=p;fill(p,MIB,count);
    }
    CHECK(count>0 && count<100);uint32_t used=heap_used();
    CHECK(heap_alloc(MIB,0)==0 && heap_used()==used && preserved(canary,64,93));
    uint32_t old_size=heap_size(canary);
    CHECK(heap_realloc(canary,2*MIB,0)==0 && heap_size(canary)==old_size && preserved(canary,64,93));
    for (unsigned i=0;i<count;++i) CHECK(preserved(blocks[i],MIB,i+1));
    for (unsigned i=0;i<count;++i) heap_free(blocks[i]);
    CHECK(heap_alloc(MIB,0)==blocks[0]);
    printf("exhaustion blocks=%u heap_used=%u\n",count,used);return 0;
}
typedef struct { uint32_t p,size;unsigned tag; } Live;
static uint32_t random_state=0x5eed1234u;
static uint32_t rng(void) {
    random_state^=random_state<<13;random_state^=random_state>>17;random_state^=random_state<<5;
    return random_state;
}
static uint32_t random_size(void) {
    return (rng()%10)==0 ? 4097+rng()%(256*1024) : rng()%8193;
}
static int valid_new(Live live[128],unsigned changed) {
    Live a=live[changed];CHECK(a.p && !(a.p&15));CHECK(heap_size(a.p)==a.size);
    uint64_t end=(uint64_t)a.p+(a.size ? a.size:1);
    CHECK(a.p>=GUEST_HEAP_BASE+16 && end<=GUEST_HEAP_BASE+GUEST_HEAP_SIZE);
    for (unsigned i=0;i<128;++i) if (i!=changed && live[i].p) {
        uint64_t other_end=(uint64_t)live[i].p+(live[i].size ? live[i].size:1);
        CHECK(end<=live[i].p || other_end<=a.p);
    }
    return 0;
}
static int random_case(void) {
    Live live[128]={{0}};unsigned allocations=0,frees=0,reallocations=0,failures=0;
    for (unsigned operation=0;operation<100000;++operation) {
        unsigned index=rng()%128;Live old=live[index];
        if (old.p) CHECK(heap_size(old.p)==old.size && preserved(old.p,old.size,old.tag));
        if (!old.p) {
            uint32_t size=random_size(),p=heap_alloc(size,0);
            if (!p) { ++failures;continue; }
            live[index]=(Live){p,size,rng()};CHECK(valid_new(live,index)==0);
            fill(p,size,live[index].tag);++allocations;
        } else if (rng()%100<45) {
            heap_free(old.p);live[index]=(Live){0};++frees;
        } else {
            uint32_t size=random_size(),p=heap_realloc(old.p,size,0);
            if (!p) { CHECK(heap_size(old.p)==old.size && preserved(old.p,old.size,old.tag));++failures;continue; }
            CHECK(preserved(p,old.size<size ? old.size:size,old.tag));
            live[index]=(Live){p,size,rng()};CHECK(valid_new(live,index)==0);
            fill(p,size,live[index].tag);++reallocations;
        }
    }
    uint64_t bytes=0;unsigned count=0;
    for (unsigned i=0;i<128;++i) if (live[i].p) {
        CHECK(valid_new(live,i)==0 && preserved(live[i].p,live[i].size,live[i].tag));
        bytes+=live[i].size;++count;
    }
    uint32_t used=heap_used();
    printf("{\"seed\":1592594996,\"operations\":100000,\"allocations\":%u,\"frees\":%u,\"reallocations\":%u,\"failed_requests\":%u,\"live_blocks\":%u,\"live_bytes\":%" PRIu64 ",\"heap_top\":%u,\"heap_used\":%u,\"holes_slack_headers\":%" PRIu64 "}\n",
           allocations,frees,reallocations,failures,count,bytes,GUEST_HEAP_BASE+used,used,(uint64_t)used-bytes);
    for (unsigned i=0;i<128;++i) heap_free(live[i].p);
    return 0;
}
int main(int argc,char **argv) {
    CHECK(argc==2);CHECK(!guest_mem_init());int result;
    if (!strcmp(argv[1],"alignment")) result=alignment();
    else if (!strcmp(argv[1],"reuse")) result=reuse();
    else if (!strcmp(argv[1],"split")) result=split();
    else if (!strcmp(argv[1],"coalesce")) result=coalesce();
    else if (!strcmp(argv[1],"realloc")) result=realloc_case();
    else if (!strcmp(argv[1],"exhaustion")) result=exhaustion();
    else if (!strcmp(argv[1],"random")) result=random_case();
    else if (!strcmp(argv[1],"oversize-round") || !strcmp(argv[1],"oversize-end")) {
        uint32_t requested=!strcmp(argv[1],"oversize-round") ? UINT32_MAX:0xfffffff0u;
        if (requested==0xfffffff0u) CHECK(heap_alloc(1,0));
        uint32_t p=heap_alloc(requested,0);
        printf("oversize request=%u pointer=0x%08x heap_used=%u\n",requested,p,heap_used());
        if (requested==0xfffffff0u && p) {
            uint32_t next=heap_alloc(16,0);
            printf("overlap following=0x%08x equals_invalid=%u\n",next,next==p);
        }
        CHECK(p==0);result=0;
    } else { fprintf(stderr,"unknown mode\n");return 2; }
    trace_close();if (!result) printf("PASS heap %s\n",argv[1]);return result;
}
