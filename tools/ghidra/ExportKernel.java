// @category Touhou123Vita.Analysis
// Selected functions and vtables from the exact local reference image.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public class ExportKernel extends GhidraScript {
    public void run() throws Exception {
        String[] a=getScriptArgs();
        boolean resourcesOnly=a.length==3&&a[2].equalsIgnoreCase("resources");
        if((a.length!=2&&!resourcesOnly) || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Reference hash mismatch");
        Path out=Paths.get(a[0]);Files.createDirectories(out);
        List<String> rows=new ArrayList<>();DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
        Set<Long> targets=new LinkedHashSet<>();
        if(!resourcesOnly){
            // Shared input helpers for ground/air attacks and dash/flight routing.
            // 0x487ba0 is intentionally omitted: SokuLib identifies it as useSkill.
            long[] refs={0x438c60L,0x4640b0L,0x464200L,0x465e10L,0x47c770L,0x47a040L,0x47a5b0L,0x47a740L,0x47a110L,0x479e10L,
                         0x487020L,0x487740L,0x4877c0L,0x487900L,0x487990L,0x487ab0L,
                         0x489610L,0x489e90L,0x48a220L,0x48a380L,0x48a470L,0x48a560L,
                         0x4397f0L,0x439850L,0x4636b0L,0x43e9a0L,0x4396c0L,
                         // Input history map lookup used by FUN_00489610.
                         0x43f2f0L};
            for(long v:refs)targets.add(v);
            // Record scalar xrefs for common input/BE handlers, retaining exact instructions
            // and containing functions for the next Ghidra review pass.
            Set<Long> fields=new HashSet<>(Arrays.asList(0x4fL,0x80eL,0x128L,0x14bL,0x41L,0x4bL,
                0x1d5L,0x1d6L,0x1d7L,0x1d8L,0x1d9L,0x1ddL,0x1deL,0x1dfL,0x1e0L,0x1e1L,
                0x1e5L,0x1e6L,0x1e7L,0x1f1L));
            for(Instruction ins:currentProgram.getListing().getInstructions(true)){
                for(int op=0;op<ins.getNumOperands();op++){
                    Object[] operandRefs=ins.getOpObjects(op);
                    for(Object ref:operandRefs)if(ref instanceof Scalar){
                        long field=((Scalar)ref).getUnsignedValue();
                        if(fields.contains(field)){
                            Function caller=getFunctionContaining(ins.getAddress());
                            if(caller!=null){rows.add(String.format("field-ref\t%04x\t%s\t%s\t%s",field,ins.getAddress(),ins.getMnemonicString(),caller.getEntryPoint()));targets.add(caller.getEntryPoint().getOffset());}
                        }
                    }
                }
            }
            long[] tables={0x85bf4cL,0x85eab4L,0x8588ecL};
            for(long table:tables)for(int slot=0;slot<25;slot++){
                long addr=Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(table+slot*4)));
                rows.add(String.format("vtable\t%08x\t%d\t%08x",table,slot,addr));
                if(addr>=0x401000L && addr<0x857000L && (slot==8||slot==3||slot==5||slot==7||slot==10||slot==15||slot==16||slot==20))targets.add(addr);
            }
        }
        // Follow direct references to image/PAT extension strings. These
        // callers reveal the real resource lookup path, including any name
        // rewriting or shared-atlas indirection.
        List<String> resourceRefs=new ArrayList<>();
        if(resourcesOnly){
            long[] loaderHelpers={0x405030L,0x408be0L,0x408cf0L,0x409150L,0x40d1e0L,0x41c080L,0x41c530L,0x419b70L,0x419f90L,0x409b50L,0x40d1d0L,0x41c9b0L,0x41c350L,0x41c440L,0x41b900L};
            for(long helper:loaderHelpers)targets.add(helper);
            for(long global:new long[]{0x896b80L,0x896b84L,0x896b8cL,0x8a0048L,0x8a006cL,0x8a0070L,0x8a007cL}){
                if(global==0x8a0048L || global==0x8a006cL || global==0x8a0070L || global==0x8a007cL){
                    ReferenceIterator globalRefs=currentProgram.getReferenceManager().getReferencesTo(toAddr(global));
                    while(globalRefs.hasNext()){
                        Reference reference=globalRefs.next();Function caller=getFunctionContaining(reference.getFromAddress());
                        if(caller!=null){rows.add(String.format("global-ref	%08x	%s	%s",global,reference.getFromAddress(),caller.getEntryPoint()));targets.add(caller.getEntryPoint().getOffset());}
                    }
                }
                try {
                    rows.add(String.format("global\t%08x\t%08x",global,Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(global)))));
                } catch(Exception ignored) { rows.add(String.format("global\t%08x\tUNAVAILABLE",global)); }
            }
        }
        byte[] buffer=new byte[65536];
        for(MemoryBlock block:currentProgram.getMemory().getBlocks()){
            if(!block.isInitialized())continue;
            StringBuilder run=new StringBuilder();Address runStart=null;long offset=0;
            while(offset<block.getSize()){
                int wanted=(int)Math.min(buffer.length,block.getSize()-offset);
                Address chunk=block.getStart().add(offset);byte[] readBuffer=wanted==buffer.length?buffer:new byte[wanted];
                int count=currentProgram.getMemory().getBytes(chunk,readBuffer);
                if(count<=0)break;
                for(int i=0;i<count;i++){
                    int ch=readBuffer[i]&0xff;
                    if(ch>=0x20&&ch<=0x7e){
                        if(run.length()==0)runStart=chunk.add(i);
                        if(run.length()<1024)run.append((char)ch);
                    }else{
                        collectResourceString(runStart,run.toString(),targets,resourceRefs,resourcesOnly);
                        run.setLength(0);runStart=null;
                    }
                }
                offset+=count;
            }
            collectResourceString(runStart,run.toString(),targets,resourceRefs,resourcesOnly);
        }
        Files.write(out.resolve("resource-strings.tsv"),resourceRefs,StandardCharsets.UTF_8);
        for(long address:targets){
            Function f=getFunctionAt(toAddr(address));if(f==null){rows.add("missing\t"+Long.toHexString(address));continue;}
            DecompileResults r=d.decompileFunction(f,120,monitor);
            rows.add("function\t"+f.getEntryPoint()+"\t"+f.getName()+"\t"+r.decompileCompleted());
            if(r.decompileCompleted())Files.write(out.resolve(f.getEntryPoint()+".c"),r.getDecompiledFunction().getC().getBytes(StandardCharsets.UTF_8));
        }
        d.dispose();Files.write(out.resolve("manifest.tsv"),rows,StandardCharsets.UTF_8);
    }
    private void collectResourceString(Address address,String text,Set<Long> targets,List<String> rows,boolean resourcesOnly){
        if(address==null)return;String lower=text.toLowerCase(Locale.ROOT);
        if(!(lower.contains(".cv2")||lower.contains(".bmp")||lower.contains(".pat")||lower.contains(".pal")||lower.contains(".dat")))return;
        ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(address);
        while(refs.hasNext()){
            Reference ref=refs.next();Function caller=getFunctionContaining(ref.getFromAddress());
            String entry=caller==null?"":caller.getEntryPoint().toString();
            rows.add(String.format("%s\t%s\t%s\t%s",address,text,ref.getFromAddress(),entry));
            if(resourcesOnly&&caller!=null&&(lower.contains("data/character/%s/%s.pat")||lower.contains("palette%03d")||lower.equals(".bmp")||lower.contains(".dat")))
                targets.add(caller.getEntryPoint().getOffset());
        }
    }
}
