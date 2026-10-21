// @category Touhou123Vita.Analysis
// Function inventory of the hash-pinned image for the static-recompilation route (F0).
// Writes functions.tsv (one row per function) and functions-summary.txt; no pseudocode.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class ExportFunctions extends GhidraScript {
    public void run() throws Exception {
        String[] a = getScriptArgs();
        if (a.length != 2 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))
            throw new IllegalStateException("Reference hash mismatch");
        Path out = Paths.get(a[0]);
        Files.createDirectories(out);
        Listing listing = currentProgram.getListing();
        ReferenceManager refs = currentProgram.getReferenceManager();
        List<String> rows = new ArrayList<>();
        rows.add("entry\tname\tbytes\tinstructions\tthunk\tcallers\tcallees\tx87\tsse\tindirect_calls\tindirect_jumps\tfs_refs\tcalling_convention");
        long functions = 0, thunks = 0, totalBytes = 0, totalIns = 0, x87Fns = 0, sseFns = 0, fsFns = 0, indirectJumpFns = 0;
        AddressSet covered = new AddressSet();
        FunctionIterator it = listing.getFunctions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Function f = it.next();
            if (f.isExternal()) continue;
            functions++;
            if (f.isThunk()) thunks++;
            AddressSetView body = f.getBody();
            covered.add(body);
            long ins = 0, x87 = 0, sse = 0, icall = 0, ijmp = 0, fs = 0;
            for (Instruction i : listing.getInstructions(body, true)) {
                ins++;
                String m = i.getMnemonicString().toUpperCase();
                String text = i.toString().toUpperCase();
                if (m.startsWith("F") && !m.equals("FEMMS")) x87++;
                if (text.contains("XMM")) sse++;
                if (text.contains("FS:")) fs++;
                FlowType flow = i.getFlowType();
                if (flow.isCall() && flow.isComputed()) icall++;
                if (flow.isJump() && flow.isComputed()) ijmp++;
            }
            int callers = 0;
            for (Reference r : refs.getReferencesTo(f.getEntryPoint())) if (r.getReferenceType().isCall()) callers++;
            int callees = f.getCalledFunctions(monitor).size();
            totalBytes += body.getNumAddresses();
            totalIns += ins;
            if (x87 > 0) x87Fns++;
            if (sse > 0) sseFns++;
            if (fs > 0) fsFns++;
            if (ijmp > 0) indirectJumpFns++;
            rows.add(String.format("%s\t%s\t%d\t%d\t%b\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s",
                f.getEntryPoint(), f.getName(), body.getNumAddresses(), ins, f.isThunk(), callers, callees,
                x87, sse, icall, ijmp, fs, f.getCallingConventionName()));
        }
        long orphanIns = 0;
        for (Instruction i : listing.getInstructions(true)) if (!covered.contains(i.getAddress())) orphanIns++;
        Files.write(out.resolve("functions.tsv"), rows, StandardCharsets.UTF_8);
        List<String> summary = Arrays.asList(
            "sha256=" + a[1],
            "functions=" + functions,
            "thunks=" + thunks,
            "function_bytes=" + totalBytes,
            "function_instructions=" + totalIns,
            "instructions_outside_functions=" + orphanIns,
            "functions_with_x87=" + x87Fns,
            "functions_with_sse=" + sseFns,
            "functions_with_fs_refs=" + fsFns,
            "functions_with_computed_jumps=" + indirectJumpFns);
        Files.write(out.resolve("functions-summary.txt"), summary, StandardCharsets.UTF_8);
        println(String.join("\n", summary));
    }
}
