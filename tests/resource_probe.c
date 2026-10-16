#include "t123/resources.h"
#include "t123/pattern.h"
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv){
 if(argc<2)return 2;T123Resources b;if(t123_resources_open(&b,argv[1]))return 3;
 for(unsigned i=0;i<3;i++)printf("archive %u: %u files\n",i,b.dat[i].count);
 if(argc==2){for(unsigned j=0;j<b.dat[0].count;j++)if(strstr(b.dat[0].entries[j].name,"reimu")&&strstr(b.dat[0].entries[j].name,"stand"))puts(b.dat[0].entries[j].name);}
 if(argc==5){unsigned char *p;size_t n;if(t123_resource_read(&b,argv[2],&p,&n))return 4;FILE *f=fopen(argv[3],"wb");if(!f)return 5;fwrite(p,1,n,f);fclose(f);free(p);}
 if(argc==6){T123Bitmap m;if(t123_resource_bitmap(&b,argv[2],argv[3],&m))return 6;FILE *f=fopen(argv[4],"wb");if(!f)return 7;uint32_t head[]={m.width,m.height};fwrite(head,4,2,f);fwrite(m.pixels,4,(size_t)m.width*m.height,f);fclose(f);t123_bitmap_free(&m);}
 if(argc==4){T123Pattern p;if(t123_resource_pattern(&b,argv[2],&p))return 8;printf("PAT images=%u moves=%u aliases=%u\n",p.image_count,p.move_count,p.alias_count);FILE *f=fopen(argv[3],"w");if(!f)return 9;for(unsigned i=0;i<p.move_count;i++){T123Move *m=&p.moves[i];for(unsigned j=0;j<m->sequence.count;j++){T123Pose *v=&m->poses[j];fprintf(f,"%d,%u,%u,%u,%u,%d,%d,%u,%u\n",m->action,m->index,j,v->duration,v->damage,v->ox,v->oy,v->hurt_count,v->attack_count);}}fclose(f);t123_pattern_free(&p);}
 t123_resources_close(&b);return 0;
}
