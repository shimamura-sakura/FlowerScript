# FlowerScript

An assembler / disassembler tool for InnocentGrey 's script format

All sources are in `iglib/`

## Examples

Disassemble `script.s`, save result lines in `code.txt`

```python
with open('script.s', 'rb') as fp:
    lines = flowerscript.disasm(fp)
with open('output.py', 'w') as fp:
    fp.writelines(map(lambda l: l + '\n', lines))
```

Assemble and save to `script.s`

```python
import flowerscript
s = flowerscript.Assembler(encoding='cp932')

# - disassembly result here
s.op('clear_layer', 0x00)
s.op('set_value', 0x64, 0x00)
s.op('set_value', 0x65, 0x00)
s.op('set_value', 0x66, 0x00)
s.op('set_value', 0x67, 0x00)
s.op('set_value', 0x68, 0x00)
s.op('set_value', 0x69, 0x00)
s.op('set_value', 0x6a, 0x00)
s.op('set_value', 0x6b, 0x00)
s.op('set_value', 0x6c, 0x80)
s.op('set_value', 0x6d, 0x00)
s.op('jmp_2shuume', 0x0b, s.label_0x64)
s.op('jump', 0x00, s.label_0x9a)
s.label_0x64.define()
s.op('choices_beg', 0x00)
s.op('choices_add', s.label_0x9a, '最初から見る')
s.op('choices_add', s.label_0xad, 'プロローグを見ない')
s.op('choices_end', 0x64)
s.label_0x9a.define()
s.op('call_script', 0x00, '02a_00001.s')
s.op('0x01', 0x00)
s.label_0xad.define()
s.op('call_script', 0x00, '02a_01000.s')
s.op('0x01', 0x00)
s.op('call_script', 0x00, '02a_08000.s')
s.op('0x01', 0x00)
s.op('choices_beg', 0x00)
s.op('choices_add', s.label_0x134, '朗読劇')
s.op('choices_add', s.label_0x121, 'バレエ発表会')
s.op('choices_add', s.label_0x119, 'バレエ（離別エンド）')
s.op('choices_end', 0x5a)
s.label_0x119.define()
s.op('set_value', 0x6a, 0x01)
s.label_0x121.define()
s.op('call_script', 0x00, '02a_06550.s')
s.op('0x01', 0x00)
s.label_0x134.define()
s.op('call_script', 0x00, '02a_03950.s')
s.op('0x01', 0x00)
# - end

s.finish()
with open('script.s', 'wb') as fp:
    fp.write(s.bytes)
```
