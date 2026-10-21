// @category Touhou123Vita.Analysis
// Export stage selection and background loaders from the exact local PE.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class ExportStages extends GhidraScript {
    private static final long[] TARGETS={
        0x424280L,0x426900L,0x40c580L,0x40cb60L,0x406c60L,0x406d30L,0x406ee0L,0x406fa0L,0x407040L,0x4070e0L,0x429440L,
        0x46f7b0L,0x46f9c0L,0x471460L,0x471500L,
        0x46fe40L,0x470e40L,0x471c50L,0x472230L,0x472640L,0x473270L,
        0x4723b0L,0x4723f0L,0x472640L,0x472730L,
        0x406ea0L,0x406ee0L,0x406fa0L,0x407040L,0x4070e0L,0x429440L,
        0x473620L,0x473af0L,0x474f70L,0x475eb0L,0x476990L,0x477310L,0x477550L
    };
    public void run() throws Exception {
        String[] a=getScriptArgs();
        if(a.length!=2 || !a[1].equalsIgnoreCase(currentProgram.getExecutableSHA256()))
            throw new IllegalStateException("Expected output directory and matching executable SHA256");
        Path out=Paths.get(a[0]);Files.createDirectories(out);
        DecompInterface decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
        List<String> manifest=new ArrayList<>(),callers=new ArrayList<>();
        manifest.add("sha256\t"+currentProgram.getExecutableSHA256());
        manifest.add("address\tname\tdecompiled");
        callers.add("target\ttarget_name\tcall_site\tcaller_entry\tcaller_name");
        List<Long> addresses=new ArrayList<>();for(long address:TARGETS)addresses.add(address);
        List<String> vtable=new ArrayList<>();vtable.add("symbol\ttable\tslot\ttarget\tfunction\tdecompiled");
        List<String> refsOut=new ArrayList<>();refsOut.add("instruction\toperand\ttarget\tsymbol\tfunction_pointer_count");
        Function bg12=getFunctionAt(toAddr(0x472640L));
        if(bg12!=null){
            InstructionIterator insIt=currentProgram.getListing().getInstructions(bg12.getBody(),true);
            while(insIt.hasNext()){
                Instruction ins=insIt.next();
                for(Reference ref:currentProgram.getReferenceManager().getReferencesFrom(ins.getAddress())){
                    Address target=ref.getToAddress();Symbol targetSymbol=currentProgram.getSymbolTable().getPrimarySymbol(target);
                    int functionPointers=0;
                    if(ref.getReferenceType().isData()&&currentProgram.getMemory().contains(target)){
                        for(int slot=0;slot<48;slot++){
                            Address entry=target.add(slot*4L);if(!currentProgram.getMemory().contains(entry))break;
                            long pointer=currentProgram.getMemory().getInt(entry)&0xffffffffL;
                            if(getFunctionAt(toAddr(pointer))!=null)functionPointers++;
                        }
                    }
                    refsOut.add(String.format("BG12 %s\t%d\t%s\t%s\t%d",ins.getAddress(),ref.getOperandIndex(),target,targetSymbol==null?"":targetSymbol.getName(),functionPointers));
                    if(functionPointers>=5&&ins.getAddress().equals(toAddr(0x472688L))&&targetSymbol!=null&&targetSymbol.getName().equalsIgnoreCase("vftable")){
                        int misses=0;
                        for(int slot=0;slot<48;slot++){
                            Address entry=target.add(slot*4L);if(!currentProgram.getMemory().contains(entry))break;
                            long pointer=currentProgram.getMemory().getInt(entry)&0xffffffffL;Function method=getFunctionAt(toAddr(pointer));
                            vtable.add(String.format("BG12 constructor-ref:%s\t%s\t%d\t%08x\t%s\t%s",target,target,slot,pointer,method==null?"UNDEFINED":method.getName(),false));
                            if(method!=null){misses=0;if(!addresses.contains(pointer))addresses.add(pointer);}else if(++misses>=1)break;
                        }
                    }
                }
            }
        }
        Function bg34=getFunctionAt(toAddr(0x474f70L));
        if(bg34!=null){
            InstructionIterator insIt=currentProgram.getListing().getInstructions(bg34.getBody(),true);
            while(insIt.hasNext()){
                Instruction ins=insIt.next();
                for(Reference ref:currentProgram.getReferenceManager().getReferencesFrom(ins.getAddress())){
                    Address target=ref.getToAddress();Symbol targetSymbol=currentProgram.getSymbolTable().getPrimarySymbol(target);
                    int functionPointers=0;
                    if(ref.getReferenceType().isData()&&currentProgram.getMemory().contains(target)){
                        for(int slot=0;slot<48;slot++){
                            Address entry=target.add(slot*4L);if(!currentProgram.getMemory().contains(entry))break;
                            long pointer=currentProgram.getMemory().getInt(entry)&0xffffffffL;
                            if(getFunctionAt(toAddr(pointer))!=null)functionPointers++;
                        }
                    }
                    refsOut.add(String.format("%s\t%d\t%s\t%s\t%d",ins.getAddress(),ref.getOperandIndex(),target,targetSymbol==null?"":targetSymbol.getName(),functionPointers));
                    if(functionPointers>=5&&ins.getAddress().equals(toAddr(0x474fcbL))&&targetSymbol!=null&&targetSymbol.getName().equalsIgnoreCase("vftable")){
                        int misses=0;
                        for(int slot=0;slot<48;slot++){
                            Address entry=target.add(slot*4L);if(!currentProgram.getMemory().contains(entry))break;
                            long pointer=currentProgram.getMemory().getInt(entry)&0xffffffffL;Function method=getFunctionAt(toAddr(pointer));
                            vtable.add(String.format("constructor-ref:%s\t%s\t%d\t%08x\t%s\t%s",target, target,slot,pointer,method==null?"UNDEFINED":method.getName(),false));
                            if(method!=null){misses=0;if(!addresses.contains(pointer))addresses.add(pointer);}else if(++misses>=1)break;
                        }
                    }
                }
            }
        }
        SymbolIterator symbols=currentProgram.getSymbolTable().getAllSymbols(true);
        while(symbols.hasNext()){
            Symbol symbol=symbols.next();String name=symbol.getName();
            if(!name.toLowerCase().contains("bg34")||!name.toLowerCase().contains("vftable"))continue;
            int misses=0;
            for(int slot=0;slot<64;slot++){
                Address entry=symbol.getAddress().add(slot*4L);if(!currentProgram.getMemory().contains(entry))break;
                long target=currentProgram.getMemory().getInt(entry)&0xffffffffL;Address targetAddress=toAddr(target);
                Function method=getFunctionAt(targetAddress);boolean found=method!=null;
                vtable.add(String.format("%s\t%s\t%d\t%08x\t%s\t%s",name,symbol.getAddress(),slot,target,found?method.getName():"UNDEFINED",false));
                if(found){misses=0;if(!addresses.contains(target))addresses.add(target);}else if(++misses>=3)break;
            }
        }
        for(long address:addresses){
            Function f=getFunctionAt(toAddr(address));
            if(f==null){manifest.add(String.format("%08x\tMISSING\tfalse",address));continue;}
            DecompileResults result=decompiler.decompileFunction(f,120,monitor);
            manifest.add(String.format("%08x\t%s\t%s",address,f.getName(),result.decompileCompleted()));
            if(result.decompileCompleted())
                Files.write(out.resolve(String.format("%08x.c",address)),result.getDecompiledFunction().getC().getBytes(StandardCharsets.UTF_8));
            if(address==0x474f70L){
                List<String> assembly=new ArrayList<>();InstructionIterator listing=currentProgram.getListing().getInstructions(f.getBody(),true);
                while(listing.hasNext()){Instruction instruction=listing.next();assembly.add(instruction.getAddress()+"\t"+instruction.toString());}
                Files.write(out.resolve("00474f70.asm.tsv"),assembly,StandardCharsets.UTF_8);
            }
            if(!vtable.isEmpty()){
                for(int row=1;row<vtable.size();row++)if(vtable.get(row).matches(".*\\t"+String.format("%08x",address)+"\\t.*"))vtable.set(row,vtable.get(row).replace("\tfalse","\t"+result.decompileCompleted()));
            }
            ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
            while(refs.hasNext()){
                Reference ref=refs.next();Function caller=getFunctionContaining(ref.getFromAddress());
                if(caller==null)continue;
                callers.add(String.format("%08x\t%s\t%s\t%s\t%s",address,f.getName(),ref.getFromAddress(),caller.getEntryPoint(),caller.getName()));
            }
        }
        decompiler.dispose();
        Files.write(out.resolve("manifest.tsv"),manifest,StandardCharsets.UTF_8);
        Files.write(out.resolve("callers.tsv"),callers,StandardCharsets.UTF_8);
        Files.write(out.resolve("bg34-vtable.tsv"),vtable,StandardCharsets.UTF_8);
        Files.write(out.resolve("bg34-constructor-references.tsv"),refsOut,StandardCharsets.UTF_8);
        long[] globals={0x8581d0L,0x8579a0L,0x8581c8L,0x857b20L,0x871520L,0x8575a4L,0x8581c0L,0x857990L,0x85ae80L,0x85ae88L,0x85ae90L,0x85ad14L};
        List<String> values=new ArrayList<>();values.add("address\tfloat\tuint32");
        for(long address:globals){int raw=currentProgram.getMemory().getInt(toAddr(address));values.add(String.format("%08x\t%s\t%08x",address,Float.intBitsToFloat(raw),raw));}
        Files.write(out.resolve("bg34-camera-constants.tsv"),values,StandardCharsets.UTF_8);
    }
}
