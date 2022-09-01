class Label:
    def __init__(self):
        self.pos = []
        self.off = None

    def define(self, offset):
        self.off = offset

    def refer(self, size, offset):
        self.pos.append((offset, size))


class LabelAndScript:
    def __init__(self, label, script):
        self.label = label
        self.script = script

    # define the label, optional at offset
    def define(self, offset=None):
        if offset == None:
            offset = len(self.script.bytes)
        self.label.define(offset)
        # return a number, so the user can add a minus sign to make some indent
        return 0

    # refer to the label, adding a record
    def refer(self, size, offset):
        self.label.refer(size, offset)


class Script:
    def __init__(self):
        self.bytes = bytearray()
        self.labels = dict()

    # use 'label_XXX' to create a label
    def __getattribute__(self, name: str):
        if not name.startswith('label_'):
            return object.__getattribute__(self, name)
        if name not in self.labels:
            self.labels[name] = Label()
        return LabelAndScript(self.labels[name], self)

    # write an little endian number of size bytes, optional at offset
    def s_write_le(self, size, value, offset=None):
        # check range
        max_value = (1 << (size * 8))
        if value < 0:
            value += max_value
        if value < 0 or not value < max_value:
            raise ValueError('out of representable range')
        # generate data
        data = []
        for i in range(size):
            data.append(value & 0xFF)
            value >>= 8
        # adjust length
        if offset == None:
            offset = len(self.bytes)
        elif offset < 0 or offset > len(self.bytes):
            raise ValueError('offset out of range')
        # write data
        self.bytes[offset:offset+size] = data
        return offset

    # refer to a label as an offset, zero as placeholder
    def s_refer_lb(self, size, las, offset=None):
        offset = self.s_write_le(size, 0, offset)
        las.refer(size, offset)

    # write the offsets of all labels
    def s_apply_lb(self):
        for label in self.labels.values():
            for offset, size in label.pos:
                self.s_write_le(size, label.off, offset)

    # append data
    def s_append(self, data):
        self.bytes += data


class IGScript(Script):
    def __init__(self, encoding='cp932'):
        super().__init__()
        self.encoding = encoding

    def ig_opcode(self, opcode, data_size):
        self.s_write_le(1, opcode)
        self.s_write_le(1, data_size + 2)

    def ig_unknown(self, opcode, data):
        self.ig_opcode(opcode, len(data))
        self.s_append(bytes(data))

    # 0x00 - String
    def string(self, string, u1=0x00, tail=None):
        self.ig_opcode(0x00, 2)
        s_data = string.encode(self.encoding)
        if tail != None:
            s_data.extend(tail)
        self.s_write_le(1, u1)
        self.s_write_le(1, len(s_data))
        self.s_append(s_data)

    # 0x01 - Unknown
    def ig_0x01(self, u2=0x00):
        self.ig_opcode(0x01, 2)
        self.s_write_le(2, u2)

    # 0x02 - Call script
    def call_script(self, name, u1=0x00, tail=None):
        self.ig_opcode(0x02, 2)
        n_data = name.encode(self.encoding)
        if tail != None:
            n_data.extend(tail)
        self.s_write_le(1, u1)
        self.s_write_le(1, len(n_data))
        self.s_append(n_data)

    # 0x04 - Set value
    def set_value(self, data_addr, value):
        self.ig_opcode(0x04, 6)
        self.s_write_le(2, data_addr)
        self.s_write_le(4, value)

    # 0x0d - Jump
    def jmp(self, las, u2=0x0000):
        self.ig_opcode(0x0d, 6)
        self.s_write_le(2, u2)
        self.s_refer_lb(4, las)

    # 0x1b - End Choices
    def choices_end(self, choice_no):
        self.ig_opcode(0x1b, 2)
        self.s_write_le(2, choice_no)

    # 0x1c - Begin Choices
    def choices_beg(self, u2=0x0000):
        self.ig_opcode(0x1c, 2)
        self.s_write_le(2, u2)

    # 0x1d - Append Choice
    def choices_append(self, las, text, tail=None):
        self.ig_opcode(0x1d, 6)
        t_data = text.encode(self.encoding)
        if tail != None:
            t_data.extend(tail)
        self.s_write_le(2, len(t_data))
        self.s_refer_lb(4, las)
        self.s_append(t_data)

    # 0x3b - Second round (Nishuume)
    def jmp_nishuume(self, las, u2=0x0000):
        self.ig_opcode(0x3b, 6)
        self.s_write_le(2, u2)
        self.s_refer_lb(4, las)

    # 0x40 - Clear layer
    def clear_layer(self, layer):
        self.ig_opcode(0x40, 2)
        self.s_write_le(2, layer)
