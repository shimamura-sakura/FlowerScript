# FlowerScript

An assembler / disassembler tool for InnocentGrey 's script format

Currently it can (dis)asm all scripts from

- FLOWERS Le volume sur ete.
- FLOWERS Le volume sur hiver.

Use `iglib` as a package

## Usage

```python
# Disasm

from iglib import flowerscript, igarchive

with open('script.s', 'rb') as fp:
    # gbk for chinese translated games
    result = flowerscript.disasm(fp, encoding='cp932')
with open('script.py', 'w') as fp:
    for line in result:
        print(line, file=fp)

# Assemble

s = flowerscript.Assembler(encoding='cp932')

# Example result: start.s from FLOWERS Le volume sur ete
# Many operations are documented in 'iglib/flowerscript.py'
s.op('dlg_show', 0)
s.op('set_value', 0x64, 0)
s.op('set_value', 0x65, 0)
s.op('set_value', 0x66, 0)
s.op('set_value', 0x67, 0)
s.op('set_value', 0x68, 0)
s.op('set_value', 0x69, 0)
s.op('set_value', 0x6a, 0)
s.op('set_value', 0x6b, 0)
s.op('set_value', 0x6c, 128)
s.op('set_value', 0x6d, 0)
s.op('jump_2shuume', 0x0b, s.label_0x64)
s.op('jmp', 0x00, s.label_0x9a)
s.label_0x64.define()
s.op('sel_beg', 0x00)
s.op('sel_add', s.label_0x9a, '最初から見る')
s.op('sel_add', s.label_0xad, 'プロローグを見ない')
s.op('sel_end', 0x64)
s.label_0x9a.define()
s.op('jmp_script', 0x00, '02a_00001.s')
s.op('end', 0x00)
s.label_0xad.define()
s.op('jmp_script', 0x00, '02a_01000.s')
s.op('end', 0x00)
s.op('jmp_script', 0x00, '02a_08000.s')
s.op('end', 0x00)
s.op('sel_beg', 0x00)
s.op('sel_add', s.label_0x134, '朗読劇')
s.op('sel_add', s.label_0x121, 'バレエ発表会')
s.op('sel_add', s.label_0x119, 'バレエ（離別エンド）')
s.op('sel_end', 0x5a)
s.label_0x119.define()
s.op('set_value', 0x6a, 1)
s.label_0x121.define()
s.op('jmp_script', 0x00, '02a_06550.s')
s.op('end', 0x00)
s.label_0x134.define()
s.op('jmp_script', 0x00, '02a_03950.s')
s.op('end', 0x00)
# End of example result

# Save the script
s.finish() # write all label offsets into their places
with open('script.s', 'wb') as fp:
    fp.write(s.bytes)

# Create IGA Archive
with open('example.iga', 'wb') as fp:
    fp.write(igarchive.iga_create(
        [
            ('start.s', s.bytes) # (name, data)
        ],
        xor = 0xFF # Use 0xFF for script.iga, otherwise 0x00
    ))
```
