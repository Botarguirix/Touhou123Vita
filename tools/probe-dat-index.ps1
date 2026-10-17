param(
    [Parameter(Mandatory)][string[]]$Archive,
    [Parameter(Mandatory)][string]$Output
)
$ErrorActionPreference='Stop'
$source=@"
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
public sealed class T123DatIndexEntry { public uint Offset; public uint Size; public string Path; }
public static class T123DatIndexReader {
  private sealed class MT {
    readonly uint[] words=new uint[624]; int cursor=624;
    public MT(uint seed){words[0]=seed;for(uint i=1;i<624;i++)words[i]=unchecked(1812433253u*(words[i-1]^(words[i-1]>>30))+i);}
    public uint Next(){if(cursor==624){for(int i=0;i<624;i++){uint twist=(words[i]&0x80000000u)|(words[(i+1)%624]&0x7fffffffu);words[i]=words[(i+397)%624]^(twist>>1)^((twist&1)!=0?0x9908b0dfu:0u);}cursor=0;}uint value=words[cursor++];value^=value>>11;value^=(value<<7)&0x9d2c5680u;value^=(value<<15)&0xefc60000u;return value^(value>>18);}
  }
  public static List<T123DatIndexEntry> Read(string file){
    byte[] data=File.ReadAllBytes(file);if(data.Length<6)throw new InvalidDataException("short header: "+file);
    int count=data[0]|data[1]<<8;uint length=(uint)(data[2]|data[3]<<8|data[4]<<16|data[5]<<24);
    if(count<=0||length<(uint)count*9||length>16*1024*1024||length+6>data.Length)throw new InvalidDataException("invalid header: "+file);
    byte[] table=new byte[(int)length];Buffer.BlockCopy(data,6,table,0,(int)length);var mt=new MT(length+6);uint a=0xc5,b=0x83;
    for(int i=0;i<table.Length;i++){table[i]^=(byte)(mt.Next()^a);a=(a+b)&255;b=(b+0x53)&255;}
    var encoding=Encoding.GetEncoding(1252);var rows=new List<T123DatIndexEntry>(count);int position=0;
    for(int i=0;i<count;i++){
      if(table.Length-position<9)throw new InvalidDataException("truncated row: "+file);
      uint offset=BitConverter.ToUInt32(table,position),size=BitConverter.ToUInt32(table,position+4);int nameLength=table[position+8];position+=9;
      if(nameLength<=0||nameLength>table.Length-position||offset<length+6||offset>(uint)data.Length||size>(uint)data.Length-offset)throw new InvalidDataException("invalid row "+i+" in "+file);
      string name=encoding.GetString(table,position,nameLength);position+=nameLength;
      rows.Add(new T123DatIndexEntry{Offset=offset,Size=size,Path=name});
    }
    return rows;
  }
}
"@
Add-Type -TypeDefinition $source
$rows=[System.Collections.Generic.List[object]]::new()
foreach($path in $Archive){
    $resolved=(Resolve-Path -LiteralPath $path).Path
    foreach($entry in [T123DatIndexReader]::Read($resolved)){$rows.Add([pscustomobject]@{archive=[IO.Path]::GetFileName($resolved);offset=$entry.Offset;size=$entry.Size;path=$entry.Path})}
}
$rows | Export-Csv -LiteralPath $Output -Delimiter "`t" -NoTypeInformation -Encoding utf8
Write-Output "wrote $Output with $($rows.Count) rows"
