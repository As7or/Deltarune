import os, re


def _fix_name(name):
    return re.sub(r'#U([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), name)


def fix_encoding(root_dir):
    """Recorre root_dir y renombra archivos/carpetas con el patron #Uxxxx
    (encoding roto tipico de zips exportados desde Obsidian) a su caracter real.
    Devuelve cuantos se renombraron."""
    renamed = 0
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for fname in filenames:
            new = _fix_name(fname)
            if new != fname:
                os.rename(os.path.join(dirpath, fname), os.path.join(dirpath, new))
                renamed += 1
        for dname in dirnames:
            new = _fix_name(dname)
            if new != dname:
                os.rename(os.path.join(dirpath, dname), os.path.join(dirpath, new))
                renamed += 1
    return renamed

