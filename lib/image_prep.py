import os, base64, subprocess, tempfile

GIF_RAW_LIMIT = 300 * 1024  # bytes: si el gif ya pesa menos que esto, se usa tal cual

_cache = {}

def prepare_image(path, maxw=220):
    """Devuelve (mime, b64) o (None, None) si no existe / falla."""
    key = (path, maxw)
    if key in _cache:
        return _cache[key]
    if not os.path.exists(path):
        _cache[key] = (None, None)
        return None, None

    ext = os.path.splitext(path)[1].lower()

    if ext == ".gif":
        size = os.path.getsize(path)
        if size <= GIF_RAW_LIMIT:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            result = ("image/gif", b64)
        else:
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
                out_path = tmp.name
            try:
                cmd = [
                    "ffmpeg", "-y", "-i", path, "-t", "4",
                    "-vf", f"fps=8,scale={maxw}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=48[p];[s1][p]paletteuse",
                    out_path, "-loglevel", "error"
                ]
                subprocess.run(cmd, check=True)
                with open(out_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                result = ("image/gif", b64)
            except Exception:
                result = (None, None)
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)
    else:
        try:
            from PIL import Image
            import io
            im = Image.open(path)
            im = im.convert("RGBA")
            w, h = im.size
            if w > maxw:
                im = im.resize((maxw, int(h * maxw / w)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            result = ("image/png", b64)
        except Exception:
            result = (None, None)

    _cache[key] = result
    return result

