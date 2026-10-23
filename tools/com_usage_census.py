#!/usr/bin/env python3
"""Censo conservador de métodos COM del PE fijado; no confunde vtables C++ con COM."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import struct
import uuid
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
sys.path.insert(0, str(ROOT / "local/python-deps"))
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

# Orden de los SDK públicos locales de DirectX/MinGW, no datos del juego.
VTABLES = {'ID3DXEffect': ['QueryInterface',
                 'AddRef',
                 'Release',
                 'GetDesc',
                 'GetParameterDesc',
                 'GetTechniqueDesc',
                 'GetPassDesc',
                 'GetFunctionDesc',
                 'GetParameter',
                 'GetParameterByName',
                 'GetParameterBySemantic',
                 'GetParameterElement',
                 'GetTechnique',
                 'GetTechniqueByName',
                 'GetPass',
                 'GetPassByName',
                 'GetFunction',
                 'GetFunctionByName',
                 'GetAnnotation',
                 'GetAnnotationByName',
                 'SetValue',
                 'GetValue',
                 'SetBool',
                 'GetBool',
                 'SetBoolArray',
                 'GetBoolArray',
                 'SetInt',
                 'GetInt',
                 'SetIntArray',
                 'GetIntArray',
                 'SetFloat',
                 'GetFloat',
                 'SetFloatArray',
                 'GetFloatArray',
                 'SetVector',
                 'GetVector',
                 'SetVectorArray',
                 'GetVectorArray',
                 'SetMatrix',
                 'GetMatrix',
                 'SetMatrixArray',
                 'GetMatrixArray',
                 'SetMatrixPointerArray',
                 'GetMatrixPointerArray',
                 'SetMatrixTranspose',
                 'GetMatrixTranspose',
                 'SetMatrixTransposeArray',
                 'GetMatrixTransposeArray',
                 'SetMatrixTransposePointerArray',
                 'GetMatrixTransposePointerArray',
                 'SetString',
                 'GetString',
                 'SetTexture',
                 'GetTexture',
                 'GetPixelShader',
                 'GetVertexShader',
                 'SetArrayRange',
                 'GetPool',
                 'SetTechnique',
                 'GetCurrentTechnique',
                 'ValidateTechnique',
                 'FindNextValidTechnique',
                 'IsParameterUsed',
                 'Begin',
                 'BeginPass',
                 'CommitChanges',
                 'EndPass',
                 'End',
                 'GetDevice',
                 'OnLostDevice',
                 'OnResetDevice',
                 'SetStateManager',
                 'GetStateManager',
                 'BeginParameterBlock',
                 'EndParameterBlock',
                 'ApplyParameterBlock',
                 'DeleteParameterBlock',
                 'CloneEffect',
                 'SetRawValue'],
 'IDirect3D9': ['QueryInterface',
                'AddRef',
                'Release',
                'RegisterSoftwareDevice',
                'GetAdapterCount',
                'GetAdapterIdentifier',
                'GetAdapterModeCount',
                'EnumAdapterModes',
                'GetAdapterDisplayMode',
                'CheckDeviceType',
                'CheckDeviceFormat',
                'CheckDeviceMultiSampleType',
                'CheckDepthStencilMatch',
                'CheckDeviceFormatConversion',
                'GetDeviceCaps',
                'GetAdapterMonitor',
                'CreateDevice'],
 'IDirect3DDevice9': ['QueryInterface',
                      'AddRef',
                      'Release',
                      'TestCooperativeLevel',
                      'GetAvailableTextureMem',
                      'EvictManagedResources',
                      'GetDirect3D',
                      'GetDeviceCaps',
                      'GetDisplayMode',
                      'GetCreationParameters',
                      'SetCursorProperties',
                      'SetCursorPosition',
                      'ShowCursor',
                      'CreateAdditionalSwapChain',
                      'GetSwapChain',
                      'GetNumberOfSwapChains',
                      'Reset',
                      'Present',
                      'GetBackBuffer',
                      'GetRasterStatus',
                      'SetDialogBoxMode',
                      'SetGammaRamp',
                      'GetGammaRamp',
                      'CreateTexture',
                      'CreateVolumeTexture',
                      'CreateCubeTexture',
                      'CreateVertexBuffer',
                      'CreateIndexBuffer',
                      'CreateRenderTarget',
                      'CreateDepthStencilSurface',
                      'UpdateSurface',
                      'UpdateTexture',
                      'GetRenderTargetData',
                      'GetFrontBufferData',
                      'StretchRect',
                      'ColorFill',
                      'CreateOffscreenPlainSurface',
                      'SetRenderTarget',
                      'GetRenderTarget',
                      'SetDepthStencilSurface',
                      'GetDepthStencilSurface',
                      'BeginScene',
                      'EndScene',
                      'Clear',
                      'SetTransform',
                      'GetTransform',
                      'MultiplyTransform',
                      'SetViewport',
                      'GetViewport',
                      'SetMaterial',
                      'GetMaterial',
                      'SetLight',
                      'GetLight',
                      'LightEnable',
                      'GetLightEnable',
                      'SetClipPlane',
                      'GetClipPlane',
                      'SetRenderState',
                      'GetRenderState',
                      'CreateStateBlock',
                      'BeginStateBlock',
                      'EndStateBlock',
                      'SetClipStatus',
                      'GetClipStatus',
                      'GetTexture',
                      'SetTexture',
                      'GetTextureStageState',
                      'SetTextureStageState',
                      'GetSamplerState',
                      'SetSamplerState',
                      'ValidateDevice',
                      'SetPaletteEntries',
                      'GetPaletteEntries',
                      'SetCurrentTexturePalette',
                      'GetCurrentTexturePalette',
                      'SetScissorRect',
                      'GetScissorRect',
                      'SetSoftwareVertexProcessing',
                      'GetSoftwareVertexProcessing',
                      'SetNPatchMode',
                      'GetNPatchMode',
                      'DrawPrimitive',
                      'DrawIndexedPrimitive',
                      'DrawPrimitiveUP',
                      'DrawIndexedPrimitiveUP',
                      'ProcessVertices',
                      'CreateVertexDeclaration',
                      'SetVertexDeclaration',
                      'GetVertexDeclaration',
                      'SetFVF',
                      'GetFVF',
                      'CreateVertexShader',
                      'SetVertexShader',
                      'GetVertexShader',
                      'SetVertexShaderConstantF',
                      'GetVertexShaderConstantF',
                      'SetVertexShaderConstantI',
                      'GetVertexShaderConstantI',
                      'SetVertexShaderConstantB',
                      'GetVertexShaderConstantB',
                      'SetStreamSource',
                      'GetStreamSource',
                      'SetStreamSourceFreq',
                      'GetStreamSourceFreq',
                      'SetIndices',
                      'GetIndices',
                      'CreatePixelShader',
                      'SetPixelShader',
                      'GetPixelShader',
                      'SetPixelShaderConstantF',
                      'GetPixelShaderConstantF',
                      'SetPixelShaderConstantI',
                      'GetPixelShaderConstantI',
                      'SetPixelShaderConstantB',
                      'GetPixelShaderConstantB',
                      'DrawRectPatch',
                      'DrawTriPatch',
                      'DeletePatch',
                      'CreateQuery'],
 'IDirect3DSurface9': ['QueryInterface',
                       'AddRef',
                       'Release',
                       'GetDevice',
                       'SetPrivateData',
                       'GetPrivateData',
                       'FreePrivateData',
                       'SetPriority',
                       'GetPriority',
                       'PreLoad',
                       'GetType',
                       'GetContainer',
                       'GetDesc',
                       'LockRect',
                       'UnlockRect',
                       'GetDC',
                       'ReleaseDC'],
 'IDirect3DSwapChain9': ['QueryInterface',
                         'AddRef',
                         'Release',
                         'Present',
                         'GetFrontBufferData',
                         'GetBackBuffer',
                         'GetRasterStatus',
                         'GetDisplayMode',
                         'GetDevice',
                         'GetPresentParameters'],
 'IDirect3DTexture9': ['QueryInterface',
                       'AddRef',
                       'Release',
                       'GetDevice',
                       'SetPrivateData',
                       'GetPrivateData',
                       'FreePrivateData',
                       'SetPriority',
                       'GetPriority',
                       'PreLoad',
                       'GetType',
                       'SetLOD',
                       'GetLOD',
                       'GetLevelCount',
                       'SetAutoGenFilterType',
                       'GetAutoGenFilterType',
                       'GenerateMipSubLevels',
                       'GetLevelDesc',
                       'GetSurfaceLevel',
                       'LockRect',
                       'UnlockRect',
                       'AddDirtyRect'],
 'IDirect3DVertexBuffer9': ['QueryInterface',
                            'AddRef',
                            'Release',
                            'GetDevice',
                            'SetPrivateData',
                            'GetPrivateData',
                            'FreePrivateData',
                            'SetPriority',
                            'GetPriority',
                            'PreLoad',
                            'GetType',
                            'Lock',
                            'Unlock',
                            'GetDesc'],
 'IDirectInput8A': ['QueryInterface',
                    'AddRef',
                    'Release',
                    'CreateDevice',
                    'EnumDevices',
                    'GetDeviceStatus',
                    'RunControlPanel',
                    'Initialize',
                    'FindDevice',
                    'EnumDevicesBySemantics',
                    'ConfigureDevices'],
 'IDirectInputDevice8A': ['QueryInterface',
                          'AddRef',
                          'Release',
                          'GetCapabilities',
                          'EnumObjects',
                          'GetProperty',
                          'SetProperty',
                          'Acquire',
                          'Unacquire',
                          'GetDeviceState',
                          'GetDeviceData',
                          'SetDataFormat',
                          'SetEventNotification',
                          'SetCooperativeLevel',
                          'GetObjectInfo',
                          'GetDeviceInfo',
                          'RunControlPanel',
                          'Initialize',
                          'CreateEffect',
                          'EnumEffects',
                          'GetEffectInfo',
                          'GetForceFeedbackState',
                          'SendForceFeedbackCommand',
                          'EnumCreatedEffectObjects',
                          'Escape',
                          'Poll',
                          'SendDeviceData',
                          'EnumEffectsInFile',
                          'WriteEffectToFile',
                          'BuildActionMap',
                          'SetActionMap',
                          'GetImageInfo'],
 'IDirectSound8': ['QueryInterface',
                   'AddRef',
                   'Release',
                   'CreateSoundBuffer',
                   'GetCaps',
                   'DuplicateSoundBuffer',
                   'SetCooperativeLevel',
                   'Compact',
                   'GetSpeakerConfig',
                   'SetSpeakerConfig',
                   'Initialize',
                   'VerifyCertification'],
 'IDirectSoundBuffer8': ['QueryInterface',
                         'AddRef',
                         'Release',
                         'GetCaps',
                         'GetCurrentPosition',
                         'GetFormat',
                         'GetVolume',
                         'GetPan',
                         'GetFrequency',
                         'GetStatus',
                         'Initialize',
                         'Lock',
                         'Play',
                         'SetCurrentPosition',
                         'SetFormat',
                         'SetVolume',
                         'SetPan',
                         'SetFrequency',
                         'Stop',
                         'Unlock',
                         'Restore',
                         'SetFX',
                         'AcquireResources',
                         'GetObjectInPath']}

# Globales de interfaz comprobados en creación, no nombres adivinados por offset.
SEEDS = {0x8A0E2C: "IDirect3D9", 0x8A0E30: "IDirect3DDevice9", 0x896B50: "IDirect3DDevice9",
         0x8A0E34: "IDirect3DSwapChain9", 0x8A019C: "IDirectInput8A",
         0x8A01A0: "IDirectInputDevice8A", 0x8A0FCC: "IDirectSound8",
         0x89AB00: "ID3DXEffect", 0x89AB08: "ID3DXEffect"}
REGS = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"}
CONTAINERS = {0x896B4C: "IDirect3DDevice9", 0x89AAFC: "ID3DXEffect",
              0x89AB04: "ID3DXEffect"}
REVIEWED_RETURN_CALLS = {0x414EF0: "IDirect3D9"}
# Rama de éxito de Direct3DCreate9: el bloque de fallo acaba en RET y el
# slice lineal no cruza ese RET. EAX sigue siendo el resultado de la factory.
REVIEWED_REGISTERS = {(0x414F1A, "eax"): ("interface?", "IDirect3D9", "Direct3DCreate9@0x414ef0"),
                      (0x414F26, "eax"): ("interface?", "IDirect3D9", "Direct3DCreate9@0x414ef0")}
VTABLES["IDirectSoundBuffer"] = VTABLES["IDirectSoundBuffer8"][:21]
# Wrappers revisados: campo +4 recibe la salida de D3DXCreateEffect o
# CreateSoundBuffer. La clase/pasaje de this se infiere: confianza media.
PARAMETER_FIELDS = (
    (0x418160, 0x418181, "ecx", "ID3DXEffect"),
    (0x4181E0, 0x418201, "ecx", "ID3DXEffect"),
    (0x418210, 0x418225, "ecx", "ID3DXEffect"),
    (0x418230, 0x418245, "ecx", "ID3DXEffect"),
    (0x418440, 0x418475, "ecx", "IDirectSoundBuffer"),
    (0x418480, 0x4184A1, "ecx", "IDirectSoundBuffer"),
    (0x418550, 0x418647, "eax", "IDirectSoundBuffer"),
    (0x418650, 0x41877A, "ecx", "IDirectSoundBuffer"),
    (0x418780, 0x4187AD, "ecx", "IDirectSoundBuffer"),
    (0x4187B0, 0x418805, "esi", "IDirectSoundBuffer"),
)
REVIEWED_FIELD_LOADS = {
    0x4010F7: "IDirect3DDevice9", 0x40110E: "IDirect3DDevice9",
    0x401144: "IDirect3DDevice9", 0x40115F: "IDirect3DDevice9",
    0x404AD4: "IDirect3DDevice9", 0x404B09: "IDirect3DDevice9",
    0x404B1D: "IDirect3DDevice9", 0x404B35: "IDirect3DDevice9",
    0x404B49: "IDirect3DDevice9", 0x404B5F: "IDirect3DDevice9",
    0x4090A5: "IDirect3DTexture9", 0x4090E2: "IDirect3DTexture9",
    0x409481: "IDirect3DTexture9", 0x4094FB: "IDirect3DTexture9",
    0x405241: "IDirect3DTexture9", 0x405252: "IDirect3DSurface9",
    0x405275: "IDirect3DSurface9",
    0x4181E9: "ID3DXEffect", 0x418216: "ID3DXEffect", 0x418236: "ID3DXEffect",
    0x418443: "IDirectSoundBuffer", 0x418483: "IDirectSoundBuffer",
    0x4183B3: "IDirectSoundBuffer",
    0x41855B: "IDirectSoundBuffer", 0x41859A: "IDirectSoundBuffer",
    0x418677: "IDirectSoundBuffer", 0x4186C1: "IDirectSoundBuffer",
    0x41873F: "IDirectSoundBuffer",
}


def parameter_value(ins, index, operand):
    address = ins[index][0]
    for start, stop, reg, interface in PARAMETER_FIELDS:
        if start <= address < stop and operand == reg:
            return ("container", interface, f"{reg}+4@{start:#x}")
    return None


def method_name(interface, offset):
    table = VTABLES.get(interface, [])
    if offset < 0 or offset % 4 or offset // 4 >= len(table):
        return None
    return table[offset // 4]


def scalar(operand):
    try:
        return int(operand, 0) & 0xFFFFFFFF
    except ValueError:
        return None


def value(ins, index, operand, seeds, depth=0):
    """Slice local; cruzar una rama reduce confianza. Un offset no prueba COM."""
    if depth > 16:
        return None
    reviewed = REVIEWED_REGISTERS.get((ins[index][0], operand))
    if reviewed:
        return reviewed
    number = scalar(operand)
    if number is not None:
        return ("constant", number)
    if operand in REGS:
        crossed_branch = False
        def uncertainty(result):
            if result and crossed_branch:
                return (result[0].rstrip("?") + "?",) + result[1:]
            return result
        for j in range(index - 1, max(-1, index - 2000), -1):
            _, _, mnemonic, op = ins[j]
            if mnemonic in ("ret", "int3"):
                return parameter_value(ins, index, operand)
            if mnemonic.startswith("j"):
                crossed_branch = True
            if mnemonic == "call" and operand == "eax" and ins[j][0] in REVIEWED_RETURN_CALLS:
                source = ins[j][0]
                return ("interface?", REVIEWED_RETURN_CALLS[source], f"return@{source:#x}")
            if mnemonic == "call" and operand in ("eax", "ecx", "edx"):
                return None
            parts = op.split(", ", 1)
            if parts[0] != operand:
                aliases = {"eax": ("ax", "al", "ah"), "ebx": ("bx", "bl", "bh"),
                           "ecx": ("cx", "cl", "ch"), "edx": ("dx", "dl", "dh")}
                if parts[0] in aliases.get(operand, ()) and mnemonic not in ("cmp", "test", "push"):
                    return None
                continue
            if mnemonic == "mov" and len(parts) == 2:
                return uncertainty(value(ins, j, parts[1], seeds, depth + 1))
            if mnemonic == "xor" and parts == [operand, operand]:
                return ("constant", 0)
            if mnemonic == "lea" and len(parts) == 2:
                absolute = re.fullmatch(r"\[(0x[0-9a-f]+)\]", parts[1])
                return ("constant", int(absolute[1], 16)) if absolute else None
            if mnemonic not in ("push", "test", "cmp"):
                return None
        return parameter_value(ins, index, operand)
    if ins[index][0] in REVIEWED_FIELD_LOADS and operand.startswith("dword ptr ["):
        address = ins[index][0]
        return ("interface?", REVIEWED_FIELD_LOADS[address], f"field+4@{address:#x}")
    absolute = re.fullmatch(r"dword ptr \[(0x[0-9a-f]+)\]", operand)
    if absolute:
        address = int(absolute[1], 16)
        if address in seeds:
            return ("interface", seeds[address], address)
        return None
    memory = re.fullmatch(r"dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+|[0-9]+))?\]", operand)
    if memory:
        base = value(ins, index, memory[1], seeds, depth + 1)
        offset = int(memory[2], 0) if memory[2] else 0
        if base and base[0].rstrip("?") == "container" and offset == 4:
            return ("interface?", base[1], base[2])
        if base and base[0].rstrip("?") == "interface" and offset == 0:
            return ("vtable" + ("?" if base[0].endswith("?") else ""), base[1], base[2])
        if base and base[0].rstrip("?") == "vtable" and method_name(base[1], offset):
            return ("method" + ("?" if base[0].endswith("?") else ""), base[1], base[2], offset)
    return None


def arguments(ins, index, seeds):
    result = []
    for j in range(index - 1, max(-1, index - 40), -1):
        _, _, mnemonic, operand = ins[j]
        if mnemonic == "call" or mnemonic.startswith("j") or mnemonic in ("ret", "int3"):
            break
        if mnemonic == "push":
            result.append(value(ins, j, operand, seeds))
        elif operand.startswith("esp,") or mnemonic == "pop":
            break
    return result


def cfg_read(operand, registers, seeds):
    number = scalar(operand)
    if number is not None:
        if number in CONTAINERS:
            return ("container", CONTAINERS[number], number)
        return ("constant", number)
    if operand in REGS:
        return registers.get(operand)
    absolute = re.fullmatch(r"dword ptr \[(0x[0-9a-f]+)\]", operand)
    if absolute:
        origin = int(absolute[1], 16)
        return ("interface", seeds[origin], origin) if origin in seeds else None
    mem = re.fullmatch(r"(?:dword ptr )?\[(e[a-z]{2})(?: \+ (0x[0-9a-f]+|[0-9]+))?\]", operand)
    if not mem:
        return None
    base = registers.get(mem[1])
    offset = int(mem[2], 0) if mem[2] else 0
    if not base:
        return None
    if base[0] == "container" and offset == 4:
        return ("interface", base[1], base[2] + 4)
    if base[0] == "interface" and offset == 0:
        return ("vtable", base[1], base[2])
    if base[0] == "vtable" and method_name(base[1], offset):
        return ("method", base[1], base[2], offset)
    return None


def join_state(left, right):
    def merge(a, b):
        if a == b:
            return a
        if a and b and a[0] in ("constant", "constant_set") and b[0] in ("constant", "constant_set"):
            av = (a[1],) if a[0] == "constant" else a[1]
            bv = (b[1],) if b[0] == "constant" else b[1]
            choices = tuple(sorted(set(av) | set(bv)))
            return ("constant_set", choices) if len(choices) <= 32 else None
        return None
    registers = {reg: merge(left[0].get(reg), right[0].get(reg)) for reg in REGS}
    # Los argumentos se cuentan desde ESP: preservar el sufijo común aunque
    # una ruta conserve más pushes antiguos (registros guardados del prólogo).
    stack = tuple(reversed([merge(a, b) for a, b in zip(reversed(left[1]), reversed(right[1]))]))
    return registers, stack


def state_arguments(args, argc):
    data_args = (args[1:] + [None] * argc)[:argc]
    single = [a[1] if a and a[0] == "constant" else None for a in data_args]
    choices = [[a[1]] if a and a[0] == "constant" else
               list(a[1]) if a and a[0] == "constant_set" else None for a in data_args]
    return single, choices


def forward_wrappers(ins, seeds, jump_tables=None):
    """CFG acotado de helpers cuyo ECX procede de un contenedor conocido.

    Se unen registros por igualdad en cada bloque. No sigue llamadas dentro
    del mismo CFG; descubre otros helpers de la misma clase por ECX. Todas
    estas atribuciones quedan como medias, no como cobertura dinámica.
    """
    jump_tables = jump_tables or {}
    by_va = {row[0]: i for i, row in enumerate(ins)}
    entries = {}
    provenance = []
    for i, (address, _, mnemonic, operand) in enumerate(ins):
        target = scalar(operand) if mnemonic == "call" else None
        if target not in by_va:
            continue
        receiver = value(ins, i, "ecx", seeds)
        if receiver and receiver[0] == "constant" and receiver[1] in CONTAINERS:
            entries.setdefault(target, set()).add(receiver[1])
            provenance.append({"caller": address, "callee": target,
                               "container": receiver[1]})
    pending = deque(sorted(entries))
    analysed, found, incomplete = set(), {}, []
    while pending:
        entry = pending.popleft()
        if entry in analysed or len(entries.get(entry, ())) != 1:
            continue
        analysed.add(entry)
        origin = next(iter(entries[entry]))
        initial = {reg: None for reg in REGS}
        initial["ecx"] = ("container", CONTAINERS[origin], origin)
        states = {entry: (initial, ())}
        work = deque([entry])
        visits = 0
        while work and visits < 20000 and len(states) < 5000:
            address = work.popleft()
            i = by_va.get(address)
            if i is None:
                continue
            _, size, mnemonic, operand = ins[i]
            registers, stack = states[address]
            registers, stack = dict(registers), tuple(stack)
            parts = operand.split(", ", 1)
            if mnemonic == "mov" and len(parts) == 2 and parts[0] in REGS:
                registers[parts[0]] = cfg_read(parts[1], registers, seeds)
            elif mnemonic == "lea" and len(parts) == 2 and parts[0] in REGS:
                # Solo copia de this a desplazamiento cero; no confundir
                # dirección de campo con el objeto al que apunta ese campo.
                m = re.fullmatch(r"\[(e[a-z]{2})\]", parts[1])
                registers[parts[0]] = registers.get(m[1]) if m else None
            elif mnemonic == "xor" and len(parts) == 2 and parts[0] == parts[1] and parts[0] in REGS:
                registers[parts[0]] = ("constant", 0)
            elif mnemonic == "push":
                stack = (stack + (cfg_read(operand, registers, seeds),))[-16:]
            elif mnemonic == "pop":
                if operand in REGS:
                    registers[operand] = stack[-1] if stack else None
                stack = stack[:-1]
            elif mnemonic == "call":
                target_value = cfg_read(operand, registers, seeds)
                args = list(reversed(stack))
                if target_value and target_value[0] == "method":
                    _, interface, source, offset = target_value
                    match = bool(args and args[0] == ("interface", interface, source))
                    candidate = {"va": address, "interface": interface,
                                 "method": method_name(interface, offset), "offset": offset,
                                 "source_global_va": source,
                                 "source_field_origin": f"CFG helper {entry:#x}",
                                 "confidence": "medium", "this_argument_matches": match,
                                 "arguments": args, "context": ins[max(0, i-12):i+1],
                                 "analysis": "forward_cfg_known_container"}
                    if interface == "IDirect3DDevice9" and candidate["method"] in (
                            "SetRenderState", "SetTextureStageState", "SetSamplerState"):
                        argc = 2 if candidate["method"] == "SetRenderState" else 3
                        candidate["constant_arguments"], candidate["constant_argument_choices"] = state_arguments(args, argc)
                    # Sobrescribir también con ausencia tras una unión evita
                    # conservar una inferencia provisional de la primera ruta.
                    found[(entry, address)] = candidate
                else:
                    found.pop((entry, address), None)
                direct = scalar(operand)
                receiver = registers.get("ecx")
                if direct in by_va and receiver and receiver[0] == "container":
                    known = entries.setdefault(direct, set())
                    if receiver[2] not in known:
                        known.add(receiver[2])
                        pending.append(direct)
                        provenance.append({"caller": address, "callee": direct,
                                           "container": receiver[2]})
                for reg in ("eax", "ecx", "edx"):
                    registers[reg] = None
                stack = ()
            elif mnemonic not in ("test", "cmp", "ret", "int3") and not mnemonic.startswith("j"):
                dest = parts[0]
                if "[esp" in dest and mnemonic not in ("fld", "fild", "fldcw"):
                    # Escrituras de pila no modeladas invalidan los pushes
                    # pendientes; no conservar valores previos de esos slots.
                    stack = ()
                aliases = {"ax": "eax", "al": "eax", "ah": "eax",
                           "bx": "ebx", "bl": "ebx", "bh": "ebx",
                           "cx": "ecx", "cl": "ecx", "ch": "ecx",
                           "dx": "edx", "dl": "edx", "dh": "edx"}
                dest = aliases.get(dest, dest)
                if dest in REGS:
                    registers[dest] = None
                    if dest == "esp":
                        stack = ()
            successors = []
            if mnemonic not in ("ret", "int3", "jmp"):
                successors.append(address + size)
            if mnemonic.startswith("j"):
                target = scalar(operand)
                if target in by_va:
                    successors.append(target)
                elif address in jump_tables:
                    successors.extend(jump_tables[address])
                elif mnemonic == "jmp":
                    incomplete.append({"entry": entry, "va": address, "reason": "indirect_jump"})
            for target in successors:
                if target not in by_va or not entry - 0x10000 <= target <= entry + 0x10000:
                    continue
                next_state = (registers, stack)
                merged = join_state(states[target], next_state) if target in states else next_state
                if states.get(target) != merged:
                    states[target] = merged
                    work.append(target)
            visits += 1
        if work:
            incomplete.append({"entry": entry, "reason": "analysis_budget"})
    calls = [row for (entry, _), row in found.items() if len(entries[entry]) == 1]
    return calls, sorted(provenance, key=lambda x: (x["caller"], x["callee"])), incomplete


def census_instructions(ins, seeds=None, follow_wrappers=False, jump_tables=None):
    seeds = dict(SEEDS if seeds is None else seeds)
    calls, unknown = [], []
    for i, (address, _, mnemonic, operand) in enumerate(ins):
        if mnemonic != "call" or scalar(operand) is not None:
            continue
        target = value(ins, i, operand, seeds)
        if not target or target[0].rstrip("?") != "method":
            unknown.append({"va": address, "operand": operand,
                            "confidence": "unassigned",
                            "reason": "interface_provenance_not_recovered"})
            continue
        _, interface, origin, offset = target
        args = arguments(ins, i, seeds)
        this_matches = bool(args and args[0] and args[0][0].rstrip("?") == "interface"
                            and args[0][1:] == (interface, origin))
        entry = {"va": address, "interface": interface,
                 "method": method_name(interface, offset), "offset": offset,
                 "source_global_va": origin if isinstance(origin, int) else None,
                 "source_field_origin": origin if isinstance(origin, str) else None,
                 "confidence": "high" if this_matches and target[0] == "method" else "medium",
                 "this_argument_matches": this_matches,
                 "arguments": args, "context": ins[max(0, i-12):i+1]}
        if interface == "IDirect3DDevice9" and entry["method"] in (
                "SetRenderState", "SetTextureStageState", "SetSamplerState"):
            # args[0] es this; solo constancias demostradas por el slice.
            argc = 2 if entry["method"] == "SetRenderState" else 3
            entry["constant_arguments"], entry["constant_argument_choices"] = state_arguments(args, argc)
        calls.append(entry)
    provenance, incomplete = [], []
    if follow_wrappers:
        wrapper_calls, provenance, incomplete = forward_wrappers(ins, seeds, jump_tables)
        by_va = {row["va"]: row for row in calls}
        for row in wrapper_calls:
            if row["va"] not in by_va:
                by_va[row["va"]] = row
        calls = [by_va[va] for va in sorted(by_va)]
        unknown = [row for row in unknown if row["va"] not in by_va]
    counts = {}
    for interface in VTABLES:
        counts[interface] = [dict(method=method,
                                 high=sum(c["interface"] == interface and c["method"] == method
                                          and c["confidence"] == "high" for c in calls),
                                 medium=sum(c["interface"] == interface and c["method"] == method
                                            and c["confidence"] == "medium" for c in calls))
                             for method in VTABLES[interface]
                             if any(c["interface"] == interface and c["method"] == method for c in calls)]
    return {"calls": calls, "methods": counts, "unresolved_indirect_calls": unknown,
            "constant_states": [c for c in calls if "constant_arguments" in c],
            "seed_globals": {hex(k): v for k, v in sorted(seeds.items())},
            "reviewed_parameter_fields": PARAMETER_FIELDS,
            "reviewed_field_loads": {hex(k): v for k, v in sorted(REVIEWED_FIELD_LOADS.items())},
            "wrapper_provenance": provenance, "incomplete_wrapper_cfg": incomplete,
            "scope": "Lower bound from known globals, reviewed fields, bounded wrapper CFGs and absolute creation outputs. Unresolved includes imports, C++/CRT, data and COM; zero findings do not prove absence."}


def render_switches(pe):
    """Tablas MSVC revisadas de los dos helpers de estados del renderer.

    Solo metadatos del PE fijado; no se extrapolan límites a otros switches.
    El primero usa una tabla de índices de byte tras un límite de 0x22.
    """
    base = pe.OPTIONAL_HEADER.ImageBase
    selector = pe.get_data(0x404CB8 - base, 35)
    specs = ((0x404BA7, 0x404C80, max(selector) + 1),
             (0x404E49, 0x405014, 4))
    edges, metadata = {}, []
    for site, table, count in specs:
        if pe.get_data(site - base, 7) != b"\xff\x24\x85" + struct.pack("<I", table):
            raise ValueError("unexpected renderer switch encoding")
        targets = struct.unpack("<" + "I" * count, pe.get_data(table - base, 4 * count))
        if not all(0x401000 <= target < 0x857000 for target in targets):
            raise ValueError("renderer switch points outside .text")
        edges[site] = sorted(set(targets))
        metadata.append({"site": site, "table": table, "entries": count,
                         "targets": list(targets),
                         "selector_table": 0x404CB8 if site == 0x404BA7 else None,
                         "selector_count": 35 if site == 0x404BA7 else None})
    return edges, metadata


def census(exe=ROOT / "original/th123.exe"):
    raw = Path(exe).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("reference SHA256 mismatch")
    pe = pefile.PE(data=raw)
    guids = {}
    for va, interface, expected in (
            (0x86777C, "IDirectInput8A", "bf798030-483a-4da2-aa99-5d64ed369700"),
            (0x8676AC, "IDirectSound8", "c50a7e93-f395-4834-9ef6-7fa99de50966")):
        actual = str(uuid.UUID(bytes_le=pe.get_data(va - pe.OPTIONAL_HEADER.ImageBase, 16)))
        if actual != expected:
            raise ValueError("unexpected COM creation IID")
        guids[hex(va)] = dict(interface=interface, iid=actual)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    ins = []
    for section in pe.sections:
        if section.Characteristics & 0x20000000:
            ins.extend(md.disasm_lite(section.get_data(),
                                     pe.OPTIONAL_HEADER.ImageBase + section.VirtualAddress))
    signatures = {
        ("IDirect3D9", "CreateDevice"): (6, "IDirect3DDevice9"),
        ("IDirect3DDevice9", "GetSwapChain"): (2, "IDirect3DSwapChain9"),
        ("IDirect3DDevice9", "GetBackBuffer"): (4, "IDirect3DSurface9"),
        ("IDirect3DDevice9", "CreateTexture"): (7, "IDirect3DTexture9"),
        ("IDirect3DDevice9", "CreateVertexBuffer"): (5, "IDirect3DVertexBuffer9"),
        ("IDirect3DDevice9", "GetRenderTarget"): (2, "IDirect3DSurface9"),
        ("IDirect3DDevice9", "CreateRenderTarget"): (7, "IDirect3DSurface9"),
        ("IDirect3DTexture9", "GetSurfaceLevel"): (2, "IDirect3DSurface9"),
        ("IDirectSound8", "CreateSoundBuffer"): (2, "IDirectSoundBuffer"),
        ("IDirectSound8", "DuplicateSoundBuffer"): (2, "IDirectSoundBuffer"),
        ("IDirectInput8A", "CreateDevice"): (2, "IDirectInputDevice8A"),
    }
    seeds, derived = dict(SEEDS), []
    jump_tables, switch_metadata = render_switches(pe)
    for _ in range(4):
        result = census_instructions(ins, seeds, follow_wrappers=True, jump_tables=jump_tables)
        added = False
        for call in result["calls"]:
            signature = signatures.get((call["interface"], call["method"]))
            if not signature or not call["this_argument_matches"]:
                continue
            argument_index, interface = signature
            args = call["arguments"]
            if argument_index >= len(args) or not args[argument_index] or args[argument_index][0] != "constant":
                continue
            output = args[argument_index][1]
            # Solo slots absolutos dentro de la imagen de datos, nunca valores
            # de pila ni direcciones que el slice no haya recuperado.
            if not 0x857000 <= output < pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.SizeOfImage:
                continue
            if output not in seeds:
                seeds[output] = interface
                derived.append({"global_va": output, "interface": interface,
                                "creation_call": call["va"], "method": call["method"]})
                added = True
        if not added:
            break
    else:
        result = census_instructions(ins, seeds, follow_wrappers=True, jump_tables=jump_tables)
    result.update(sha256=SHA256, instruction_sweep=len(ins), vtables=VTABLES,
                  creation_iids=guids, derived_output_globals=derived,
                  render_switch_tables=switch_metadata)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    p.add_argument("--output", type=Path, default=ROOT / "artifacts/pe-inventory" / SHA256 / "com-usage.json")
    args = p.parse_args()
    result = census(args.exe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}: {len(result['calls'])} attributed calls; {len(result['unresolved_indirect_calls'])} unresolved")


if __name__ == "__main__":
    main()
