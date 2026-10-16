// @category Touhou123Vita.Analysis
// Selected functions and vtables from the exact local reference image.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.Function;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public class ExportKernel extends GhidraScript {
    public void run() throws Exception {
        String[] a=getScriptArgs();
        if(a.length!=2 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))throw new IllegalStateException("Reference hash mismatch");
        Path out=Paths.get(a[0]);Files.createDirectories(out);
        List<String> rows=new ArrayList<>();DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
        Set<Long> targets=new LinkedHashSet<>();
        long[] refs={0x438c60L,0x487740L,0x4877c0L,0x4397f0L,0x439850L,0x4636b0L,0x43e9a0L,0x4396c0L};
        for(long v:refs)targets.add(v);
        long[] tables={0x85bf4cL,0x85eab4L,0x8588ecL};
        for(long table:tables)for(int slot=0;slot<25;slot++){
            long addr=Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(table+slot*4)));
            rows.add(String.format("vtable\t%08x\t%d\t%08x",table,slot,addr));
            if(addr>=0x401000L && addr<0x857000L && (slot==8||slot==3||slot==5||slot==7||slot==10||slot==15||slot==16||slot==20))targets.add(addr);
        }
        for(long address:targets){
            Function f=getFunctionAt(toAddr(address));if(f==null){rows.add("missing\t"+Long.toHexString(address));continue;}
            DecompileResults r=d.decompileFunction(f,120,monitor);
            rows.add("function\t"+f.getEntryPoint()+"\t"+f.getName()+"\t"+r.decompileCompleted());
            if(r.decompileCompleted())Files.write(out.resolve(f.getEntryPoint()+".c"),r.getDecompiledFunction().getC().getBytes(StandardCharsets.UTF_8));
        }
        d.dispose();Files.write(out.resolve("manifest.tsv"),rows,StandardCharsets.UTF_8);
    }
}
