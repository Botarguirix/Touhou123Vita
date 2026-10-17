// @category Touhou123Vita.Analysis
// Export selected character virtuals and their xrefs from the pinned PE.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class ExportCharacterObjectRoutes extends GhidraScript {
    public void run() throws Exception {
        String[] a=getScriptArgs();
        if(a.length<3 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))
            throw new IllegalStateException("Expected output directory, matching SHA-256, and one or more function VAs");
        Path out=Paths.get(a[0]);Files.createDirectories(out);
        DecompInterface decomp=new DecompInterface();decomp.openProgram(currentProgram);
        List<String> manifest=new ArrayList<>(),xrefs=new ArrayList<>();
        manifest.add("va\tname\tdecompiled");xrefs.add("target\tcaller\tcallsite\treference_type");
        for(int i=2;i<a.length;i++){
            long va=Long.parseUnsignedLong(a[i].replaceFirst("^(0[xX])",""),16);
            Address address=toAddr(va);Function f=currentProgram.getFunctionManager().getFunctionAt(address);
            if(f==null){manifest.add(String.format("%08X\tmissing\tfalse",va));continue;}
            DecompileResults result=decomp.decompileFunction(f,120,monitor);
            manifest.add(String.format("%08X\t%s\t%s",va,f.getName(),result.decompileCompleted()));
            if(result.decompileCompleted())Files.write(out.resolve(String.format("%08X.c",va)),result.getDecompiledFunction().getC().getBytes(StandardCharsets.UTF_8));
            ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(address);
            while(refs.hasNext()){
                Reference ref=refs.next();Function caller=currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
                xrefs.add(String.format("%08X\t%s\t%s\t%s",va,caller==null?"":caller.getEntryPoint(),ref.getFromAddress(),ref.getReferenceType()));
            }
        }
        decomp.dispose();Files.write(out.resolve("manifest.tsv"),manifest,StandardCharsets.UTF_8);Files.write(out.resolve("xrefs.tsv"),xrefs,StandardCharsets.UTF_8);
    }
}
