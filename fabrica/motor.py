"""Motor de la fábrica de superhéroes: guion JSON -> Short vertical 1080x1920 dinámico con voz, subtítulos y efectos.

Tipos de escena: titulo, ficha, dos_fichas, mosaico, medallones, cifra, versus, lista, bucle.
Todo el arte es original (sin personajes ni logotipos de terceros). Ver GUIONES.md.
"""
import os, sys, json, math, random, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arte import *
import cairocffi as cairo

PALETA = ["#1F3B8A", "#8A1F2B", "#4B1F7A", "#7A5A12", "#14532D", "#3A3F55", "#0E5E6F", "#7A2E12"]
COLORES_TXT = {"cromo": None, "verde": GREEN, "rojo": RED, "amarillo": YEL, "blanco": WHITE, "dorado": GOLD}
GAP = 0.12
MAX_DUR = 29.4

def col(c, i=0):
    if isinstance(c, str) and c.startswith("#"): return hexc(c)
    return hexc(PALETA[i % len(PALETA)])

def linea_titulo(ctx, l, y, size, i):
    if isinstance(l, str): l = {"t": l, "c": "cromo" if i == 0 else "verde"}
    c = l.get("c", "cromo")
    if c == "cromo": glow_text(ctx, l["t"], CX, y, size, WHITE, (1, 1, 1), chrome=True, maxw=880)
    else:
        cc = COLORES_TXT.get(c, GREEN); glow_text(ctx, l["t"], CX, y, size, cc, cc, maxw=880)

def ficha_dict(f, i, t):
    nombre = f.get("arte", "estrella")
    pjs = f.get("personajes") or ([f["personaje"]] if f.get("personaje") else [])
    def arte_ficha(ctx, x, y, s, tt, n=nombre, pjs=pjs):
        if not pjs: return dibujar_arte(ctx, n, x, y, s, tt)
        k = len(pjs[:3]); paso = s * 1.6 / max(1, k)
        for j, p in enumerate(pjs[:3]):
            dibujar_personaje(ctx, p, x + (j - (k - 1) / 2) * paso * 1.05, y + s * 0.35, s * (2.6 if k == 1 else 2.1), "busto", fallback=n, t=tt)
    return {"title": f.get("titulo", "").upper(), "year": str(f.get("anio", "")), "col": col(f.get("color"), i), "art": arte_ficha}

# ---------------------------------------------------------------- escenas
def esc_titulo(ctx, e, lt, gt, dur, idx):
    lineas = e.get("lineas", [])
    for i, l in enumerate(lineas[:3]):
        k = ease_out_back((lt - i * 0.08) / 0.3)
        if k <= 0: continue
        ctx.save(); ctx.translate(CX, 330 + i * 125); ctx.scale(k, k); ctx.translate(-CX, -(330 + i * 125))
        linea_titulo(ctx, l, 330 + i * 125, 112 if i == 0 else 118, i); ctx.restore()
    y0 = 960 if len(lineas) >= 2 else 880
    pop = ease_out_back((lt - 0.15) / 0.35)
    if e.get("numero") is not None:
        ctx.save(); ctx.translate(CX, y0); ctx.scale(pop, pop)
        glow_text(ctx, str(e["numero"]), 0, 0, 520, GOLD, GOLD, font="Bangers"); ctx.restore()
    if e.get("personaje") and pop > 0 and ruta_personaje(e["personaje"]):
        ctx.save(); ctx.translate(CX, y0); ctx.scale(pop, pop)
        dibujar_personaje(ctx, e["personaje"], 0, 0, 640, "cuerpo", t=gt); ctx.restore()
    elif e.get("arte") and pop > 0:
        s = 300 if e.get("numero") is None else 140
        y = y0 if e.get("numero") is None else y0 + 330
        ctx.save(); ctx.translate(CX, y); ctx.scale(pop, pop); dibujar_arte(ctx, e["arte"], 0, 0, s, gt); ctx.restore()
    if e.get("pie"):
        k = ease_out_back((lt - 0.4) / 0.3)
        if k > 0:
            c = COLORES_TXT.get(e.get("pie_color", "rojo"), RED)
            ctx.save(); ctx.translate(CX, 1300); ctx.scale(k, k); glow_text(ctx, e["pie"], 0, 0, 96, c, c, maxw=880); ctx.restore()

