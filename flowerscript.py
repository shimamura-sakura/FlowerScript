import enum


ENCODING = 'cp932'


def le_fr(data):
    value = shift = 0
    for b in data:
        value += b << shift
        shift += 8
    return value


def le_to(value, size):
    maxval = 1 << (size * 8)
    if value < 0:
        value += maxval
    if value < 0 or not value < maxval:
        raise ValueError('number out of range')
    return [(value >> (i * 8)) & 0xFF for i in range(size)]


def fmt_number(number, fmt='0x%02x'):
    return fmt % number


def fmt_offset(offset):
    return 's.label_0x%x' % offset


def fmt_list(data):
    return '[%s]' % (', '.join(fmt_number(x) for x in data))


class Type(enum.Enum):
    HEXNUM = 0
    DECNUM = 1
    OFFSET = 2
    STRLEN = 3
    BARRAY = 4


class Op:
    def __init__(self, opname):
        self.opname = opname
        self.opsize = 2
        self.fields = []

    def field(self, size, ig_type):
        self.fields.append((size, ig_type))
        self.opsize += size
        return self

    def r(self, fp, encoding, label_set):
        segs = []
        slen = None
        for size, tp in self.fields:
            data = fp.read(size)
            if tp == Type.HEXNUM:
                segs.append(fmt_number(le_fr(data)))
            if tp == Type.DECNUM:
                segs.append(fmt_number(le_fr(data), '%d'))
            if tp == Type.OFFSET:
                offset = le_fr(data)
                label_set.add(offset)
                segs.append(fmt_offset(offset))
            if tp == Type.STRLEN:
                slen = le_fr(data)
            if tp == Type.BARRAY:
                segs.append(fmt_list(data))
        if slen != None:
            data = fp.read(slen)
            if (i := data.find(0)) == -1:
                tail = None
            else:
                data, tail = data[:i], data[i:]
            segs.append(repr(data.decode(encoding)))
            if tail != None:
                segs.append(fmt_list(tail))
        return 's.op(%s, %s)' % (repr(self.opname), ', '.join(segs))


OPS = {
    0x00: Op('str')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x01: Op('0x01')
    .field(2, Type.HEXNUM),
    0x02: Op('call_script')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x04: Op('set_value')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x05: Op('add_value')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x0d: Op('jump')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x0c: Op('dialog')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x0e: Op('wait')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x0f: Op('fgimage_0f')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x10: Op('bgimage_10')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x11: Op('dialog_end')
    .field(6, Type.HEXNUM),
    0x12: Op('fgimage_12')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x13: Op('image_opts')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)
    .field(2, Type.DECNUM)
    .field(2, Type.DECNUM),
    0x14: Op('fade_in')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x16: Op('0x16')
    .field(6, Type.BARRAY),
    0x1b: Op('choices_end')
    .field(2, Type.HEXNUM),
    0x1c: Op('choices_beg')
    .field(2, Type.HEXNUM),
    0x1d: Op('choices_add')
    .field(2, Type.STRLEN)
    .field(4, Type.OFFSET),
    0x21: Op('0x21')
    .field(2, Type.HEXNUM),
    0x22: Op('bgm')
    .field(5, Type.BARRAY)
    .field(1, Type.STRLEN),
    0x23: Op('0x23')
    .field(2, Type.HEXNUM),
    0x24: Op('0x24')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x27: Op('voice')
    .field(5, Type.BARRAY)
    .field(1, Type.STRLEN),
    0x28: Op('se')
    .field(5, Type.BARRAY)
    .field(1, Type.STRLEN),
    0x29: Op('0x29')
    .field(2, Type.HEXNUM),
    0x2a: Op('0x2a')
    .field(2, Type.HEXNUM),
    0x2c: Op('0x2c')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x35: Op('yuri')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),
    0x3b: Op('jmp_2shuume')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x3f: Op('add_record')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x40: Op('clear_layer')
    .field(2, Type.HEXNUM),
    0x54: Op('0x54')
    .field(2, Type.HEXNUM),
    0x72: Op('0x72')
    .field(18, Type.BARRAY),
    0x73: Op('0x73')
    .field(18, Type.BARRAY),
    0x74: Op('0x74')
    .field(2, Type.HEXNUM),
    0x75: Op('0x75')
    .field(2, Type.HEXNUM),
    0x9c: Op('fgimage_9c')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb2: Op('0xb2')
    .field(6, Type.BARRAY),
    0xb4: Op('dlg_image')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb8: Op('0xb8')
    .field(2, Type.HEXNUM),
    0xbb: Op('0xbb')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0xbc: Op('0xbc')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0xbd: Op('0xbd')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM)
}

OPS_BYNAME = dict(map(lambda kv: (kv[1].opname, (kv[0], kv[1])), OPS.items()))


def disasm(fp, encoding=ENCODING):
    lines = []
    label_set = set()
    while len(data := fp.read(2)) == 2:
        offset = fp.tell() - 2
        opcode, opsize = data
        if opcode in OPS:
            lines.append((offset, OPS[opcode].r(fp, encoding, label_set)))
        else:
            raise NotImplementedError(
                'unimplemented opcode %02x at offset %x' % (opcode, offset))
    i = 0
    while i < len(lines):
        offset, line = lines[i]
        if offset in label_set:
            label_set.remove(offset)
            lines.insert(i, (offset, fmt_offset(offset) + '.define()'))
            i += 1
        i += 1
    if len(label_set) > 0:
        raise Exception('jump into the middle of an op ?')
    return [x[1] for x in lines]


class Label:
    def __init__(self, asmer, name):
        self.name = name
        self.asmer = asmer

    def add_ref(self, offset, size):
        self.asmer.lbl_refs.append((self.name, offset, size))

    def define(self):
        self.asmer.lbl_offs[self.name] = len(self.asmer.bytes)


class Assembler:
    def __init__(self, encoding=ENCODING):
        self.encoding = encoding
        self.bytes = bytearray()
        self.lbl_refs = []
        self.lbl_offs = {}

    def __getattribute__(self, name):
        if name.startswith('label_'):
            return Label(self, name)
        return object.__getattribute__(self, name)

    def finish(self):
        for name, offset, size in self.lbl_refs:
            value = self.lbl_offs[name]
            self.bytes[offset:offset+size] = le_to(value, size)

    def op(self, opname, *args):
        if opname in OPS_BYNAME:
            opcode, op = OPS_BYNAME[opname]
        else:
            raise NotImplementedError('unknown op name')
        self.bytes.append(opcode)
        self.bytes.append(op.opsize)
        slen_off = slen_siz = None
        args = list(args)
        for size, tp in op.fields:
            if tp == Type.HEXNUM or tp == Type.DECNUM:
                value = args.pop(0)
                self.bytes.extend(le_to(value, size))
            if tp == Type.OFFSET:
                label = args.pop(0)
                label.add_ref(len(self.bytes), size)
                self.bytes.extend(le_to(-1, size))
            if tp == Type.STRLEN:
                slen_off = len(self.bytes)
                slen_siz = size
                self.bytes.extend(le_to(-1, size))
            if tp == Type.BARRAY:
                array = args.pop(0)
                self.bytes.extend(array)
        if slen_off != None:
            str_dat = args.pop(0).encode(self.encoding)
            self.bytes.extend(str_dat)
            str_len = len(str_dat)
            if len(args) > 0:
                self.bytes.extend(args[0])
                str_len += len(args[0])
            self.bytes[slen_off:slen_off+slen_siz] = le_to(str_len, slen_siz)
