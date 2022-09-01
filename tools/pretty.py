#!/bin/env python3
import struct
o_endless = (
    0x2E, 0x2F, 0x34, 0x4A, 0x4B, 0x76, 0x77, 0xA8, 0xA9, 0xAA, 0xAC
)
ext_table = (
    ((0x00, 0x02, 0x0f, 0x10, 0x12, 0x3f, 0x9c, 0xAE,
      0xB4), lambda buf: struct.unpack_from('<B', buf, 1)[0], (1, 2)),
    ((0x22, 0x27,
      0x28), lambda buf: struct.unpack_from('<B', buf, 5)[0], (5, 6)),
    ((0x25,
      0x2d), lambda buf: struct.unpack_from('<B', buf, 6)[0], (6, 7)),
    ([0x1d], lambda buf: struct.unpack_from('<H', buf, 0)[0], (0, 2))
)


def loadScriptData(data):
    offset = 0
    result = []
    length = len(data)
    while (o_begin := offset) < length:
        rs_item = []
        op_code = data[offset]
        assert op_code not in o_endless
        ins_len = data[offset+1]
        ins_dat = data[offset+2:offset+ins_len]
        offset += ins_len
        for cases, func, _ in ext_table:
            if op_code in cases:
                ext_len = func(ins_dat)
                ext_txt = data[offset:offset+ext_len]
                txt_len = ext_txt.find(b'\0')
                if txt_len != -1:
                    aft_dat = ext_txt[txt_len:]
                    ext_txt = ext_txt[:txt_len]
                    rs_item.append(aft_dat)
                ext_txt = ext_txt.decode('cp932')
                offset += ext_len
                rs_item.append(ext_txt)
                break
        rs_item.extend((ins_dat, op_code, o_begin))
        rs_item.reverse()
        result.append(rs_item)
    assert offset == length
    return result


def reprScriptData(parsed):
    max_aft = 0
    outtext = []
    max_dat = len(max(parsed, key=lambda o: len(o[2]))[2])
    for o in parsed:
        if len(o) > 4:
            if (l := len(o[4])) > max_aft:
                max_aft = l
    for offset, op_code, ins_dat, *ext in parsed:
        len_dat = len(ins_dat)
        dat_hex = ['%02x ' % b for b in ins_dat]
        for cases, _, rg in ext_table:
            if op_code in cases:
                for i in range(*rg):
                    dat_hex[i] = '__ '
        out_seg = ['%4x : %02x %2d | %s%s|' %
                   (offset, op_code, len_dat, ''.join(dat_hex),
                    (max_dat - len_dat) * '   ')]
        aft_len = 0
        txt_txt = ' |'
        if len(ext):
            if len(ext) > 1:
                aft_len = len(aft := ext[1])
                out_seg.append((' %02x' * aft_len) % tuple(aft))
                txt_txt = ' <-' + repr(ext[0])
            else:
                txt_txt = ' | ' + repr(ext[0])
        out_seg.append((max_aft - aft_len) * '   ' + txt_txt)
        outtext.append(''.join(out_seg))
    return '\n'.join(outtext)


import sys

with open(sys.argv[1], 'rb') as fp:
    data = loadScriptData(fp.read())

with open(sys.argv[2], 'w') as fp:
    fp.write(reprScriptData(data))