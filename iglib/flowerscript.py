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
    0x00: Op('dlg_str')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),  # Text
    0x01: Op('exit')
    .field(2, Type.HEXNUM),
    0x02: Op('jmp_script')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),  # Filename
    0x04: Op('val_set')
    .field(2, Type.HEXNUM)   # Address
    .field(4, Type.SG_DEC),  # Value

    # 0x64 - The 'yuri gauge', which shows a lily flower growing
    # 0x65 - Used during reasoning selections
    # 0x6c - Related to routes and endings

    0x05: Op('val_add')
    .field(2, Type.HEXNUM)   # Address
    .field(4, Type.SG_DEC),  # Value
    0x06: Op('jmp_eq')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)   # Address
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)   # Value
    .field(4, Type.OFFSET),  # Label
    0x08: Op('jmp_be')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)   # Address
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)   # Value
    .field(4, Type.OFFSET),  # Label
    0x09: Op('jmp_le')
    .field(2, Type.BARRAY)
    .field(2, Type.HEXNUM)   # Address
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)   # Value
    .field(4, Type.OFFSET),  # Label
    0x0c: Op('dlg_num')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),  # ? Sequence Number
    0x0d: Op('jmp')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),  # Label
    0x0e: Op('wait')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),  # Duration (ms)
    0x0f: Op('bg_0f')
    .field(1, Type.HEXNUM)   # ? Layer
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x10: Op('bg_10')
    .field(1, Type.HEXNUM)   # ? Layer
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x11: Op('fg_clear')
    .field(6, Type.HEXNUM),  # clear all fgs and avatar
    0x12: Op('fg_12')
    .field(1, Type.HEXNUM)   # ? Layer
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x13: Op('fg_metrics')
    .field(1, Type.HEXNUM)   # ? Layer
    .field(1, Type.UN_DEC)   # Scale %
    .field(2, Type.SG_DEC)   # X of center
    .field(2, Type.SG_DEC),  # Y of top
    0x14: Op('crossfade')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),  # Duration (ms)
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
    0x21: Op('mark_end')
    .field(2, Type.UN_DEC),  # Ending No. (1-10)
    0x22: Op('bgm_play')
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC)   # Repeat
    .field(3, Type.BARRAY)
    .field(1, Type.STRLEN),  # Filename (w/o ext; .ogg)
    0x23: Op('bgm_stop')
    .field(2, Type.HEXNUM),
    0x24: Op('bgm_fadeout')
    .field(2, Type.HEXNUM)
    .field(4, Type.SG_DEC),  # Duration (ms)
    0x25: Op('bgm_fadein')
    .field(1, Type.HEXNUM)   # ?: 0, 1 have sound, others no sound
    .field(1, Type.UN_DEC)   # Repeat
    .field(4, Type.SG_DEC)   # Fade in (ms), must be positive
    .field(1, Type.STRLEN)   # Filename (w/o ext; .ogg)
    .field(3, Type.BARRAY),
    0x27: Op('v_play')
    .field(5, Type.BARRAY)
    .field(1, Type.STRLEN),
    0x28: Op('se_play')
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC)   # Repeat
    .field(3, Type.BARRAY)
    .field(1, Type.STRLEN),  # Filename (w/o ext; .ogg)
    0x29: Op('se_stop')
    .field(2, Type.HEXNUM),
    0x2a: Op('v_stop')   # ZhangHai - voice stop
    .field(2, Type.HEXNUM),
    0x2c: Op('se_fadeout')   # Fade out SE
    .field(2, Type.HEXNUM)
    .field(4, Type.UN_DEC),  # Duration (ms)
    0x2d: Op('se_fadein')
    .field(1, Type.HEXNUM)   # ?: 0, 1 have sound, others no sound
    .field(1, Type.UN_DEC)   # Repeat
    .field(4, Type.SG_DEC)   # Fade in (ms), must be positive
    .field(1, Type.STRLEN)   # Filename (w/o ext; .ogg)
    .field(3, Type.BARRAY),
    0x35: Op('yuri')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),  # 1:Up, 2:Dn
    0x36: Op('0x36')         # Zhanghai - NOP
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),
    0x3a: Op('0x3a')         # ZhangHai - set good end completed
    .field(2, Type.HEXNUM),
    0x3b: Op('jmp_nishuume')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x3f: Op('add_backlog')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0x40: Op('dlg_mode')
    .field(2, Type.UN_DEC),
    0x4c: Op('dlg_clear')         # ZhangHai: clear vertical messages
    .field(2, Type.HEXNUM),
    0x4d: Op('dlg_fade')         # ZhangHai: fade window
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)   # visible
    .field(4, Type.SG_DEC),  # duration ms
    0x50: Op('scr_eff')         # ZhangHai: screen effect (shaking etc.)
    .field(2, Type.BARRAY)
    .field(4, Type.HEXNUM)
    .field(4, Type.HEXNUM),
    0x51: Op('scr_eff_stop')    # ZhangHai
    .field(3, Type.BARRAY),
    0x54: Op('wait_click')
    .field(2, Type.HEXNUM),  # ZhangHai: 0:Invisible 1:MsgWait 2:MsgWait

    # ZhangHai - https://github.com/zhanghai/igtools/blob/master/igscript/igscript.main.kts#L330
    0x57: Op('0x57')
    .field(2, Type.HEXNUM),
    0x5d: Op('0x5d')
    .field(2, Type.HEXNUM),
    0x5e: Op('0x5e')
    .field(2, Type.HEXNUM),
    0x5f: Op('0x5f')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x60: Op('WHAT_THE_FUCK_0x60')
    .field(82, Type.BARRAY),
    0x61: Op('0x61')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),
    0x72: Op('fg_anim_a')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM)   # ? Layer
    .field(2, Type.SG_DEC)   # X of center (original size)
    .field(2, Type.SG_DEC)   # Y of top    (original size)
    .field(2, Type.SG_DEC)   # X scale %
    .field(2, Type.SG_DEC)   # Y scale %
    .field(2, Type.SG_DEC)   # Alpha (bigger, positive)
    .field(2, Type.BARRAY)
    .field(2, Type.SG_DEC)   # do { repeat; n -= 1; } while (n > 0);
    .field(2, Type.SG_DEC),
    0x73: Op('fg_anim_b')
    .field(1, Type.HEXNUM)   # ? Layer
    .field(1, Type.UN_DEC)   # ? Method (0:?, 1;?, 2:BA, 3:AB, 4:ABA, 5:AB)
    .field(2, Type.SG_DEC)   # X of center (original size)
    .field(2, Type.SG_DEC)   # Y of top    (original size)
    .field(2, Type.SG_DEC)   # X scale %
    .field(2, Type.SG_DEC)   # Y scale %
    .field(2, Type.SG_DEC)   # Alpha (smaller, positive)
    .field(2, Type.BARRAY)
    .field(2, Type.SG_DEC)   # Duration (ms)
    .field(2, Type.SG_DEC),
    0x74: Op('fg_anim_start')   # ? anim_run
    .field(2, Type.HEXNUM),
    0x75: Op('fg_anim_stop')    # ? anim_end
    .field(2, Type.HEXNUM),
    0x83: Op('0x83')
    .field(2, Type.BARRAY)
    .field(4, Type.SG_DEC),
    0x8b: Op('0x8b')
    .field(2, Type.HEXNUM),
    0x9c: Op('fg_9c')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb2: Op('play_video')   # ZhangHai - play video
    .field(2, Type.BARRAY)
    .field(2, Type.UN_DEC)   # 0: OP, 1: GrandFinaled
    .field(2, Type.BARRAY),
    0xb3: Op('0xb3')         # ZhangHai - play credits
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC),  # 1: TrueEnd, 3: NormalEnd
    0xb4: Op('fg_avatar')
    .field(1, Type.HEXNUM)
    .field(1, Type.STRLEN),
    0xb6: Op('dlg_mode')
    .field(2, Type.UN_DEC),  # 0: horizontal bottom, 1: vertical fullscreen
    0xb8: Op('nop_chapter')
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC),  # ? Chapter No.
    0xba: Op('0xba')
    .field(2, Type.HEXNUM),
    0xbb: Op('bgm_vol_bb')   # ZhangHai - fade out music
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade out (ms)
    .field(2, Type.BARRAY),
    0xbc: Op('bgm_vol_bc')   # ZhangHai - fade in music
    .field(1, Type.UN_DEC)   # Volume %
    .field(1, Type.HEXNUM)
    .field(2, Type.UN_DEC)   # Fade in (ms)
    .field(2, Type.BARRAY),
    0xbd: Op('glb_volume_bd')         # anim global volume
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade out (ms)
    .field(2, Type.BARRAY),
    0xbe: Op('glb_volume_be')         # ZhangHai - fade in all sounds
    .field(1, Type.HEXNUM)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade in (ms)
    .field(2, Type.BARRAY),
    0xbf: Op('0xbf')         # ZhangHai - play fg anim
    .field(14, Type.BARRAY),
    0xc0: Op('0xc0')         # ZhangHai - stop fg anim
    .field(14, Type.BARRAY)
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
        print('- Warning: not all jumps are pointing to an instruction -')
        for offset in label_set:
            text = fmt_offset(offset) + '.define_as(0x%x)' % offset
            print('=>', text)
            lines.append((offset, text))
        print('- end of warning -')
    return [x[1] for x in lines]


class Label:
    def __init__(self, asmer, name):
        self.name = name
        self.asmer = asmer

    def add_ref(self, offset, size):
        self.asmer.lbl_refs.append((self.name, offset, size))

    def define(self):
        self.asmer.lbl_offs[self.name] = len(self.asmer.bytes)

    def define_as(self, value):
        self.asmer.lbl_offs[self.name] = value


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