def esc_ficha(ctx, e, lt, gt, dur, idx):
    m = ficha_dict(e, idx, gt)
    k = ease_out_back(lt / 0.38)
    cx = CX + (1 - k) * 900; rot = (-0.06 if idx % 2 == 0 else 0.06) * k + (1 - k) * 0.5
    glow = GOLD if e.get("destacar") else None
    card(ctx, m, cx, 830, 560, 760, rot, gt, check=ease_out_back((lt - 0.45) / 0.25) if e.get("check", True) else 0, glow=glow)
    if e.get("rango"):
        rk = ease_out_back((lt - 0.2) / 0.3)
        if rk > 0:
            ctx.save(); ctx.translate(CX - 300, 470); ctx.rotate(-0.15); ctx.scale(rk, rk)
            glow_text(ctx, str(e["rango"]), 0, 0, 150, GOLD, GOLD, font="Bangers"); ctx.restore()
    if e.get("cifra"):
        k2 = ease_out_back((lt - 0.35) / 0.3)
        if k2 > 0:
            ctx.save(); ctx.translate(CX, 1335); ctx.scale(k2, k2); glow_text(ctx, e["cifra"], 0, 0, 84, GREEN, GREEN, maxw=840); ctx.restore()

def esc_dos_fichas(ctx, e, lt, gt, dur, idx):
    fs = e.get("fichas", [])[:2]
    if e.get("titulo"):
        k = ease_out_back(lt / 0.3)
        ctx.save(); ctx.translate(CX, 340); ctx.scale(k, k); glow_text(ctx, e["titulo"], 0, 0, 120, WHITE, (1, 1, 1), chrome=True, maxw=880); ctx.restore()
    for j, f in enumerate(fs):
        k = ease_out_back((lt - 0.12 - j * 0.25) / 0.35)
        if k <= 0: continue
        x = CX - 215 + j * 430; y = 840 + j * 40
        sx = (-1 if j == 0 else 1) * (1 - k) * 700
        card(ctx, ficha_dict(f, idx + j, gt), x + sx, y, 410, 580, (-0.08 if j == 0 else 0.08), gt,
             check=ease_out_back((lt - 0.5 - j * 0.25) / 0.25) if f.get("check", True) else 0, glow=GOLD if f.get("destacar") else None)
    if e.get("pie"):
        k = ease_out_back((lt - 0.7) / 0.3)
        if k > 0:
            c = COLORES_TXT.get(e.get("pie_color", "rojo"), RED)
            ctx.save(); ctx.translate(CX, 1300); ctx.scale(k, k); glow_text(ctx, e["pie"], 0, 0, 100, c, c, maxw=880); ctx.restore()

def esc_mosaico(ctx, e, lt, gt, dur, idx):
    lineas = e.get("lineas", [])
    for i, l in enumerate(lineas[:2]): linea_titulo(ctx, l, 330 + i * 125, 108, i)
    fs = e.get("fichas", [])[:6]
    n = len(fs); cols = 3 if n > 4 else 2
    w, h = (240, 330) if cols == 3 else (330, 450)
    filas = math.ceil(n / cols); y0 = 640 if lineas else 520
    for j, f in enumerate(fs):
        r, c = divmod(j, cols)
        en_fila = min(cols, n - r * cols)
        x = CX + (c - (en_fila - 1) / 2) * (w + 22); y = y0 + h / 2 + r * (h + 26)
        a = ease_out_back((lt - j * 0.07) / 0.3)
        if a <= 0: continue
        ctx.save(); ctx.translate(x, y + math.sin(gt * 2 + j) * 6); ctx.scale(a, a)
        dest = e.get("destacar") == j
        card(ctx, ficha_dict(f, idx + j, gt), 0, 0, w, h, 0, gt, check=1.0 if f.get("check") or dest else 0, glow=GOLD if dest else None)
        ctx.restore()

