import os, re, shutil, unicodedata


def _fix_hex_escapes(name):
    """Arregla el patron #Uxxxx (un solo caracter mal escapado), típico de
    algunos exportadores de zip de Obsidian."""
    return re.sub(r'#U([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), name)


def _fix_cp437(name):
    """Arregla la doble corrupcion CP437<->UTF-8: bytes UTF-8 de un caracter
    acentuado que un paso intermedio interpreto como CP437, produciendo
    caracteres de dibujo de caja (├, ┬, │, ░, etc). Si el resultado sigue
    teniendo esos caracteres, el intento de arreglo no sirvio y se descarta."""
    try:
        fixed = name.encode('cp437').decode('utf-8')
        if any(c in fixed for c in ['├', '┬', '│', '░', '▒', '┤', '┴']):
            return name
        return fixed
    except Exception:
        return name


def _normalize_name(name):
    """Aplica, en orden, los dos arreglos de encoding conocidos y termina
    normalizando a NFC. Un mismo nombre puede llegar roto de dos formas
    distintas en el mismo zip (p. ej. 'Conexi#U00f3n' vs 'Conexi#U251c#U2502n'
    para la misma tilde) — ambos deben converger en el mismo nombre final NFC
    para que la resolucion de colisiones de abajo los detecte como duplicados
    del mismo archivo."""
    fixed = _fix_hex_escapes(name)
    fixed = _fix_cp437(fixed)
    return unicodedata.normalize('NFC', fixed)


def _merge_dir_into(src_dir, dst_dir, dropped):
    """Funde el contenido de src_dir dentro de dst_dir, que ya existe.
    Pasa esto cuando dos carpetas del vault -- una con el nombre roto y otra
    ya con el nombre correcto -- son en realidad la misma carpeta duplicada
    (típicamente un checkout/exportación repetido del mismo vault con dos
    encodings distintos). Para cada elemento de src_dir:
      - Si no existe ya en dst_dir, se mueve directamente.
      - Si existe y ambos son carpetas, se funde recursivamente.
      - Si existe y es un archivo (en cualquiera de los dos lados), se
        conserva el más reciente y se descarta el otro, igual que ya hace
        fix_encoding() para archivos duplicados dentro del mismo directorio.
    Al final, src_dir queda vacía y se borra."""
    for item in os.listdir(src_dir):
        src = os.path.join(src_dir, item)
        dst = os.path.join(dst_dir, item)
        if not os.path.exists(dst):
            os.rename(src, dst)
            continue
        if os.path.isdir(src) and os.path.isdir(dst):
            _merge_dir_into(src, dst, dropped)  # ya borra src al terminar
            continue
        # Colision real entre archivo(s)/carpeta(s) con el mismo nombre
        # final: nos quedamos con el más reciente.
        src_mtime = os.path.getmtime(src)
        dst_mtime = os.path.getmtime(dst)
        if src_mtime > dst_mtime:
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
            os.rename(src, dst)
            dropped.append((dst, src))
        else:
            if os.path.isdir(src):
                shutil.rmtree(src)
            else:
                os.remove(src)
            dropped.append((src, dst))
    os.rmdir(src_dir)


def fix_encoding(root_dir):
    """Recorre root_dir y renombra archivos/carpetas con encoding roto
    (patron #Uxxxx, doble corrupcion CP437, o forma Unicode NFD) a su nombre
    real en NFC.

    Si dos archivos distintos terminan resolviéndose al mismo nombre final
    (duplicados reales del mismo archivo, exportados en momentos distintos
    con corrupciones distintas), se conserva el que tenga la fecha de
    modificación más reciente y se descarta el otro, en vez de dejar que
    gane uno al azar según el orden de recorrido.

    Devuelve (renombrados, descartados) — 'descartados' es una lista de
    tuplas (ruta_borrada, ruta_conservada) para poder avisar de cada caso.
    """
    renamed = 0
    dropped = []
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        targets = {}
        for fname in filenames:
            new = _normalize_name(fname)
            targets.setdefault(new, []).append(fname)

        for new_name, originals in targets.items():
            if len(originals) == 1:
                old = originals[0]
                if new_name != old:
                    os.rename(os.path.join(dirpath, old), os.path.join(dirpath, new_name))
                    renamed += 1
                continue
            originals_full = [os.path.join(dirpath, o) for o in originals]
            originals_full.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            keeper = originals_full[0]
            final_path = os.path.join(dirpath, new_name)
            tmp_path = final_path + ".__keep_tmp__"
            os.rename(keeper, tmp_path)
            for loser in originals_full[1:]:
                if os.path.exists(loser):
                    os.remove(loser)
                    dropped.append((loser, final_path))
            os.rename(tmp_path, final_path)
            renamed += 1

        for dname in dirnames:
            new = _normalize_name(dname)
            if new == dname:
                continue
            old_path = os.path.join(dirpath, dname)
            new_path = os.path.join(dirpath, new)
            if os.path.exists(new_path):
                # La carpeta destino ya existe -- un os.rename directo aquí
                # fallaría con "OSError: Directory not empty" en Linux en
                # cuanto la carpeta correcta tuviera algún contenido (bug
                # real visto en CI: 'vault/Deltarune Teor├¡as' intentando
                # renombrarse sobre 'vault/Deltarune Teorías', que ya existe
                # con el vault completo dentro). En vez de fallar, se funde
                # el contenido de la carpeta rota dentro de la correcta.
                _merge_dir_into(old_path, new_path, dropped)
            else:
                os.rename(old_path, new_path)
            renamed += 1
    return renamed, dropped
