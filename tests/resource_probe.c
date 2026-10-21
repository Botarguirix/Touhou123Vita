#include "t123/resources.h"
#include "t123/pattern.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
static int seen_path(char **seen,unsigned count,const char *path){
 for(unsigned i=0;i<count;i++){const unsigned char *a=(const unsigned char *)seen[i],*b=(const unsigned char *)path;while(*a&&*b&&tolower(*a)==tolower(*b)){a++;b++;}if(!*a&&!*b)return 1;}return 0;
}
int main(int argc,char **argv){
 if(argc<2)return 2;T123Resources b;if(t123_resources_open(&b,argv[1]))return 3;
 if(argc>=3&&!strcmp(argv[2],"--pat-image-decode")){
  FILE *audit=stdout;if(argc>=4){audit=fopen(argv[3],"wb");if(!audit){t123_resources_close(&b);return 4;}setvbuf(audit,NULL,_IOFBF,65536);}
  char *seen[128]={0};unsigned seen_count=0,pat_count=0,total=0,decoded=0,unreferenced=0,missing=0,no_palette=0,unsupported=0;
  fprintf(audit,"character\tpat\timage_index\timage_name\tpose_refs\tdamaging_pose_refs\tbpp\twidth\theight\tstatus\n");
  /* Match runtime lookup priority: th123c > th123b > th123a > th105b > th105a. */
  for(int a=4;a>=0;a--)if(b.opened&(1u<<a))for(uint32_t j=0;j<b.dat[a].count;j++){
   const char *name=b.dat[a].entries[j].name,*prefix="data/character/";
   if(strncmp(name,prefix,strlen(prefix)))continue;
   const char *slash=strrchr(name,'/');if(!slash)continue;
   size_t folder=(size_t)(slash-(name+strlen(prefix)));
   if(!folder||strlen(slash+1)!=folder+4||strncmp(name+strlen(prefix),slash+1,folder)||strcmp(slash+1+folder,".pat"))continue;
   if(seen_path(seen,seen_count,name)||seen_count>=128)continue;
   seen[seen_count]=strdup(name);if(!seen[seen_count])continue;++seen_count;
   T123Pattern p={0};if(t123_resource_pattern(&b,name,&p)){fprintf(stderr,"PAT decode failed: %s\n",name);continue;}++pat_count;
   uint32_t *refs=calloc(p.image_count,sizeof *refs),*damage=calloc(p.image_count,sizeof *damage);
   if(!refs||!damage){free(refs);free(damage);t123_pattern_free(&p);continue;}
   for(uint32_t m=0;m<p.move_count;m++)for(unsigned q=0;q<p.moves[m].sequence.count;q++){
    const T123Pose *pose=&p.moves[m].poses[q];if(pose->image>=p.image_count)continue;++refs[pose->image];
    if(pose->damage&&(pose->attack_count||pose->attack_flags))++damage[pose->image];
   }
   char character[128];if(folder>=sizeof character)folder=sizeof character-1;memcpy(character,name+strlen(prefix),folder);character[folder]=0;
   for(uint32_t image=0;image<p.image_count;image++){
    char filename[160],resource[320],palette[256];snprintf(filename,sizeof filename,"%s",p.images[image]);
    char *dot=strrchr(filename,'.');if(dot)strcpy(dot,".cv2");
    snprintf(resource,sizeof resource,"data/character/%s/%s",character,filename);
    snprintf(palette,sizeof palette,"data/character/%s/palette000.pal",character);
    unsigned char *bytes=NULL,*pal=NULL;size_t size=0,pal_size=0;T123Bitmap bitmap={0};const char *status="decoded";unsigned bpp=0;
    if(!refs[image]){status="unreferenced";++unreferenced;}
    else if(t123_resource_read(&b,resource,&bytes,&size)){status="missing_resource";++missing;}
    else{
     if(size)bpp=bytes[0];
     if(bpp==8&&t123_resource_read(&b,palette,&pal,&pal_size)){status="missing_palette";++no_palette;}
     else if(t123_bitmap_decode(bytes,size,pal,pal_size,&bitmap)){status="unsupported_or_invalid_cv2";++unsupported;}
     else{++decoded;}
    }
    fprintf(audit,"%s\t%s\t%u\t%s\t%u\t%u\t%u\t%u\t%u\t%s\n",character,name,image,p.images[image],refs[image],damage[image],bpp,bitmap.width,bitmap.height,status);
    ++total;t123_bitmap_free(&bitmap);free(bytes);free(pal);
   }
   free(refs);free(damage);t123_pattern_free(&p);
  }
  for(unsigned i=0;i<seen_count;i++)free(seen[i]);
  fprintf(audit,"# summary pats=%u images=%u decoded=%u unreferenced=%u missing_resource=%u missing_palette=%u unsupported_or_invalid=%u\n",pat_count,total,decoded,unreferenced,missing,no_palette,unsupported);
  if(audit!=stdout)fclose(audit);
  t123_resources_close(&b);return 0;
 }
 if(argc==3&&!strcmp(argv[2],"--pat-archive-idle")){
  puts("archive\tpath\tpat_bytes\timages\tidle_poses\tfound\tidle_image_paths");
  for(unsigned a=0;a<5;a++)if(b.opened&(1u<<a))for(uint32_t j=0;j<b.dat[a].count;j++){
   const char *name=b.dat[a].entries[j].name;const char *prefix="data/character/";
   if(strncmp(name,prefix,strlen(prefix)))continue;
   const char *slash=strrchr(name,'/');if(!slash)continue;
   size_t folder=(size_t)(slash-(name+strlen(prefix)));
   if(!folder||strlen(slash+1)!=folder+4||strncmp(name+strlen(prefix),slash+1,folder)||strcmp(slash+1+folder,".pat"))continue;
   int duplicate=0;for(uint32_t k=0;k<j;k++)if(!strcmp(b.dat[a].entries[k].name,name)){duplicate=1;break;}if(duplicate)continue;
   unsigned char *bytes=NULL;size_t size=0;T123Pattern p={0};
   if(t123_dat_read(&b.dat[a],name,&bytes,&size)||t123_pattern_decode(bytes,size,&p)){free(bytes);printf("%u\t%s\t%zu\tERROR\n",a,name,size);continue;}free(bytes);
   const T123Move *idle=t123_pattern_move(&p,0,0);if(!idle)for(uint32_t k=0;k<p.move_count;k++)if(p.moves[k].action==0){idle=&p.moves[k];break;}
   unsigned poses=idle?idle->sequence.count:0,found=0;char refs[1536]={0};size_t used=0;
   for(unsigned q=0;q<poses;q++){
    const char *image=p.images[idle->poses[q].image];char image_path[256],filename[129];snprintf(filename,sizeof filename,"%s",image);
    char *dot=strrchr(filename,'.');if(dot)strcpy(dot,".cv2");
    int n=snprintf(image_path,sizeof image_path,"%.*s%s",(int)(slash-name+1),name,filename);if(n<0||(size_t)n>=sizeof image_path)continue;
    unsigned mask=0;for(unsigned d=0;d<5;d++)if(b.opened&(1u<<d)){unsigned char *asset=NULL;size_t asset_size=0;if(t123_dat_read(&b.dat[d],image_path,&asset,&asset_size)==0){mask|=1u<<d;free(asset);}}
    if(mask)++found;
    if(used<sizeof refs){n=snprintf(refs+used,sizeof refs-used,"%s%s@%x",q?",":"",image_path,mask);if(n>0)used+=(size_t)n<sizeof refs-used?(size_t)n:sizeof refs-used;}
   }
   printf("%u\t%s\t%zu\t%u\t%u\t%u\t%s\n",a,name,size,p.image_count,poses,found,refs);
   t123_pattern_free(&p);
  }
  t123_resources_close(&b);return 0;
 }
 if(argc==3&&!strcmp(argv[2],"--pat-inventory")){
  char *seen[128]={0};unsigned seen_count=0;puts("path\timages\tmoves\taliases\tposes\tdamaging_poses");
  for(unsigned i=0;i<5;i++)for(uint32_t j=0;j<b.dat[i].count;j++){
   const char *name=b.dat[i].entries[j].name;const char *prefix="data/character/";
   if(strncmp(name,prefix,strlen(prefix)))continue;
   const char *slash=strrchr(name,'/');if(!slash)continue;
   size_t folder=(size_t)(slash-(name+strlen(prefix)));
   if(!folder||strlen(slash+1)!=folder+4||strncmp(name+strlen(prefix),slash+1,folder)||strcmp(slash+1+folder,".pat"))continue;
   int duplicate=0;for(unsigned k=0;k<seen_count;k++)if(!strcmp(seen[k],name)){duplicate=1;break;}if(duplicate)continue;
   if(seen_count>=128)continue;seen[seen_count]=strdup(name);if(!seen[seen_count])continue;++seen_count;
   T123Pattern p;if(t123_resource_pattern(&b,name,&p)){printf("%s\tERROR\n",name);continue;}
   unsigned poses=0,damaging=0;for(uint32_t k=0;k<p.move_count;k++)for(unsigned q=0;q<p.moves[k].sequence.count;q++){
    const T123Pose *v=&p.moves[k].poses[q];++poses;if(v->damage&&(v->attack_count||v->attack_flags))++damaging;
   }
   printf("%s\t%u\t%u\t%u\t%u\t%u\n",name,p.image_count,p.move_count,p.alias_count,poses,damaging);
   t123_pattern_free(&p);
  }
  for(unsigned i=0;i<seen_count;i++)free(seen[i]);t123_resources_close(&b);return 0;
 }
 if(argc==3&&!strcmp(argv[2],"--pat-attacks")){
  char *seen[128]={0};unsigned seen_count=0;puts("path\taction\tsequence\tposes\tdamaging_poses\tmax_damage\tmax_attack_boxes");
  for(unsigned i=0;i<5;i++)for(uint32_t j=0;j<b.dat[i].count;j++){
   const char *name=b.dat[i].entries[j].name;const char *prefix="data/character/";
   if(strncmp(name,prefix,strlen(prefix)))continue;
   const char *slash=strrchr(name,'/');if(!slash)continue;
   size_t folder=(size_t)(slash-(name+strlen(prefix)));
   if(!folder||strlen(slash+1)!=folder+4||strncmp(name+strlen(prefix),slash+1,folder)||strcmp(slash+1+folder,".pat"))continue;
   int duplicate=0;for(unsigned k=0;k<seen_count;k++)if(!strcmp(seen[k],name)){duplicate=1;break;}if(duplicate)continue;
   if(seen_count>=128)continue;seen[seen_count]=strdup(name);if(!seen[seen_count])continue;++seen_count;
   T123Pattern p;if(t123_resource_pattern(&b,name,&p)){printf("%s\tERROR\n",name);continue;}
   for(uint32_t k=0;k<p.move_count;k++){
    const T123Move *m=&p.moves[k];unsigned damage_frames=0,max_damage=0,max_boxes=0;
    for(unsigned q=0;q<m->sequence.count;q++){
     const T123Pose *v=&m->poses[q];if(v->damage&&(v->attack_count||v->attack_flags)){
      ++damage_frames;if(v->damage>max_damage)max_damage=v->damage;if(v->attack_count>max_boxes)max_boxes=v->attack_count;
     }
    }
    if(damage_frames)printf("%s\t%d\t%u\t%u\t%u\t%u\t%u\n",name,m->action,m->index,m->sequence.count,damage_frames,max_damage,max_boxes);
   }
   t123_pattern_free(&p);
  }
  for(unsigned i=0;i<seen_count;i++)free(seen[i]);t123_resources_close(&b);return 0;
 }
 if(argc==3&&!strcmp(argv[2],"--pat-detail")){
  char *seen[128]={0};unsigned seen_count=0;
  puts("path\taction\tindex\tloop\tmove_lock\taction_lock\tpose\timage\timage_name\ttx\tty\ttw\tth\tduration\tdamage\tchip\tenemy_stun\tblock_stun\tattack_flags\tattack_boxes");
  for(unsigned i=0;i<5;i++)for(uint32_t j=0;j<b.dat[i].count;j++){
   const char *name=b.dat[i].entries[j].name;const char *prefix="data/character/";
   if(strncmp(name,prefix,strlen(prefix)))continue;
   const char *slash=strrchr(name,'/');if(!slash)continue;
   size_t folder=(size_t)(slash-(name+strlen(prefix)));
   if(!folder||strlen(slash+1)!=folder+4||strncmp(name+strlen(prefix),slash+1,folder)||strcmp(slash+1+folder,".pat"))continue;
   int duplicate=0;for(unsigned k=0;k<seen_count;k++)if(!strcmp(seen[k],name)){duplicate=1;break;}if(duplicate)continue;
   if(seen_count>=128)continue;seen[seen_count]=strdup(name);if(!seen[seen_count])continue;++seen_count;
   T123Pattern p;if(t123_resource_pattern(&b,name,&p)){printf("%s\tERROR\n",name);continue;}
   for(uint32_t k=0;k<p.move_count;k++){
    const T123Move *m=&p.moves[k];
    for(unsigned q=0;q<m->sequence.count;q++){
     const T123Pose *v=&m->poses[q];printf("%s\t%d\t%u\t%u\t%u\t%u\t%u\t%u\t%s\t%d\t%d\t%d\t%d\t%u\t%u\t%u\t%u\t%u\t0x%08x\t",name,m->action,m->index,m->sequence.loop,m->move_lock,m->action_lock,q,v->image,p.images[v->image],v->tx,v->ty,v->tw,v->th,v->duration,v->damage,v->chip,v->enemy_stun,v->block_stun,v->attack_flags);
     if(!v->attack_count)putchar('-');
     for(unsigned z=0;z<v->attack_count;z++){const T123Box *box=&v->attack[z];if(z)putchar(';');printf("%d,%d,%d,%d",box->left,box->up,box->right,box->down);}
     putchar('\n');
    }
   }
   t123_pattern_free(&p);
  }
  for(unsigned i=0;i<seen_count;i++)free(seen[i]);t123_resources_close(&b);return 0;
 }
 if(argc==3&&!strcmp(argv[2],"--manifest")){
  puts("archive\toffset\tsize\tpath");
  for(unsigned i=0;i<5;i++)for(uint32_t j=0;j<b.dat[i].count;j++)
   printf("%u\t%u\t%u\t%s\n",i,b.dat[i].entries[j].offset,b.dat[i].entries[j].size,b.dat[i].entries[j].name);
  t123_resources_close(&b);return 0;
 }
 for(unsigned i=0;i<5;i++)printf("archive %u: %u files\n",i,b.dat[i].count);
 if(argc==2){for(unsigned j=0;j<b.dat[0].count;j++)if(strstr(b.dat[0].entries[j].name,"reimu")&&strstr(b.dat[0].entries[j].name,"stand"))puts(b.dat[0].entries[j].name);}
 if(argc==5){unsigned char *p;size_t n;if(t123_resource_read(&b,argv[2],&p,&n))return 4;FILE *f=fopen(argv[3],"wb");if(!f)return 5;fwrite(p,1,n,f);fclose(f);free(p);}
 if(argc==6){T123Bitmap m;if(t123_resource_bitmap(&b,argv[2],argv[3],&m))return 6;FILE *f=fopen(argv[4],"wb");if(!f)return 7;uint32_t head[]={m.width,m.height};fwrite(head,4,2,f);fwrite(m.pixels,4,(size_t)m.width*m.height,f);fclose(f);t123_bitmap_free(&m);}
 if(argc==4){T123Pattern p;if(t123_resource_pattern(&b,argv[2],&p))return 8;printf("PAT images=%u moves=%u aliases=%u\n",p.image_count,p.move_count,p.alias_count);FILE *f=fopen(argv[3],"w");if(!f)return 9;for(unsigned i=0;i<p.move_count;i++){T123Move *m=&p.moves[i];for(unsigned j=0;j<m->sequence.count;j++){T123Pose *v=&m->poses[j];fprintf(f,"%d,%u,%u,%u,%u,%d,%d,%u,%u\n",m->action,m->index,j,v->duration,v->damage,v->ox,v->oy,v->hurt_count,v->attack_count);}}fclose(f);t123_pattern_free(&p);}
 t123_resources_close(&b);return 0;
}
