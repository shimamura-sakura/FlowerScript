import disigscript

with open('start.s', 'rb') as fp:
    d = disigscript.Decoder(fp)
    d.run()
    with open('start.dis.py', 'w') as fo:
        d.write_text(fo)