def esc_medallones(ctx, e, lt, gt, dur, idx):
    lineas = e.get("lineas", [])
    for i, l in enumerate(lineas[:2]): linea_titulo(ctx, l, 330 + i * 125, 108, i)
    items = e.get("items", [])[:8]
    n = len(items); fila1 = math.ceil(n / 2) if n > 4 else n
    r = 122 if n > 4 else 145
    y1 = 700 if lineas else 620
    for j, it in enumerate(items):
        fila = 0 if j < fila1 else 1
        en = fila1 if fila == 0 else n - fila1; pos = j if fila == 0 else j - fila1
        x = CX + (pos - (en - 1) / 2) * (r * 2 + 24); y = y1 + fila * (r * 2 + 90)
        medallon(ctx, x, y, r, ("pj:" + it["personaje"]) if it.get("personaje") and ruta_personaje(it["personaje"]) else it.get("arte", "estrella"), it.get("texto", ""), col(it.get("color"), j), gt,
                 pop=ease_out_back((lt - j * 0.09) / 0.3))

def esc_cifra(ctx, e, lt, gt, dur, idx):
    kx = ease_out_back((lt - 0.05) / 0.35)
    if kx > 0:
        ctx.save(); ctx.translate(CX, 860); ctx.scale(kx, kx)
        explosion(ctx, 14, 12, 345, RED, t=gt, semilla=7); explosion(ctx, 0, 0, 305, YEL, t=gt, semilla=3); ctx.restore()
    if e.get("texto"):
        k = ease_out_back(lt / 0.3)
        ctx.save(); ctx.translate(CX, 520); ctx.scale(k, k); glow_text(ctx, e["texto"], 0, 0, 104, WHITE, (1, 1, 1), chrome=True, maxw=880); ctx.restore()
    if e.get("arte"):
        ctx.save(); ctx.translate(CX, 1210); s_ = ease_out_back((lt - 0.2) / 0.3); ctx.scale(s_, s_)
        dibujar_arte(ctx, e["arte"], 0, 0, 150, gt); ctx.restore()
    v = float(e.get("valor", 0)); dec = int(e.get("decimales", 0))
    cur = v * ease_out(lt / 0.8)
    s2 = f"{cur:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    glow_text(ctx, f"{e.get('prefijo', '')}{s2}{e.get('sufijo', '')}", CX, 860, 190, GREEN, GREEN, maxw=560)

def esc_versus(ctx, e, lt, gt, dur, idx):
    if e.get("titulo"): glow_text(ctx, e["titulo"], CX, 340, 110, WHITE, (1, 1, 1), chrome=True, maxw=880)
    for j, key in enumerate(("a", "b")):
        f = e.get(key, {})
        k = ease_out_back((lt - j * 0.12) / 0.35)
        x = CX - 220 + j * 440 + (-1 if j == 0 else 1) * (1 - k) * 700
        card(ctx, ficha_dict(f, idx + j, gt), x, 860, 400, 560, (-0.07 if j == 0 else 0.07), gt, check=0, glow=GOLD if f.get("destacar") else None)
    k = ease_out_back((lt - 0.45) / 0.25)
    if k > 0:
        ctx.save(); ctx.translate(CX, 860); ctx.rotate(-0.12); ctx.scale(k, k)
        explosion(ctx, 0, 0, 190, YEL, t=gt, semilla=11); glow_text(ctx, "VS", 0, 0, 170, WHITE, RED, font="Bangers"); ctx.restore()

