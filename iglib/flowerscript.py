import enum


ENCODING = 'cp932'


def le_fr(data, signed=False):
    value = shift = 0
    for b in data:
        value += b << shift
        shift += 8
    if signed and b & 0x80:
        value -= 1 << shift
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
    SG_DEC = 1
    UN_DEC = 2
    OFFSET = 3
    STRLEN = 4
    BARRAY = 5


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
            if tp == Type.SG_DEC:
                segs.append(fmt_number(le_fr(data, True), '%d'))
            if tp == Type.UN_DEC:
                segs.append(fmt_number(le_fr(data, False), '%d'))
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
    0x01: Op('end')
    .field(2, Type.HEXNUM),
    0x02: Op('jmp_script')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x04: Op('set_value')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
    0x05: Op('add_value')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
    0x06: Op('jmp_eq')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x08: Op('jmp_be')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x09: Op('jmp_le')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x0d: Op('jmp')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x0c: Op('dialog')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
    0x0e: Op('wait')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
    0x0f: Op('fgimage_0f')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x10: Op('bgimage_10')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x11: Op('dlg_noimg')
    .field(6, Type.HEXNUM),
    0x12: Op('fgimage_12')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x13: Op('image_opts')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC),
    0x14: Op('fade_in')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
    0x16: Op('bg_color')
    .field(2, Type.HEXNUM)
    .field(1, Type.UN_DEC)
    .field(1, Type.UN_DEC)
    .field(1, Type.UN_DEC)
    .field(1, Type.HEXNUM),
    0x1b: Op('sel_end')
    .field(2, Type.HEXNUM),
    0x1c: Op('sel_beg')
    .field(2, Type.HEXNUM),
    0x1d: Op('sel_add')
    .field(2, Type.STRLEN)
    .field(4, Type.OFFSET),
    0x1e: Op('0x1e')
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC),
    0x21: Op('0x21')
    .field(2, Type.UN_DEC),
    0x22: Op('bgm')
    .field(5, Type.BARRAY)
    .field(1, Type.STRLEN),
    0x23: Op('bgm_stop')
    .field(2, Type.HEXNUM),
    0x24: Op('bgm_fadeout')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),
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
    0x2d: Op('0x2d')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)
    .field(4, Type.SG_DEC)
    .field(1, Type.STRLEN)
    .field(3, Type.BARRAY),
    0x35: Op('yuri')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),
    0x3b: Op('jump_2shuume')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x3f: Op('add_record')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x40: Op('dlg_show')
    .field(2, Type.HEXNUM),
    0x4c: Op('0x4c')
    .field(2, Type.HEXNUM),
    0x4d: Op('0x4d')
    .field(2, Type.BARRAY)
    .field(4, Type.SG_DEC),
    0x50: Op('0x50')
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x51: Op('0x51')
    .field(3, Type.BARRAY),
    0x54: Op('wait_click')
    .field(2, Type.HEXNUM),
    0x57: Op('0x57')
    .field(2, Type.HEXNUM),
    0x72: Op('0x72')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(4, Type.BARRAY)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC),
    0x73: Op('0x73')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC)
    .field(4, Type.BARRAY)
    .field(2, Type.SG_DEC)
    .field(2, Type.SG_DEC),
    0x74: Op('0x74')
    .field(2, Type.HEXNUM),
    0x75: Op('0x75')
    .field(2, Type.HEXNUM),
    0x9c: Op('fgimage_9c')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb2: Op('play_op')
    .field(6, Type.BARRAY),
    0xb3: Op('0xb3')
    .field(2, Type.BARRAY),
    0xb4: Op('dlg_image')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb6: Op('0xb6')
    .field(2, Type.HEXNUM),
    0xb8: Op('0xb8')
    .field(2, Type.HEXNUM),
    0xba: Op('0xba')
    .field(2, Type.HEXNUM),
    0xbb: Op('0xbb')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0xbc: Op('0xbc')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0xbd: Op('0xbd')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0xbe: Op('0xbe')
    .field(2, Type.HEXNUM)
    .field(4, Type.HEXNUM),
}

OPS_BYNAME = dict(map(lambda kv: (kv[1].opname, (kv[0], kv[1])), OPS.items()))


statistics = {}


def disasm(fp, encoding=ENCODING):
    lines = []
    label_set = set()
    while len(data := fp.read(2)) == 2:
        offset = fp.tell() - 2
        opcode, opsize = data
        if opcode in OPS:
            statistics[opcode] = statistics.get(opcode, 0) + 1
            lines.append((offset, OPS[opcode].r(fp, encoding, label_set)))
        else:
            raise NotImplementedError(
                'unimplemented opcode %02x at offset %x' % (opcode, offset))
        # print(lines[-1])
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
            raise NotImplementedError('unknown op name %s' % opname)
        self.bytes.append(opcode)
        self.bytes.append(op.opsize)
        slen_off = slen_siz = None
        args = list(args)
        for size, tp in op.fields:
            if tp == Type.HEXNUM or tp == Type.SG_DEC or tp == Type.UN_DEC:
                value = args.pop(0)
                self.bytes.extend(le_to(value, size))
                continue
            if tp == Type.OFFSET:
                label = args.pop(0)
                label.add_ref(len(self.bytes), size)
                self.bytes.extend(le_to(-1, size))
                continue
            if tp == Type.STRLEN:
                slen_off = len(self.bytes)
                slen_siz = size
                self.bytes.extend(le_to(-1, size))
                continue
            if tp == Type.BARRAY:
                array = args.pop(0)
                if len(array) != size:
                    raise ValueError('data length not equal to definition')
                self.bytes.extend(array)
                continue
            raise Exception('should be unreachable !')
        if slen_off != None:
            str_dat = args.pop(0).encode(self.encoding)
            self.bytes.extend(str_dat)
            str_len = len(str_dat)
            if len(args) > 0:
                self.bytes.extend(args[0])
                str_len += len(args[0])
            self.bytes[slen_off:slen_off+slen_siz] = le_to(str_len, slen_siz)
