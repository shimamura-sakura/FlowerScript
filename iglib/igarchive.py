#!/bin/env python3


def ig_encode(value):
    if value < 0:
        raise ValueError('value must be positive')
    result = bytearray()
    while True:
        result.append((value & 0x7F) << 1)
        value >>= 7
        if value == 0:
            break
    result.reverse()
    result[-1] |= 0x1
    return result


def ig_encode_data(data):
    result = bytearray()
    for num in data:
        result += ig_encode(num)
    return result


def ig_transform_data(data, xor=0x00):
    return bytearray(
        (data[i] ^ (i + 2) ^ xor) & 0xFF
        for i in range(len(data))
    )


def iga_create(files, xor=0x00, name_encoding='ascii'):
    descs = bytearray()
    names = bytearray()
    datas = bytearray()
    fn_beg = 0
    for name, data in files:
        name = name.encode(name_encoding)
        data = ig_transform_data(data, xor)
        # append to three blocks
        descs += ig_encode(fn_beg)
        descs += ig_encode(len(datas))
        descs += ig_encode(len(data))
        names += ig_encode_data(name)
        datas += data
        # update fn beg
        fn_beg = fn_beg + len(name)
    return b''.join((
        b'IGA0' + b'\0' * 4 + b'\2\0\0\0' * 2,
        ig_encode(len(descs)), descs,
        ig_encode(len(names)), names,
        datas,
    ))