def esc_lista(ctx, e, lt, gt, dur, idx):
    if e.get("titulo"): glow_text(ctx, e["titulo"], CX, 360, 104, WHITE, (1, 1, 1), chrome=True, maxw=880)
    items = e.get("items", [])[:5]; n = max(1, len(items))
    paso = max(0.25, (dur - 0.3) / n)
    for j, it in enumerate(items):
        k = ease_out_back((lt - j * paso) / 0.3)
        if k <= 0: continue
        y = 560 + j * 165
        ctx.save(); ctx.translate((1 - k) * -700, 0)
        rrect(ctx, CX - 400, y - 62, 800, 124, 30); ctx.set_source_rgba(0, 0, 0, 0.55); ctx.fill_preserve()
        ctx.set_source_rgb(*(GOLD if j == 0 else GREEN)); ctx.set_line_width(6); ctx.stroke()
        ctx.arc(CX - 330, y, 46, 0, 6.2832); ctx.set_source_rgb(*(GOLD if j == 0 else GREEN)); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
        text(ctx, str(j + 1), CX - 330, y + 4, 62, BLACK, stroke=0)
        ctx.select_font_face("Anton"); ctx.set_font_size(62)
        txt = str(it).upper(); tw = ctx.text_extents(txt)[4]; sz = 62 * min(1, 600 / max(1, tw))
        ctx.set_font_size(sz); fe = ctx.font_extents(); ctx.move_to(CX - 260, y + (fe[0] - fe[1]) / 2); ctx.text_path(txt)
        ctx.set_source_rgb(*BLACK); ctx.set_line_width(8); ctx.stroke_preserve(); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        ctx.restore()

def esc_protagonista(ctx, e, lt, gt, dur, idx):
    """Personaje de cuerpo entero al centro con rayos, título arriba y cifra/etiqueta abajo."""
    lineas = e.get("lineas", [])
    for i, l in enumerate(lineas[:2]):
        k = ease_out_back((lt - i * 0.08) / 0.3)
        if k > 0:
            ctx.save(); ctx.translate(CX, 330 + i * 125); ctx.scale(k, k); ctx.translate(-CX, -(330 + i * 125))
            linea_titulo(ctx, l, 330 + i * 125, 112, i); ctx.restore()
    pop = ease_out_back((lt - 0.1) / 0.4)
    if pop > 0:
        g = cairo.RadialGradient(CX, 900, 0, CX, 900, 420); c = col(e.get("color"), idx)
        g.add_color_stop_rgba(0, *light(c, 0.3), 0.55); g.add_color_stop_rgba(1, *c, 0)
        ctx.set_source(g); ctx.arc(CX, 900, 420, 0, 6.2832); ctx.fill()
        ctx.save(); ctx.translate(CX, 930 + (1 - pop) * 300); ctx.scale(pop, pop)
        dibujar_personaje(ctx, e.get("personaje", ""), 0, 0, 760, "cuerpo", fallback=e.get("arte", "estrella"), t=gt); ctx.restore()
    if e.get("cifra"):
        k = ease_out_back((lt - 0.45) / 0.3)
        if k > 0:
            ctx.save(); ctx.translate(CX, 1310); ctx.scale(k, k); glow_text(ctx, e["cifra"], 0, 0, 150, GREEN, GREEN, maxw=860); ctx.restore()
    elif e.get("etiqueta"):
        k = ease_out_back((lt - 0.45) / 0.3)
        if k > 0: pill(ctx, e["etiqueta"], CX, 1310, 64 * k + 1, GOLD, fg=BLACK, maxw=760)

ESCENAS = {"titulo": esc_titulo, "ficha": esc_ficha, "dos_fichas": esc_dos_fichas, "mosaico": esc_mosaico,
           "medallones": esc_medallones, "protagonista": esc_protagonista, "cifra": esc_cifra, "versus": esc_versus, "lista": esc_lista}

