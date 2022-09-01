# This script creates an 'start.s' that is identical to the one from 'FLOWERS - Le volume sur ete'

import flowerscript

s = flowerscript.IGScript()

s.clear_layer(0)
s.set_value(0x64, 0)
s.set_value(0x65, 0)
s.set_value(0x66, 0)
s.set_value(0x67, 0)
s.set_value(0x68, 0)
s.set_value(0x69, 0)
s.set_value(0x6A, 0)
s.set_value(0x6B, 0)
s.set_value(0x6C, 0x80)
s.set_value(0x6D, 0)
s.jmp_nishuume(s.label_nishuume, 0x0b)
s.jmp(s.label_saisho)
- s.label_nishuume.define()
s.choices_beg()
s.choices_append(s.label_saisho, '最初から見る')
s.choices_append(s.label_noprol, 'プロローグを見ない')
s.choices_end(0x64)
- s.label_saisho.define()
s.call_script('02a_00001.s')
s.ig_0x01()
- s.label_noprol.define()
s.call_script('02a_01000.s')
s.ig_0x01()
s.call_script('02a_08000.s')
s.ig_0x01()

s.choices_beg()
s.choices_append(s.label_rodokugeki, '朗読劇')
s.choices_append(s.label_bareehappy, 'バレエ発表会')
s.choices_append(s.label_bareribetu, 'バレエ（離別エンド）')
s.choices_end(0x5a)

- s.label_bareribetu.define()
s.set_value(0x6a, 1)

- s.label_bareehappy.define()
s.call_script('02a_06550.s')
s.ig_0x01()

- s.label_rodokugeki.define()
s.call_script('02a_03950.s')
s.ig_0x01()

s.s_apply_lb()
with open('start.s', 'wb') as fp:
    fp.write(s.bytes)
