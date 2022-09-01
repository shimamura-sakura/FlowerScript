#!/bin/env python3

import sys


def decode_le(data):
    value = 0
    shift = 0
    for b in data:
        value += b << shift
        shift += 8
    return value


def split_tail(data):
    i = data.find(0)
    if i == -1:
        return data, None
    return data[:i], data[i:]


def repr_hex(n, no_zero=False):
    if no_zero:
        return '0x%x' % n
    return '0x%02x' % n


def repr_list(data):
    text_segs = []
    for b in data:
        text_segs.append('0x%02x' % b)
    return '[%s]' % (', '.join(text_segs))


def repr_label(label):
    return 's.label_0x%x' % label


class Decoder:
    def __init__(self, fp, encoding='cp932'):
        self.fp = fp
        self.encoding = encoding
        self.label_offs = set()
        self.out_lines = []

    def read_le(self, size):
        return decode_le(self.fp.read(size))

    def write_text(self, fp):
        for offset, line in self.out_lines:
            if offset in self.label_offs:
                print('- %s.define()' % repr_label(offset), file=fp)
                self.label_offs.remove(offset)
            fp.write(line + '\n')
        if len(self.label_offs) > 0:
            raise ValueError('a jump into the middle of an instruction ?')

    def read_string(self, str_len):
        str_dat = self.fp.read(str_len)
        str_dat, tail = split_tail(str_dat)
        str_dat = str_dat.decode(self.encoding)
        return str_dat, tail

    def run(self):
        while True:
            offset = self.fp.tell()
            op = self.fp.read(2)
            if len(op) != 2:
                break
            opcode, op_len = op
            # 0x00 - String
            if opcode == 0x00:
                u1 = self.read_le(1)
                str_len = self.read_le(1)
                str_dat, tail = self.read_string(str_len)
                if tail == None:
                    line = 's.string(%s, %s)' % (
                        repr(str_dat), repr_hex(u1))
                else:
                    line = 's.string(%s, %s, %s)' % (
                        repr(str_dat), repr_hex(u1), repr_list(tail))
            # 0x01 - Unknown
            elif opcode == 0x01:
                u2 = self.read_le(2)
                line = 's.ig_0x01(%s)' % repr_hex(u2)
            # 0x02 - Call script
            elif opcode == 0x02:
                u1 = self.read_le(1)
                str_len = self.read_le(1)
                str_dat, tail = self.read_string(str_len)
                if tail == None:
                    line = 's.call_script(%s, %s)' % (
                        repr(str_dat), repr_hex(u1))
                else:
                    line = 's.call_script(%s, %s, %s)' % (
                        repr(str_dat), repr_hex(u1), repr_list(tail))
            # 0x04 - Set value
            elif opcode == 0x04:
                data_addr = self.read_le(2)
                value = self.read_le(4)
                line = 's.set_value(%s, %s)' % (
                    repr_hex(data_addr), repr_hex(value))
            # 0x0d - Jump
            elif opcode == 0x0d:
                u2 = self.read_le(2)
                label = self.read_le(4)
                self.label_offs.add(label)
                line = 's.jmp(%s, %s)' % (repr_label(label), repr_hex(u2))
            # 0x1b - End Choices
            elif opcode == 0x1b:
                choice_no = self.read_le(2)
                line = 's.choices_end(%s)' % (repr_hex(choice_no))
            # 0x1c - Begin Choices
            elif opcode == 0x1c:
                u2 = self.read_le(2)
                line = 's.choices_beg(%s)' % repr_hex(u2)
            # 0x1d - Append Choice
            elif opcode == 0x1d:
                str_len = self.read_le(2)
                label = self.read_le(4)
                self.label_offs.add(label)
                str_dat, tail = self.read_string(str_len)
                if tail == None:
                    line = 's.choices_append(%s, %s)' % (
                        repr_label(label), repr(str_dat))
                else:
                    line = 's.choices_append(%s, %s, %s)' % (
                        repr_label(label), repr(str_dat), repr_list(tail))
            # 0x3b - Second round (Nishuume)
            elif opcode == 0x3b:
                u2 = self.read_le(2)
                label = self.read_le(4)
                self.label_offs.add(label)
                line = 's.jmp_nishuume(%s, %s)' % (
                    repr_label(label), repr_hex(u2))
            # 0x40 - Clear layer
            elif opcode == 0x40:
                layer = self.read_le(2)
                line = 's.clear_layer(%s)' % repr_hex(layer)

            # Really unknown bytes, though not working for ops with string
            else:
                raise NotImplementedError(
                    'unimplemented op %s!' % repr_hex(opcode))
            # print(line)
            self.out_lines.append((offset, line))