# ---------------------------------------------------------------- subtítulos karaoke
def trozos(texto):
    pal = texto.upper().split(); out = []; cur = []
    for p in pal:
        if cur and (len(" ".join(cur + [p])) > 20 or len(cur) >= 3):
            out.append(cur); cur = []
        cur.append(p)
        if p.endswith(("...", ",", ".", "?", "!", ":")) and len(cur) >= 1 and len(" ".join(cur)) > 6:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def subtitulos(ctx, caps, gt):
    for s, e, palabras, tiempos in caps:
        if s <= gt < e:
            act = 0
            for i, tp in enumerate(tiempos):
                if gt >= tp: act = i
            k = ease_out_back((gt - s) / 0.12)
            ctx.save(); ctx.translate(CX, 1470); ctx.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k)
            ctx.select_font_face("Anton"); size = 92; ctx.set_font_size(size)
            esp = ctx.text_extents(" ")[4] + 8
            anchos = [ctx.text_extents(p)[4] for p in palabras]
            tot = sum(anchos) + esp * (len(palabras) - 1)
            if tot > 840:
                f = 840 / tot; size *= f; ctx.set_font_size(size); anchos = [a * f for a in anchos]; esp *= f; tot = 840
            x = -tot / 2; fe = ctx.font_extents(); by = (fe[0] - fe[1]) / 2
            for i, p in enumerate(palabras):
                num = any(ch.isdigit() for ch in p)
                c = YEL if i == act else (GREEN if num else WHITE)
                ctx.new_path(); ctx.move_to(x, by); ctx.text_path(p)
                ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_source_rgba(0, 0, 0, 0.35); ctx.set_line_width(size * 0.3); ctx.stroke_preserve()
                ctx.set_source_rgb(*BLACK); ctx.set_line_width(size * 0.12); ctx.stroke_preserve()
                ctx.set_source_rgb(*c); ctx.fill()
                x += anchos[i] + esp
            ctx.restore(); return

# ---------------------------------------------------------------- producción
def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)

def _registrar_fuentes():
    d = os.path.expanduser("~/.fonts"); os.makedirs(d, exist_ok=True)
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
    nuevo = False
    for f in os.listdir(src):
        if f.endswith(".ttf") and not os.path.exists(os.path.join(d, f)):
            import shutil; shutil.copy(os.path.join(src, f), d); nuevo = True
    if nuevo: subprocess.run(["fc-cache", "-f"], capture_output=True)

def plan_escenas(g, tl, t_end):
    """Devuelve lista de (inicio, fin, escena, bloque_idx)."""
    esc = []
    for i, (b, (s, d)) in enumerate(zip(g["bloques"], tl)):
        lst = b.get("escenas") or [b.get("escena", {"tipo": "titulo", "lineas": [b["texto"]]})]
        ini = max(0, s - 0.06) if i else 0.0
        fin_b = (tl[i + 1][0] - 0.06) if i + 1 < len(tl) else t_end
        paso = (fin_b - ini) / len(lst)
        for j, e in enumerate(lst):
            esc.append([ini + j * paso, ini + (j + 1) * paso, e, i])
    primera = esc[0][2]
    for x in esc:
        if x[2].get("tipo") == "bucle": x[2] = dict(primera, _bucle=True)
    return esc

