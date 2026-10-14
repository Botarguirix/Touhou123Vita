// @category Touhou123Vita.Analysis
// Entry point and import references only; raw pseudocode stays local.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
public class ExportT123 extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=2) throw new IllegalArgumentException("output directory, expected SHA256 required");
        if(!args[1].equalsIgnoreCase(currentProgram.getExecutableSHA256())) throw new IllegalStateException("SHA256 mismatch");
        Path out=Paths.get(args[0]); Files.createDirectories(out);
        List<String> rows=new ArrayList<>();
        rows.add("sha256\t"+currentProgram.getExecutableSHA256());
        rows.add("language\t"+currentProgram.getLanguageID());
        DecompInterface d=new DecompInterface(); d.openProgram(currentProgram);
        int n=0;
        for(Function f:currentProgram.getFunctionManager().getFunctions(true)) {
            if(f.isExternal()) { rows.add("import\t"+f.getName()); continue; }
            if(n++>=30) continue;
            DecompileResults r=d.decompileFunction(f,60,monitor);
            rows.add("function\t"+f.getEntryPoint()+"\t"+f.getName()+"\t"+r.decompileCompleted());
            if(r.decompileCompleted()) Files.write(out.resolve(f.getEntryPoint()+".c"),r.getDecompiledFunction().getC().getBytes(StandardCharsets.UTF_8));
        }
        d.dispose(); Files.write(out.resolve("manifest.tsv"),rows,StandardCharsets.UTF_8);
    }
}