def producir(g, carpeta, log=print, solo_frames=None):
    t0 = time.time(); os.makedirs(os.path.join(carpeta, "voz"), exist_ok=True)
    _registrar_fuentes()
    # 1) voz
    tl = []; t = 0.0; arch = []
    if solo_frames is None or not os.path.exists(os.path.join(carpeta, "voz", "timeline.json")):
        import voz
        for i, b in enumerate(g["bloques"]):
            log(f"  bloque {i+1}/{len(g['bloques'])}: {b['texto']}")
            r = voz.generar(b.get("decir", b["texto"]), b["texto"], os.path.join(carpeta, "voz", f"{i:02d}.wav"), log=log)
            arch.append(r["archivo"]); tl.append([t, r["duracion"]]); t += r["duracion"] + GAP
        total = t - GAP
        if total > MAX_DUR:
            f = min(1.15, total / MAX_DUR); log(f"  ⚠ {total:.1f}s > {MAX_DUR}s: acelero la voz x{f:.2f}")
            t = 0.0
            for i, a in enumerate(arch):
                tmp = a.replace(".wav", "_r.wav"); _ff("-i", a, "-filter:a", f"atempo={f}", tmp); os.replace(tmp, a)
                import soundfile as sf; inf = sf.info(a); d = inf.frames / inf.samplerate
                tl[i] = [t, d]; t += d + GAP
        json.dump(tl, open(os.path.join(carpeta, "voz", "timeline.json"), "w"))
    tl = json.load(open(os.path.join(carpeta, "voz", "timeline.json")))
    arch = [os.path.join(carpeta, "voz", f"{i:02d}.wav") for i in range(len(tl))]
    t_end = round(tl[-1][0] + tl[-1][1] + 0.6, 2)
    esc = plan_escenas(g, tl, t_end)
    # subtítulos
    caps = []
    for b, (s, d) in zip(g["bloques"], tl):
        tz = trozos(b["texto"]); total = sum(len(" ".join(c)) + 3 for c in tz); tt = s
        for c in tz:
            dd = d * (len(" ".join(c)) + 3) / total
            tiempos = []; acc = tt; tot_c = sum(len(p) + 1 for p in c)
            for p in c: tiempos.append(acc); acc += dd * (len(p) + 1) / tot_c
            caps.append([tt, tt + dd, c, tiempos]); tt += dd
    caps[-1][1] = t_end
    serie = g.get("serie")
    # 2) video
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); ctx = cairo.Context(surf)
    def frame(gt, con_subs=True):
        i = max(k for k, x in enumerate(esc) if x[0] <= gt + 1e-6)
        s, e_, e, bi = esc[i]; lt = gt - s; dur = e_ - s
        if e.get("_bucle"): lt += 1.0
        tipo = e.get("tipo", "titulo")
        c = col(e.get("fondo") or e.get("color"), i)
        ctx.save()
        # cámara: golpe de zoom al entrar + zoom lento + sacudida
        z = 1 + 0.14 * (1 - ease_out(lt / 0.3)) + 0.035 * min(1, lt / max(dur, 0.1))
        sh = 0
        if tipo in ("cifra", "versus") or e.get("impacto"):
            tk = 0.8 if tipo == "cifra" else 0.45
            if tk <= lt < tk + 0.35: sh = 16 * (1 - (lt - tk) / 0.35)
        ox = math.sin(gt * 90) * sh; oy = math.cos(gt * 77) * sh
        estilo = e.get("estilo_fondo") or g.get("estilo_fondo") or "mixto"
        if tipo == "versus" and background_imagen(ctx, "fondo_versus", lt, dur): pass
        elif estilo == "imagen" or (estilo == "mixto" and i % 2 == 1):
            if not background_imagen(ctx, fondo_por_color(vivo(c)), lt, dur): background_comic(ctx, c, gt, cy=860)
        elif estilo in ("comic", "mixto"): background_comic(ctx, c, gt, cy=860)
        else: background(ctx, dark(c, 0.82), dark(c, 0.5), gt, cy=860)
        ctx.translate(CX + ox, 900 + oy); ctx.scale(z, z); ctx.translate(-CX, -900)
        ESCENAS.get(tipo, esc_titulo)(ctx, e, lt, gt, dur, i)
        if i > 0 and lt < 0.4: lineas_velocidad(ctx, 0.55 * (1 - lt / 0.4))
        if sh > 0: lineas_velocidad(ctx, min(0.6, sh / 16 * 0.6))
        if e.get("globo"):
            gp = ease_out_back((lt - 0.35) / 0.3)
            gy = 640 if tipo in ("titulo", "protagonista") else 520
            globo(ctx, e["globo"], CX + 190, gy, 430, 210, cola=(-1, 1), tipo=e.get("globo_tipo", "ovalo"), pop=gp)
        ctx.restore()
        b = g["bloques"][bi]
        if serie and b.get("paso"): series_bar(ctx, int(b["paso"]), int(serie.get("total", 5)), serie.get("texto", "").upper())
        if con_subs: subtitulos(ctx, caps, gt)
        if lt < 0.09 and i > 0:
            ctx.set_source_rgba(1, 1, 1, 0.45 * (1 - lt / 0.09)); ctx.paint()
        surf.flush()
    if solo_frames is not None:
        for tt, ruta in solo_frames: frame(tt); surf.write_to_png(ruta)
        return
    video_tmp = os.path.join(carpeta, "video_mudo.part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", video_tmp], stdin=subprocess.PIPE)
    nf = int(round(t_end * FPS))
    for f in range(nf):
        frame(f / FPS); p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError("falló el render de video")
    # miniatura
    frame(min(1.2, esc[0][1] - 0.05), con_subs=False); mini = os.path.join(carpeta, "miniatura.png"); surf.write_to_png(mini)
    # 3) audio
    inputs, flt, mezcla = [], [], []
    for i, (a, (s, d)) in enumerate(zip(arch, tl)):
        inputs += ["-i", a]; ms = int(s * 1000)
        flt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={ms}|{ms}[v{i}]")
    n = len(arch)
    flt.append("".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000[voz]")
    T = t_end
    flt.append(f"sine=f=55:d={T}:r=48000,volume=0.05[p1];sine=f=82.4:d={T}:r=48000,volume=0.035[p2];sine=f=110:d={T}:r=48000,tremolo=f=0.5:d=0.6,volume=0.02[p3];"
               f"[p1][p2][p3]amix=inputs=3:normalize=0,afade=t=in:d=0.3,afade=t=out:st={T-0.4}:d=0.4[pad]")
    for k, (s, e_, e, bi) in enumerate(esc):
        if k == 0: continue
        ms = int(s * 1000)
        flt.append(f"anoisesrc=d=0.3:c=pink:r=48000:a=0.3,bandpass=f=1400:w=1000,afade=t=in:d=0.12,afade=t=out:st=0.12:d=0.18,adelay={ms}|{ms}[w{k}]"); mezcla.append(f"[w{k}]")
        tipo = e.get("tipo")
        if tipo in ("ficha", "dos_fichas") and e.get("check", True):
            m2 = int((s + 0.45) * 1000)
            flt.append(f"sine=f=1320:d=0.16:r=48000,volume=0.1,afade=t=out:d=0.16,adelay={m2}|{m2}[d{k}]"); mezcla.append(f"[d{k}]")
        if tipo in ("cifra", "versus") or e.get("impacto"):
            m3 = int((s + (0.8 if tipo == "cifra" else 0.45)) * 1000)
            flt.append(f"sine=f=60:d=0.4:r=48000,volume=0.6,afade=t=out:d=0.4,adelay={m3}|{m3}[b{k}]"); mezcla.append(f"[b{k}]")
    flt.append(f"[voz][pad]{''.join(mezcla)}amix=inputs={2+len(mezcla)}:normalize=0:duration=longest,apad=whole_dur={T},atrim=0:{T},alimiter=limit=0.95[a]")
    audio = os.path.join(carpeta, "audio.m4a")
    _ff(*inputs, "-filter_complex", ";".join(flt), "-map", "[a]", "-ac", "2", "-c:a", "aac", "-b:a", "192k", audio)
    final = os.path.join(carpeta, "short_final.mp4"); tmp = final.replace(".mp4", ".part.mp4")
    _ff("-i", video_tmp, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", tmp)
    os.replace(tmp, final); os.remove(video_tmp)
    return {"video": final, "miniatura": mini, "duracion": t_end, "voz_real": True, "segundos_render": round(time.time() - t0, 1)}

if __name__ == "__main__":
    g = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "videos", g.get("id", "prueba"))
    print(producir(g, out))
