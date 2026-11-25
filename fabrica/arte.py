"""Arte vectorial plano de la fábrica (todo original: sin personajes ni logotipos de terceros)."""
import cairocffi as cairo, math, json, random, subprocess, sys, os, re

W, H, FPS = 1080, 1920, 30
CX = 490  # content centre (keeps right margin free for TikTok/Shorts UI)
GOLD = (0.98, 0.76, 0.18)
BLACK = (0.04, 0.04, 0.06)
WHITE = (1, 1, 1)

def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
def mix(c, d, t): return tuple(a + (b - a) * t for a, b in zip(c, d))
def light(c, t): return mix(c, (1, 1, 1), t)
def dark(c, t): return mix(c, (0, 0, 0), t)

GEMS = [
    dict(name="ESPACIO", col=hexc("#2F80ED"), place="EL TESERACTO", year="2011", icon="orbit"),
    dict(name="MENTE", col=hexc("#F2C94C"), place="CETRO DE LOKI", year="2012", icon="waves"),
    dict(name="REALIDAD", col=hexc("#EB3B3B"), place="EL ÉTER · SVARTALFHEIM", year="2013", icon="swirl"),
    dict(name="PODER", col=hexc("#9B51E0"), place="ORBE · MORAG", year="2014", icon="bolt"),
    dict(name="TIEMPO", col=hexc("#27AE60"), place="OJO DE AGAMOTTO", year="2016", icon="clock"),
    dict(name="ALMA", col=hexc("#F2862E"), place="VORMIR", year="2018", icon="flame"),
]

def ease_out_back(t):
    t = max(0, min(1, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def ease_out(t):
    t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def ease_in_out(t):
    t = max(0, min(1, t)); return 3 * t * t - 2 * t * t * t

random.seed(7)
STARS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(0, 6.28)) for _ in range(70)]

# ---------- primitives ----------
def background(ctx, base, ray, t, cx=CX, cy=880):
    ctx.set_source_rgb(*base); ctx.paint()
    n = 20; ang0 = t * 0.12
    for i in range(n):
        a = ang0 + i * 2 * math.pi / n
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, 2600, a, a + math.pi / n * 0.9)
        ctx.close_path()
    ctx.set_source_rgba(*ray, 0.55); ctx.fill()
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, 1300)
    g.add_color_stop_rgba(0, *light(ray, 0.15), 0.35)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.75)
    ctx.set_source(g); ctx.paint()
    for x, y, r, ph in STARS:
        a = 0.35 + 0.35 * math.sin(t * 2.5 + ph)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.move_to(x, y - r * 2); ctx.line_to(x + r * 0.5, y - r * 0.5); ctx.line_to(x + r * 2, y)
        ctx.line_to(x + r * 0.5, y + r * 0.5); ctx.line_to(x, y + r * 2); ctx.line_to(x - r * 0.5, y + r * 0.5)
        ctx.line_to(x - r * 2, y); ctx.line_to(x - r * 0.5, y - r * 0.5); ctx.close_path(); ctx.fill()

def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path()

def gem(ctx, cx, cy, r, col, alpha=1.0, glow=True):
    if r <= 1: return
    if glow:
        g = cairo.RadialGradient(cx, cy, r * 0.2, cx, cy, r * 2.0)
        g.add_color_stop_rgba(0, *col, 0.55 * alpha); g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g); ctx.arc(cx, cy, r * 2.0, 0, 6.2832); ctx.fill()
    tl, tr = (cx - 0.5 * r, cy - 0.55 * r), (cx + 0.5 * r, cy - 0.55 * r)
    gl, gr = (cx - r, cy - 0.12 * r), (cx + r, cy - 0.12 * r)
    gml, gmr = (cx - 0.33 * r, cy - 0.12 * r), (cx + 0.33 * r, cy - 0.12 * r)
    bot = (cx, cy + 0.9 * r)
    tm = (cx, cy - 0.55 * r)
    faces = [
        ([tl, gl, gml], light(col, 0.35)), ([tl, gml, tm], light(col, 0.55)),
        ([tm, gml, gmr], light(col, 0.25)), ([tm, gmr, tr], light(col, 0.45)),
        ([tr, gmr, gr], col),
        ([gl, gml, bot], dark(col, 0.05)), ([gml, gmr, bot], light(col, 0.12)),
        ([gmr, gr, bot], dark(col, 0.35)),
    ]
    for pts, c in faces:
        poly(ctx, pts); ctx.set_source_rgba(*c, alpha); ctx.fill()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*BLACK, alpha * 0.9); ctx.set_line_width(max(1.5, r * 0.025))
    for a, b in [(gl, gml), (gml, tl), (gml, tm), (gml, gmr), (gmr, tm), (gmr, tr), (gml, bot), (gmr, bot)]:
        ctx.move_to(*a); ctx.line_to(*b)
    ctx.stroke()
    poly(ctx, [tl, tr, gr, bot, gl]); ctx.set_line_width(max(3, r * 0.07))
    ctx.set_source_rgba(*BLACK, alpha); ctx.stroke()
    # sparkle highlight
    hx, hy, s = cx - 0.18 * r, cy - 0.38 * r, r * 0.12
    poly(ctx, [(hx, hy - s), (hx + s * 0.3, hy - s * 0.3), (hx + s, hy), (hx + s * 0.3, hy + s * 0.3),
               (hx, hy + s), (hx - s * 0.3, hy + s * 0.3), (hx - s, hy), (hx - s * 0.3, hy - s * 0.3)])
    ctx.set_source_rgba(1, 1, 1, 0.9 * alpha); ctx.fill()

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

def text(ctx, s, x, y, size, fill=WHITE, font="Bangers", stroke=10, anchor="c", alpha=1.0, maxw=None):
    ctx.select_font_face(font); ctx.set_font_size(size)
    ext = ctx.text_extents(s)
    if maxw and ext[4] > maxw:
        size *= maxw / ext[4]; ctx.set_font_size(size); ext = ctx.text_extents(s)
    tw = ext[4]
    fe = ctx.font_extents()
    bx = x - tw / 2 if anchor == "c" else x
    by = y + (fe[0] - fe[1]) / 2  # vertical centre on y
    ctx.move_to(bx, by); ctx.text_path(s)
    if stroke:
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_width(stroke)
        ctx.set_source_rgba(*BLACK, alpha); ctx.stroke_preserve()
    ctx.set_source_rgba(*fill, alpha); ctx.fill()
    return size

def pill(ctx, s, cx, cy, size, bg, fg=WHITE, font="Anton", padx=34, h=None, maxw=700):
    ctx.select_font_face(font); ctx.set_font_size(size)
    tw = ctx.text_extents(s)[4]
    if tw > maxw - 2 * padx:
        size *= (maxw - 2 * padx) / tw; ctx.set_font_size(size); tw = ctx.text_extents(s)[4]
    h = h or size * 1.45
    w = tw + 2 * padx
    rrect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
    ctx.set_source_rgb(*bg); ctx.fill_preserve()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
    text(ctx, s, cx, cy + 2, size, fg, font, stroke=0)

def icon(ctx, kind, cx, cy, r, col, t):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    c2 = light(col, 0.3)
    def strk(w=14):
        ctx.set_source_rgb(*BLACK); ctx.set_line_width(w + 10); ctx.stroke_preserve()
        ctx.set_source_rgb(*c2); ctx.set_line_width(w); ctx.stroke()
    if kind == "orbit":
        for k, (rx, ry, rot) in enumerate([(1.9, 0.55, -0.4), (1.9, 0.55, 0.5)]):
            ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot); ctx.scale(rx * r, ry * r)
            ctx.arc(0, 0, 1, 0, 6.2832); ctx.restore(); strk(10)
        for k in range(2):
            a = t * 1.5 + k * math.pi
            px, py = math.cos(a) * 1.9 * r, math.sin(a) * 0.55 * r
            rot = -0.4 if k == 0 else 0.5
            x = cx + px * math.cos(rot) - py * math.sin(rot); y = cy + px * math.sin(rot) + py * math.cos(rot)
            ctx.arc(x, y, 18, 0, 6.2832); ctx.set_source_rgb(*WHITE); ctx.fill_preserve()
            ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
    elif kind == "waves":
        for k in range(3):
            rr = r * (1.25 + 0.3 * k) + 10 * math.sin(t * 4 - k)
            for side in (-1, 1):
                a0 = math.pi - 0.6 if side < 0 else -0.6
                ctx.new_sub_path(); ctx.arc(cx, cy, rr, a0, a0 + 1.2); strk(12)
    elif kind == "swirl":
        for k in range(3):
            ctx.new_sub_path()
            for i in range(60):
                a = i / 59 * 4.5 + t * 1.2 + k * 2.09
                rr = r * (0.9 + i / 59 * 1.1)
                x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            strk(11)
    elif kind == "bolt":
        for side in (-1, 1):
            s = r * 0.9; ox = cx + side * r * 1.55; oy = cy - 10 + 8 * math.sin(t * 9 + side)
            pts = [(0, -1.1), (0.45, -1.1), (0.15, -0.15), (0.55, -0.15), (-0.2, 1.15), (0.0, 0.15), (-0.4, 0.15)]
            poly(ctx, [(ox + side * px * s * 0.6, oy + py * s * 0.6) for px, py in pts])
            ctx.set_source_rgb(*c2); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(7); ctx.stroke()
    elif kind == "clock":
        R = r * 1.55
        ctx.new_sub_path(); ctx.arc(cx, cy, R, 0, 6.2832); strk(12)
        for k in range(12):
            a = k * math.pi / 6
            ctx.move_to(cx + math.cos(a) * (R - 30), cy + math.sin(a) * (R - 30))
            ctx.line_to(cx + math.cos(a) * (R - 8), cy + math.sin(a) * (R - 8))
        ctx.set_source_rgb(*c2); ctx.set_line_width(8); ctx.stroke()
        a = t * 2.2 - math.pi / 2
        ctx.move_to(cx + math.cos(a) * (R - 10), cy + math.sin(a) * (R - 10))
        ctx.line_to(cx + math.cos(a) * (R + 40), cy + math.sin(a) * (R + 40)); strk(10)
    elif kind == "flame":
        fl = 1 + 0.06 * math.sin(t * 10)
        for k, (sc, c) in enumerate([(1.0, dark(col, 0.1)), (0.72, light(col, 0.35))]):
            s = r * 1.55 * sc
            ctx.move_to(cx, cy - s * 1.25 * fl)
            ctx.curve_to(cx + s * 0.35, cy - s * 0.6, cx + s * 0.95, cy - s * 0.2, cx + s * 0.8, cy + s * 0.45)
            ctx.curve_to(cx + s * 0.65, cy + s * 0.95, cx - s * 0.65, cy + s * 0.95, cx - s * 0.8, cy + s * 0.45)
            ctx.curve_to(cx - s * 0.95, cy - s * 0.2, cx - s * 0.35, cy - s * 0.6, cx, cy - s * 1.25 * fl)
            ctx.close_path(); ctx.set_source_rgb(*c); ctx.fill_preserve()
            ctx.set_source_rgb(*BLACK); ctx.set_line_width(8); ctx.stroke()


GREEN = hexc("#38E07B"); RED = hexc("#FF3B4E"); YEL = hexc("#FFD23F")
# ---------------- text effects ----------------
def glow_text(ctx, s, x, y, size, fill, glow, font="Anton", alpha=1.0, chrome=False, maxw=None, rot=0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot)
    ctx.select_font_face(font); ctx.set_font_size(size)
    tw = ctx.text_extents(s)[4]
    if maxw and tw > maxw:
        size *= maxw / tw; ctx.set_font_size(size); tw = ctx.text_extents(s)[4]
    fe = ctx.font_extents(); bx, by = -tw / 2, (fe[0] - fe[1]) / 2
    for wdt, a in [(size * 0.42, 0.10), (size * 0.28, 0.16), (size * 0.16, 0.25)]:
        ctx.new_path(); ctx.move_to(bx, by); ctx.text_path(s)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_width(wdt)
        ctx.set_source_rgba(*glow, a * alpha); ctx.stroke()
    ctx.new_path(); ctx.move_to(bx, by); ctx.text_path(s)
    ctx.set_line_width(size * 0.09); ctx.set_source_rgba(*BLACK, alpha); ctx.stroke_preserve()
    if chrome:
        g = cairo.LinearGradient(0, by - size * 0.75, 0, by)
        g.add_color_stop_rgba(0, 1, 1, 1, alpha); g.add_color_stop_rgba(0.45, 0.78, 0.8, 0.86, alpha)
        g.add_color_stop_rgba(0.55, 0.55, 0.58, 0.65, alpha); g.add_color_stop_rgba(1, 0.95, 0.96, 1, alpha)
        ctx.set_source(g)
    else:
        ctx.set_source_rgba(*fill, alpha)
    ctx.fill(); ctx.restore()

def series_bar(ctx, k, n=5, label="TOP 5 TAQUILLA MARVEL"):
    x, y, w, h = CX - 330, 285, 660, 74
    rrect(ctx, x - 6, y - 6, w + 12, h + 12, 43); ctx.set_source_rgba(*GREEN, 0.25); ctx.fill()
    rrect(ctx, x, y, w, h, 37); ctx.set_source_rgb(*dark(GREEN, 0.55)); ctx.fill_preserve()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
    text(ctx, f"{label} · {k}/{n}", CX, y + h / 2 + 2, 44, WHITE, font="Anton", stroke=7)
    # progress
    py = y + h + 22
    rrect(ctx, x + 30, py, w - 60, 14, 7); ctx.set_source_rgba(1, 1, 1, 0.18); ctx.fill()
    rrect(ctx, x + 30, py, (w - 60) * k / n, 14, 7); ctx.set_source_rgb(*GREEN); ctx.fill()

def check_badge(ctx, x, y, r, pop=1.0):
    if pop <= 0: return
    r *= pop
    g = cairo.RadialGradient(x, y, r * 0.5, x, y, r * 1.8)
    g.add_color_stop_rgba(0, *GREEN, 0.6); g.add_color_stop_rgba(1, *GREEN, 0)
    ctx.set_source(g); ctx.arc(x, y, r * 1.8, 0, 6.2832); ctx.fill()
    ctx.arc(x, y, r, 0, 6.2832); ctx.set_source_rgb(*GREEN); ctx.fill_preserve()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(r * 0.14); ctx.stroke()
    ctx.move_to(x - r * 0.45, y + r * 0.02); ctx.line_to(x - r * 0.12, y + r * 0.38); ctx.line_to(x + r * 0.5, y - r * 0.4)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(r * 0.34); ctx.stroke_preserve()
    ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(r * 0.2); ctx.stroke()

# ---------------- original card art (no franchise characters/logos) ----------------
def art_robot(ctx, cx, cy, s, t):
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(cx, cy - s * 0.95); ctx.line_to(cx, cy - s * 0.62); ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.05); ctx.stroke()
    ctx.arc(cx, cy - s * 0.98, s * 0.07, 0, 6.2832); ctx.set_source_rgb(*RED); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(5); ctx.stroke()
    rrect(ctx, cx - s * 0.62, cy - s * 0.62, s * 1.24, s * 1.05, s * 0.18)
    g = cairo.LinearGradient(cx - s, 0, cx + s, 0); g.add_color_stop_rgb(0, 0.82, 0.84, 0.9); g.add_color_stop_rgb(1, 0.5, 0.53, 0.6)
    ctx.set_source(g); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.05); ctx.stroke()
    for ex in (-1, 1):
        rrect(ctx, cx + ex * s * 0.32 - s * 0.17, cy - s * 0.32, s * 0.34, s * 0.16, s * 0.06)
        ctx.set_source_rgb(*RED); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(5); ctx.stroke()
    rrect(ctx, cx - s * 0.36, cy + s * 0.05, s * 0.72, s * 0.2, s * 0.04); ctx.set_source_rgb(0.2, 0.2, 0.25); ctx.fill()
    for k in range(5):
        x = cx - s * 0.28 + k * s * 0.14
        ctx.move_to(x, cy + s * 0.07); ctx.line_to(x, cy + s * 0.23)
    ctx.set_source_rgb(0.75, 0.75, 0.8); ctx.set_line_width(4); ctx.stroke()
    # shoulders
    ctx.move_to(cx - s * 0.95, cy + s * 0.95); ctx.curve_to(cx - s * 0.9, cy + s * 0.5, cx + s * 0.9, cy + s * 0.5, cx + s * 0.95, cy + s * 0.95)
    ctx.close_path(); ctx.set_source_rgb(0.45, 0.48, 0.55); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.05); ctx.stroke()

def art_city(ctx, cx, cy, s, t):
    # portal
    pr = s * 0.42
    g = cairo.RadialGradient(cx, cy - s * 0.45, 0, cx, cy - s * 0.45, pr * 1.6)
    g.add_color_stop_rgba(0, 0.6, 0.9, 1, 0.9); g.add_color_stop_rgba(0.6, 0.2, 0.5, 1, 0.5); g.add_color_stop_rgba(1, 0.2, 0.5, 1, 0)
    ctx.set_source(g); ctx.arc(cx, cy - s * 0.45, pr * 1.6, 0, 6.2832); ctx.fill()
    for k in range(3):
        ctx.new_sub_path()
        for i in range(50):
            a = i / 49 * 5 + t * 2 + k * 2.1; rr = pr * (0.1 + i / 49 * 0.9)
            (ctx.move_to if i == 0 else ctx.line_to)(cx + math.cos(a) * rr, cy - s * 0.45 + math.sin(a) * rr * 0.6)
        ctx.set_source_rgba(1, 1, 1, 0.8); ctx.set_line_width(5); ctx.stroke()
    # skyline
    random.seed(3); x = cx - s;
    while x < cx + s:
        bw = s * random.uniform(0.18, 0.3); bh = s * random.uniform(0.5, 1.1)
        ctx.rectangle(x, cy + s * 0.95 - bh, bw, bh); ctx.set_source_rgb(0.12, 0.13, 0.22); ctx.fill_preserve()
        ctx.set_source_rgb(*BLACK); ctx.set_line_width(4); ctx.stroke()
        for wy in range(int(bh / (s * 0.12))):
            for wx in range(int(bw / (s * 0.1))):
                if random.random() < 0.55:
                    ctx.rectangle(x + s * 0.03 + wx * s * 0.1, cy + s * 0.95 - bh + s * 0.05 + wy * s * 0.12, s * 0.05, s * 0.06)
        ctx.set_source_rgb(*YEL); ctx.fill()
        x += bw

def art_web(ctx, cx, cy, s, t):
    for k, (dx, dy) in enumerate([(-0.55, -0.2), (0.55, -0.2), (0, 0.35)]):
        ctx.save(); ctx.translate(cx + dx * s, cy + dy * s); ctx.rotate(t * (1.5 if k % 2 else -1.5))
        ctx.set_dash([18, 12]); ctx.arc(0, 0, s * 0.38, 0, 6.2832)
        ctx.set_source_rgb(1, 0.65, 0.15); ctx.set_line_width(9); ctx.stroke(); ctx.set_dash([])
        ctx.restore()
    n = 10
    for i in range(n):
        a = i * 2 * math.pi / n
        ctx.move_to(cx, cy); ctx.line_to(cx + math.cos(a) * s * 1.1, cy + math.sin(a) * s * 1.1)
    for rr in (0.25, 0.5, 0.75, 1.0):
        for i in range(n + 1):
            a = i * 2 * math.pi / n; p = (cx + math.cos(a) * s * rr, cy + math.sin(a) * s * rr)
            (ctx.move_to if i == 0 else ctx.line_to)(*p)
    ctx.set_source_rgba(1, 1, 1, 0.85); ctx.set_line_width(4); ctx.stroke()

def art_gems(ctx, cx, cy, s, t):
    for i in range(6):
        a = t * 0.6 + i * math.pi / 3 - math.pi / 2
        gem(ctx, cx + math.cos(a) * s * 0.62, cy + math.sin(a) * s * 0.62, s * 0.24, GEMS[i]["col"])
    text(ctx, "6", cx, cy + 6, s * 0.7, GOLD, stroke=12)

def art_hourglass(ctx, cx, cy, s, t):
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, s * 1.2)
    g.add_color_stop_rgba(0, 1, 0.85, 0.3, 0.55); g.add_color_stop_rgba(1, 1, 0.85, 0.3, 0)
    ctx.set_source(g); ctx.arc(cx, cy, s * 1.2, 0, 6.2832); ctx.fill()
    w, h = s * 0.55, s * 0.85
    for yy in (-h, h):
        rrect(ctx, cx - w * 1.25, cy + yy - s * 0.08, w * 2.5, s * 0.16, s * 0.05)
        ctx.set_source_rgb(*GOLD); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
    ctx.move_to(cx - w, cy - h + s * 0.08); ctx.line_to(cx + w, cy - h + s * 0.08); ctx.line_to(cx + s * 0.06, cy)
    ctx.line_to(cx + w, cy + h - s * 0.08); ctx.line_to(cx - w, cy + h - s * 0.08); ctx.line_to(cx - s * 0.06, cy); ctx.close_path()
    ctx.set_source_rgba(0.8, 0.95, 1, 0.35); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(7); ctx.stroke()
    lvl = 0.55 + 0.1 * math.sin(t)
    ctx.move_to(cx - w * lvl, cy - h * 0.15 - h * 0.5 * lvl); ctx.line_to(cx + w * lvl, cy - h * 0.15 - h * 0.5 * lvl); ctx.line_to(cx, cy - h * 0.05); ctx.close_path()
    ctx.set_source_rgb(*YEL); ctx.fill()
    ctx.move_to(cx - w * 0.8, cy + h - s * 0.1); ctx.line_to(cx + w * 0.8, cy + h - s * 0.1); ctx.line_to(cx, cy + h * 0.35); ctx.close_path(); ctx.fill()
    ctx.move_to(cx, cy); ctx.line_to(cx, cy + h * 0.4); ctx.set_source_rgb(*YEL); ctx.set_line_width(5); ctx.stroke()

def card(ctx, m, cx, cy, w, h, rot, t, check=1.0, glow=None):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot)
    x, y = -w / 2, -h / 2
    if glow:
        for k, a in [(40, 0.12), (24, 0.2), (12, 0.3)]:
            rrect(ctx, x - k, y - k, w + 2 * k, h + 2 * k, 30 + k); ctx.set_source_rgba(*glow, a); ctx.fill()
    rrect(ctx, x + 16, y + 22, w, h, 26); ctx.set_source_rgba(0, 0, 0, 0.55); ctx.fill()
    rrect(ctx, x, y, w, h, 26)
    g = cairo.LinearGradient(0, y, 0, y + h * 0.7); g.add_color_stop_rgb(0, *light(m["col"], 0.15)); g.add_color_stop_rgb(1, *dark(m["col"], 0.55))
    ctx.set_source(g); ctx.fill_preserve(); ctx.save(); ctx.clip()
    # spotlight
    rg = cairo.RadialGradient(0, y + h * 0.35, 0, 0, y + h * 0.35, w * 0.7)
    rg.add_color_stop_rgba(0, 1, 1, 1, 0.18); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    ctx.set_source(rg); ctx.paint()
    m["art"](ctx, 0, y + h * 0.36, w * 0.36, t)
    ctx.rectangle(x, y + h * 0.72, w, h * 0.28); ctx.set_source_rgb(0.04, 0.03, 0.08); ctx.fill()
    ctx.restore()
    rrect(ctx, x, y, w, h, 26); ctx.set_source_rgb(*BLACK); ctx.set_line_width(12); ctx.stroke()
    glow_text(ctx, m["title"], 0, y + h * 0.81, w * 0.12, WHITE, RED, maxw=w * 0.86)
    glow_text(ctx, m["year"], 0, y + h * 0.92, w * 0.09, light(RED, 0.2), RED)
    check_badge(ctx, x + w - 62, y + 62, 46, check)
    ctx.restore()

# ---------------- original mascot: "Palomito" popcorn bucket ----------------
def mascot(ctx, cx, cy, s, t, blink=True, point=False):
    bob = math.sin(t * 4) * s * 0.03; cy += bob
    # popcorn cloud
    random.seed(11)
    for k in range(14):
        a = math.pi + k / 13 * math.pi; r = s * 0.5
        px = cx + math.cos(a) * r * 0.95; py = cy - s * 0.55 + math.sin(a) * r * 0.45
        ctx.arc(px, py, s * random.uniform(0.17, 0.23), 0, 6.2832)
        ctx.set_source_rgb(*BLACK); ctx.fill()
    random.seed(11)
    for k in range(14):
        a = math.pi + k / 13 * math.pi; r = s * 0.5
        px = cx + math.cos(a) * r * 0.95; py = cy - s * 0.55 + math.sin(a) * r * 0.45
        rr = s * random.uniform(0.17, 0.23) - 6
        ctx.arc(px, py, rr, 0, 6.2832); ctx.set_source_rgb(1, 0.97, 0.85); ctx.fill()
        ctx.arc(px + rr * 0.3, py + rr * 0.3, rr * 0.4, 0, 6.2832); ctx.set_source_rgb(1, 0.85, 0.4); ctx.fill()
    # bucket
    top, bot = cy - s * 0.55, cy + s * 0.75
    tw, bw = s * 0.62, s * 0.46
    ctx.move_to(cx - tw, top); ctx.line_to(cx + tw, top); ctx.line_to(cx + bw, bot); ctx.line_to(cx - bw, bot); ctx.close_path()
    ctx.save(); ctx.clip_preserve(); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    for k in range(-3, 4, 2):
        ctx.move_to(cx + k * tw / 4 - tw / 8, top); ctx.line_to(cx + k * tw / 4 + tw / 8, top)
        ctx.line_to(cx + k * bw / 4 + bw / 8, bot); ctx.line_to(cx + k * bw / 4 - bw / 8, bot); ctx.close_path()
    ctx.set_source_rgb(*RED); ctx.fill(); ctx.restore()
    ctx.move_to(cx - tw, top); ctx.line_to(cx + tw, top); ctx.line_to(cx + bw, bot); ctx.line_to(cx - bw, bot); ctx.close_path()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.05); ctx.stroke()
    # face plate
    rrect(ctx, cx - s * 0.4, cy - s * 0.25, s * 0.8, s * 0.6, s * 0.15); ctx.set_source_rgb(1, 0.95, 0.85); ctx.fill_preserve()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.035); ctx.stroke()
    bl = blink and (t % 3.2) < 0.12
    for ex in (-1, 1):
        x = cx + ex * s * 0.17; y = cy - s * 0.05
        if bl:
            ctx.move_to(x - s * 0.08, y); ctx.line_to(x + s * 0.08, y); ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
        else:
            ctx.arc(x, y, s * 0.1, 0, 6.2832); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(5); ctx.stroke()
            ctx.arc(x + s * 0.02, y + s * 0.01, s * 0.05, 0, 6.2832); ctx.fill()
    ctx.arc(cx, cy + s * 0.13, s * 0.12, 0.15, math.pi - 0.15); ctx.set_source_rgb(*BLACK); ctx.set_line_width(6); ctx.stroke()
    # arms
    for ex in (-1, 1):
        up = point and ex == 1
        ax, ay = cx + ex * s * 0.55, cy + s * 0.2
        hx, hy = (cx + ex * s * 0.95, cy - s * 0.45) if up else (cx + ex * s * 0.85, cy + s * 0.45)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(ax, ay); ctx.line_to(hx, hy); ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.11); ctx.stroke()
        ctx.move_to(ax, ay); ctx.line_to(hx, hy); ctx.set_source_rgb(1, 0.95, 0.85); ctx.set_line_width(s * 0.06); ctx.stroke()
        ctx.arc(hx, hy, s * 0.08, 0, 6.2832); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(5); ctx.stroke()


# ---------------- más arte genérico ----------------
def _stroke_fill(ctx, fill, lw=6):
    ctx.set_source_rgb(*fill); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(lw); ctx.stroke()

def art_mascara(ctx, cx, cy, s, t, col=RED):
    ctx.move_to(cx - s * 0.95, cy - s * 0.1)
    ctx.curve_to(cx - s * 0.7, cy - s * 0.5, cx - s * 0.2, cy - s * 0.4, cx, cy - s * 0.2)
    ctx.curve_to(cx + s * 0.2, cy - s * 0.4, cx + s * 0.7, cy - s * 0.5, cx + s * 0.95, cy - s * 0.1)
    ctx.curve_to(cx + s * 0.8, cy + s * 0.35, cx + s * 0.25, cy + s * 0.35, cx, cy + s * 0.12)
    ctx.curve_to(cx - s * 0.25, cy + s * 0.35, cx - s * 0.8, cy + s * 0.35, cx - s * 0.95, cy - s * 0.1)
    ctx.close_path(); _stroke_fill(ctx, col, s * 0.05)
    for ex in (-1, 1):
        ctx.save(); ctx.translate(cx + ex * s * 0.42, cy - s * 0.03); ctx.scale(s * 0.22, s * 0.12)
        ctx.arc(0, 0, 1, 0, 6.2832); ctx.restore(); _stroke_fill(ctx, (1, 1, 1), 5)

def art_martillo(ctx, cx, cy, s, t, col=None):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-0.5 + 0.08 * math.sin(t * 3))
    rrect(ctx, -s * 0.08, -s * 0.2, s * 0.16, s * 1.1, s * 0.05); _stroke_fill(ctx, (0.55, 0.35, 0.2), s * 0.04)
    rrect(ctx, -s * 0.55, -s * 0.55, s * 1.1, s * 0.45, s * 0.06); _stroke_fill(ctx, (0.7, 0.72, 0.78), s * 0.05)
    ctx.rectangle(-s * 0.55, -s * 0.38, s * 1.1, s * 0.1); ctx.set_source_rgba(1, 1, 1, 0.35); ctx.fill()
    ctx.restore()

def art_rayo(ctx, cx, cy, s, t, col=YEL):
    k = 1 + 0.05 * math.sin(t * 12)
    pts = [(0.15, -1), (-0.45, 0.1), (-0.05, 0.1), (-0.25, 1), (0.45, -0.15), (0.05, -0.15), (0.3, -1)]
    poly(ctx, [(cx + x * s * k, cy + y * s * k) for x, y in pts]); _stroke_fill(ctx, col, s * 0.05)

def art_escudo(ctx, cx, cy, s, t, col=hexc("#2F80ED")):
    ctx.move_to(cx, cy - s); ctx.curve_to(cx + s * 0.5, cy - s * 0.8, cx + s * 0.8, cy - s * 0.85, cx + s * 0.85, cy - s * 0.75)
    ctx.curve_to(cx + s * 0.9, cy, cx + s * 0.5, cy + s * 0.7, cx, cy + s); ctx.curve_to(cx - s * 0.5, cy + s * 0.7, cx - s * 0.9, cy, cx - s * 0.85, cy - s * 0.75)
    ctx.curve_to(cx - s * 0.8, cy - s * 0.85, cx - s * 0.5, cy - s * 0.8, cx, cy - s); ctx.close_path()
    _stroke_fill(ctx, col, s * 0.06)
    art_rayo(ctx, cx, cy, s * 0.5, t, YEL)

def art_trofeo(ctx, cx, cy, s, t, col=GOLD):
    ctx.move_to(cx - s * 0.6, cy - s * 0.8); ctx.line_to(cx + s * 0.6, cy - s * 0.8); ctx.curve_to(cx + s * 0.6, cy + s * 0.1, cx + s * 0.2, cy + s * 0.25, cx, cy + s * 0.3)
    ctx.curve_to(cx - s * 0.2, cy + s * 0.25, cx - s * 0.6, cy + s * 0.1, cx - s * 0.6, cy - s * 0.8); ctx.close_path(); _stroke_fill(ctx, col, s * 0.05)
    for ex in (-1, 1):
        ctx.new_sub_path(); ctx.arc(cx + ex * s * 0.62, cy - s * 0.45, s * 0.22, -math.pi / 2, math.pi / 2) if ex > 0 else ctx.arc_negative(cx - s * 0.62, cy - s * 0.45, s * 0.22, -math.pi / 2, math.pi / 2)
        ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.1); ctx.stroke_preserve(); ctx.set_source_rgb(*col); ctx.set_line_width(s * 0.05); ctx.stroke()
    ctx.rectangle(cx - s * 0.1, cy + s * 0.3, s * 0.2, s * 0.3); _stroke_fill(ctx, col, s * 0.04)
    rrect(ctx, cx - s * 0.45, cy + s * 0.6, s * 0.9, s * 0.25, s * 0.05); _stroke_fill(ctx, dark(col, 0.3), s * 0.04)
    text(ctx, "1", cx, cy - s * 0.3, s * 0.6, WHITE, stroke=8)

def art_claqueta(ctx, cx, cy, s, t, col=None):
    rrect(ctx, cx - s * 0.8, cy - s * 0.3, s * 1.6, s * 1.0, s * 0.06); _stroke_fill(ctx, (0.15, 0.15, 0.18), s * 0.05)
    ang = -0.25 - 0.2 * max(0, math.sin(t * 5))
    ctx.save(); ctx.translate(cx - s * 0.8, cy - s * 0.3); ctx.rotate(ang)
    ctx.rectangle(0, -s * 0.3, s * 1.6, s * 0.3); _stroke_fill(ctx, (0.15, 0.15, 0.18), s * 0.05)
    for k in range(5):
        x = k * s * 0.34
        poly(ctx, [(x, -s * 0.3), (x + s * 0.17, -s * 0.3), (x + s * 0.32, 0), (x + s * 0.15, 0)]); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.restore()
    for k in range(3):
        ctx.move_to(cx - s * 0.6, cy + s * (0.0 + k * 0.22)); ctx.line_to(cx + s * 0.6, cy + s * (0.0 + k * 0.22))
    ctx.set_source_rgba(1, 1, 1, 0.6); ctx.set_line_width(5); ctx.stroke()

def art_portal(ctx, cx, cy, s, t, col=hexc("#FF9F1C")):
    for k in range(3):
        ctx.save(); ctx.translate(cx, cy); ctx.rotate(t * (2 + k) * (1 if k % 2 else -1))
        ctx.set_dash([s * 0.18, s * 0.1]); ctx.arc(0, 0, s * (0.95 - k * 0.2), 0, 6.2832)
        ctx.set_source_rgba(*col, 0.9 - k * 0.2); ctx.set_line_width(s * 0.07); ctx.stroke(); ctx.set_dash([]); ctx.restore()
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, s * 0.5); g.add_color_stop_rgba(0, 1, 1, 1, 0.8); g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g); ctx.arc(cx, cy, s * 0.5, 0, 6.2832); ctx.fill()

def art_planeta(ctx, cx, cy, s, t, col=hexc("#9B51E0")):
    ctx.arc(cx, cy, s * 0.6, 0, 6.2832); _stroke_fill(ctx, col, s * 0.05)
    ctx.save(); ctx.arc(cx, cy, s * 0.6, 0, 6.2832); ctx.clip()
    for k in range(3):
        ctx.rectangle(cx - s, cy - s * 0.4 + k * s * 0.3, s * 2, s * 0.1)
    ctx.set_source_rgba(1, 1, 1, 0.25); ctx.fill(); ctx.restore()
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(-0.35); ctx.scale(s * 1.0, s * 0.25)
    ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(*BLACK); ctx.set_line_width(s * 0.12); ctx.stroke_preserve(); ctx.set_source_rgb(*YEL); ctx.set_line_width(s * 0.06); ctx.stroke()

def art_calavera(ctx, cx, cy, s, t, col=(0.95, 0.95, 0.9)):
    ctx.arc(cx, cy - s * 0.15, s * 0.6, 0, 6.2832); _stroke_fill(ctx, col, s * 0.05)
    rrect(ctx, cx - s * 0.35, cy + s * 0.25, s * 0.7, s * 0.4, s * 0.1); _stroke_fill(ctx, col, s * 0.05)
    for ex in (-1, 1):
        ctx.arc(cx + ex * s * 0.24, cy - s * 0.15, s * 0.16, 0, 6.2832); ctx.set_source_rgb(*BLACK); ctx.fill()
    poly(ctx, [(cx, cy + s * 0.02), (cx - s * 0.07, cy + s * 0.15), (cx + s * 0.07, cy + s * 0.15)]); ctx.fill()
    for k in range(-1, 2):
        ctx.move_to(cx + k * s * 0.13, cy + s * 0.32); ctx.line_to(cx + k * s * 0.13, cy + s * 0.6)
    ctx.set_line_width(5); ctx.stroke()

def art_corona(ctx, cx, cy, s, t, col=GOLD):
    pts = [(-0.8, 0.4), (-0.8, -0.4), (-0.4, 0.0), (0, -0.6), (0.4, 0.0), (0.8, -0.4), (0.8, 0.4)]
    poly(ctx, [(cx + x * s, cy + y * s) for x, y in pts]); _stroke_fill(ctx, col, s * 0.05)
    for x, y, c in [(-0.8, -0.45, RED), (0, -0.65, hexc("#2F80ED")), (0.8, -0.45, GREEN)]:
        ctx.arc(cx + x * s, cy + y * s, s * 0.1, 0, 6.2832); _stroke_fill(ctx, c, 4)

def art_dinero(ctx, cx, cy, s, t, col=hexc("#2E9E5B")):
    for k in range(3):
        ctx.save(); ctx.translate(cx + (k - 1) * s * 0.15, cy + (1 - k) * s * 0.12); ctx.rotate((k - 1) * 0.15 + 0.05 * math.sin(t * 3 + k))
        rrect(ctx, -s * 0.8, -s * 0.4, s * 1.6, s * 0.8, s * 0.06); _stroke_fill(ctx, col, s * 0.04)
        ctx.arc(0, 0, s * 0.25, 0, 6.2832); _stroke_fill(ctx, light(col, 0.4), 4)
        text(ctx, "$", 0, s * 0.02, s * 0.4, BLACK, stroke=0)
        ctx.restore()

def art_fuego(ctx, cx, cy, s, t, col=hexc("#F2862E")):
    icon(ctx, "flame", cx, cy, s * 0.62, col, t)

def art_ojo(ctx, cx, cy, s, t, col=GREEN):
    ctx.move_to(cx - s, cy); ctx.curve_to(cx - s * 0.5, cy - s * 0.6, cx + s * 0.5, cy - s * 0.6, cx + s, cy)
    ctx.curve_to(cx + s * 0.5, cy + s * 0.6, cx - s * 0.5, cy + s * 0.6, cx - s, cy); ctx.close_path(); _stroke_fill(ctx, (1, 1, 1), s * 0.05)
    ctx.arc(cx + s * 0.1 * math.sin(t * 2), cy, s * 0.3, 0, 6.2832); _stroke_fill(ctx, col, 5)
    ctx.arc(cx + s * 0.1 * math.sin(t * 2), cy, s * 0.13, 0, 6.2832); ctx.set_source_rgb(*BLACK); ctx.fill()

def art_espada(ctx, cx, cy, s, t, col=(0.8, 0.82, 0.88)):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(0.6)
    poly(ctx, [(-s * 0.09, -s * 0.4), (s * 0.09, -s * 0.4), (s * 0.09, s * 0.75), (0, s * 0.95), (-s * 0.09, s * 0.75)]); _stroke_fill(ctx, col, s * 0.04)
    rrect(ctx, -s * 0.35, -s * 0.5, s * 0.7, s * 0.12, s * 0.04); _stroke_fill(ctx, GOLD, s * 0.04)
    rrect(ctx, -s * 0.07, -s * 0.95, s * 0.14, s * 0.45, s * 0.04); _stroke_fill(ctx, (0.45, 0.25, 0.15), s * 0.04)
    ctx.restore()

def art_casco(ctx, cx, cy, s, t, col=(0.55, 0.58, 0.66)):
    ctx.move_to(cx - s * 0.7, cy + s * 0.6); ctx.curve_to(cx - s * 0.8, cy - s * 0.9, cx + s * 0.8, cy - s * 0.9, cx + s * 0.7, cy + s * 0.6); ctx.close_path()
    _stroke_fill(ctx, col, s * 0.05)
    rrect(ctx, cx - s * 0.55, cy - s * 0.15, s * 1.1, s * 0.25, s * 0.1); _stroke_fill(ctx, hexc("#38E0E0"), s * 0.04)
    ctx.rectangle(cx - s * 0.5, cy - s * 0.1, s * 0.4, s * 0.06); ctx.set_source_rgba(1, 1, 1, 0.6); ctx.fill()

def art_estrella(ctx, cx, cy, s, t, col=YEL):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5 + t * 0.5; r = s * (0.9 if k % 2 == 0 else 0.4)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    poly(ctx, pts); _stroke_fill(ctx, col, s * 0.05)

def art_nave(ctx, cx, cy, s, t, col=(0.85, 0.87, 0.92)):
    cy += math.sin(t * 3) * s * 0.05
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s * 0.3); ctx.arc(0, 0.2, 1, 0, 6.2832); ctx.restore(); _stroke_fill(ctx, col, s * 0.05)
    ctx.save(); ctx.translate(cx, cy - s * 0.05); ctx.scale(s * 0.45, s * 0.35); ctx.arc(0, 0, 1, math.pi, 2 * math.pi); ctx.restore(); _stroke_fill(ctx, hexc("#38E0E0"), s * 0.04)
    for k in range(-2, 3):
        ctx.arc(cx + k * s * 0.35, cy + s * 0.08, s * 0.06, 0, 6.2832); ctx.set_source_rgb(*YEL); ctx.fill()

def art_libro(ctx, cx, cy, s, t, col=hexc("#8A1F2B")):
    rrect(ctx, cx - s * 0.6, cy - s * 0.8, s * 1.2, s * 1.6, s * 0.06); _stroke_fill(ctx, col, s * 0.05)
    rrect(ctx, cx - s * 0.45, cy - s * 0.6, s * 0.9, s * 0.4, s * 0.04); _stroke_fill(ctx, GOLD, 4)
    text(ctx, "?", cx, cy + s * 0.25, s * 0.7, GOLD, stroke=8)

def art_numero(ctx, cx, cy, s, t, col=GOLD, valor="1"):
    text(ctx, str(valor), cx, cy, s * 1.6, col, stroke=14)

def art_interrogacion(ctx, cx, cy, s, t, col=GREEN):
    glow_text(ctx, "?", cx, cy, s * 1.8, col, col, font="Bangers")

ARTE = {
    "robot": art_robot, "ciudad": art_city, "telarana": art_web, "gemas": art_gems, "reloj_arena": art_hourglass,
    "mascara": art_mascara, "martillo": art_martillo, "rayo": art_rayo, "escudo": art_escudo, "trofeo": art_trofeo,
    "claqueta": art_claqueta, "portal": art_portal, "planeta": art_planeta, "calavera": art_calavera, "corona": art_corona,
    "dinero": art_dinero, "fuego": art_fuego, "ojo": art_ojo, "espada": art_espada, "casco": art_casco,
    "estrella": art_estrella, "nave": art_nave, "libro": art_libro, "interrogacion": art_interrogacion,
}

def dibujar_arte(ctx, nombre, cx, cy, s, t):
    if isinstance(nombre, str) and nombre.startswith("cine_") and dibujar_recurso(ctx, nombre, cx, cy, s, t): return
    if nombre == "palomito":
        mascot(ctx, cx, cy + s * 0.1, s * 0.85, t); return
    f = ARTE.get(nombre) or ARTE["estrella"]
    f(ctx, cx, cy, s, t)

def medallon(ctx, cx, cy, r, arte, etiqueta, col, t, pop=1.0):
    if pop <= 0: return
    r *= pop
    ctx.arc(cx, cy, r + 10, 0, 6.2832); ctx.set_source_rgb(*BLACK); ctx.fill()
    ctx.arc(cx, cy, r, 0, 6.2832); ctx.set_source_rgb(*GOLD); ctx.fill()
    ctx.arc(cx, cy, r * 0.86, 0, 6.2832)
    g = cairo.RadialGradient(cx, cy - r * 0.3, 0, cx, cy, r); g.add_color_stop_rgb(0, *light(col, 0.15)); g.add_color_stop_rgb(1, *dark(col, 0.6))
    ctx.set_source(g); ctx.fill()
    ctx.save(); ctx.arc(cx, cy, r * 0.86, 0, 6.2832); ctx.clip()
    if isinstance(arte, str) and arte.startswith("pj:"):
        dibujar_personaje(ctx, arte[3:], cx, cy + r * 0.12, r * 1.75, "busto", t=t)
    else:
        dibujar_arte(ctx, arte, cx, cy, r * 0.5, t)
    ctx.restore()
    if etiqueta and pop > 0.6:
        pill(ctx, etiqueta, cx, cy + r + 18, max(34, r * 0.3), col, fg=WHITE, padx=14, maxw=r * 2.3)


# ---------------- personajes ilustrados (PNG en /personajes) ----------------
_RAIZ_PJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "personajes"))
_CACHE_PJ = {}

def ruta_personaje(nombre, version="busto"):
    for v in (version, "cuerpo" if version == "busto" else "busto"):
        r = os.path.join(_RAIZ_PJ, f"{nombre}-{v}.png")
        if os.path.exists(r): return r
    return None

def personajes_disponibles():
    if not os.path.isdir(_RAIZ_PJ): return []
    return sorted({f.rsplit("-", 1)[0] for f in os.listdir(_RAIZ_PJ) if f.endswith((".png",)) and "-" in f})

def dibujar_personaje(ctx, nombre, cx, cy, alto, version="busto", fallback="estrella", t=0):
    """Dibuja el PNG del personaje centrado en (cx, cy) con altura `alto`. Si no existe, usa arte original."""
    r = ruta_personaje(nombre, version)
    if not r:
        dibujar_arte(ctx, fallback, cx, cy, alto * 0.42, t); return False
    if r not in _CACHE_PJ: _CACHE_PJ[r] = cairo.ImageSurface.create_from_png(r)
    img = _CACHE_PJ[r]; w, h = img.get_width(), img.get_height()
    esc = alto / h
    ctx.save(); ctx.translate(cx - w * esc / 2, cy - h * esc / 2); ctx.scale(esc, esc)
    ctx.set_source_surface(img, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint(); ctx.restore()
    return True

# ---------------- fondo estilo cómic (rayos + semitono), original ----------------
import colorsys
_CACHE_COMIC = {}

def vivo(col):
    h, sat, v = colorsys.rgb_to_hsv(*col)
    if sat < 0.15: return colorsys.hsv_to_rgb(0.62, 0.35, 0.55)   # grises -> azul pizarra
    return colorsys.hsv_to_rgb(h, max(sat, 0.85), 0.86)

def _capas_comic(col):
    key = tuple(round(x, 3) for x in col)
    if key in _CACHE_COMIC: return _CACHE_COMIC[key]
    cx, cy = CX, 860
    base = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(base)
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, 1350)
    g.add_color_stop_rgb(0, *light(col, 0.22)); g.add_color_stop_rgb(0.5, *col); g.add_color_stop_rgb(1, *dark(col, 0.35))
    c.set_source(g); c.paint()
    top = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(top)
    paso = 24; dmax = math.hypot(W, H) / 1.6
    c.set_source_rgba(*dark(col, 0.3), 0.5)
    for y in range(0, H + paso, paso):
        off = (paso / 2) if (y // paso) % 2 else 0
        for x in range(-paso, W + paso, paso):
            xx = x + off; d = math.hypot(xx - cx, y - cy) / dmax
            r = paso * 0.5 * max(0, min(1, (d - 0.15) * 1.3))
            if r > 0.6: c.new_sub_path(); c.arc(xx, y, r, 0, 6.2832)
    c.fill()
    gg = cairo.RadialGradient(cx, cy, 0, cx, cy, 360)
    gg.add_color_stop_rgba(0, *light(col, 0.6), 0.6); gg.add_color_stop_rgba(1, *light(col, 0.6), 0)
    c.set_source(gg); c.paint()
    v = cairo.RadialGradient(cx, cy, 750, cx, cy, 1550)
    v.add_color_stop_rgba(0, 0, 0, 0, 0); v.add_color_stop_rgba(1, 0, 0, 0, 0.5)
    c.set_source(v); c.paint()
    _CACHE_COMIC[key] = (base, top); return base, top

def background_comic(ctx, col, t, cy=860, cx=CX):
    col = vivo(col); base, top = _capas_comic(col)
    ctx.set_source_surface(base, 0, 0); ctx.paint()
    random.seed(5); n = 44; ang0 = t * 0.08
    for i in range(n):
        a = ang0 + i * 2 * math.pi / n + random.uniform(-0.03, 0.03)
        w = random.uniform(0.012, 0.06)
        ctx.move_to(cx, cy); ctx.line_to(cx + math.cos(a - w) * 2600, cy + math.sin(a - w) * 2600)
        ctx.line_to(cx + math.cos(a + w) * 2600, cy + math.sin(a + w) * 2600); ctx.close_path()
        ctx.set_source_rgba(*light(col, 0.4), random.uniform(0.2, 0.42)); ctx.fill()
    ctx.set_source_surface(top, 0, 0); ctx.paint()

# ---------------- globos de diálogo y explosiones de cómic (originales) ----------------
def explosion(ctx, cx, cy, r, col=YEL, puntas=14, t=0, semilla=3, borde=10):
    rnd = random.Random(semilla); pts = []
    for i in range(puntas * 2):
        a = i * math.pi / puntas + t * 0.4
        rr = r * (1.0 if i % 2 == 0 else rnd.uniform(0.55, 0.7)) * (1 + 0.03 * math.sin(t * 8 + i))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.82))
    poly(ctx, pts); ctx.set_source_rgb(*col); ctx.fill_preserve()
    ctx.set_line_join(cairo.LINE_JOIN_MITER); ctx.set_source_rgb(*BLACK); ctx.set_line_width(borde); ctx.stroke()

def _nube(ctx, cx, cy, w, h, bultos=9):
    for i in range(bultos):
        a = i * 2 * math.pi / bultos
        ctx.new_sub_path(); ctx.arc(cx + math.cos(a) * w * 0.38, cy + math.sin(a) * h * 0.32, min(w, h) * 0.3, 0, 6.2832)
    ctx.new_sub_path(); ctx.save(); ctx.translate(cx, cy); ctx.scale(w * 0.42, h * 0.38); ctx.arc(0, 0, 1, 0, 6.2832); ctx.restore()

def globo(ctx, texto, cx, cy, w, h, cola=(-1, 1), tipo="ovalo", sombra=hexc("#3FB4F0"), pop=1.0):
    """Globo de diálogo blanco con contorno negro; cola apunta en dirección (dx, dy)."""
    if pop <= 0: return
    ctx.save(); ctx.translate(cx, cy); ctx.scale(pop, pop); ctx.translate(-cx, -cy)
    tx, ty = cx + cola[0] * w * 0.32, cy + cola[1] * h * 0.62
    def forma(dx=0, dy=0):
        ctx.new_path()
        if tipo == "nube": _nube(ctx, cx + dx, cy + dy, w, h)
        else:
            ctx.save(); ctx.translate(cx + dx, cy + dy); ctx.scale(w / 2, h / 2); ctx.arc(0, 0, 1, 0, 6.2832); ctx.restore()
        ctx.move_to(cx + dx - w * 0.12, cy + dy + h * 0.3); ctx.line_to(tx + dx, ty + dy); ctx.line_to(cx + dx + w * 0.08, cy + dy + h * 0.36); ctx.close_path()
    if sombra:
        forma(-18, 14); ctx.set_source_rgb(*sombra); ctx.fill_preserve(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(9); ctx.stroke()
    forma(); ctx.set_source_rgb(*BLACK); ctx.set_line_width(18); ctx.stroke_preserve(); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    # texto (máx. 2 líneas)
    pal = texto.upper().split(); lineas = [texto.upper()]
    if len(texto) > 14 and len(pal) > 1:
        mitad = len(texto) / 2; acc = 0; cut = 1
        for i, p in enumerate(pal):
            acc += len(p) + 1
            if acc >= mitad: cut = i + 1; break
        lineas = [" ".join(pal[:cut]), " ".join(pal[cut:])]
    size = h * (0.3 if len(lineas) == 2 else 0.38)
    for i, l in enumerate(lineas):
        y = cy + (i - (len(lineas) - 1) / 2) * size * 1.05
        text(ctx, l, cx, y, size, BLACK, stroke=0, maxw=w * 0.78)
    ctx.restore()


# ---------------- fondos e insertos de Vecteezy (licencia gratuita con atribución) ----------------
_RAIZ_REC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recursos")
_CACHE_IMG = {}
FONDOS_IMG = {"fondo_comic_1": 0.08, "fondo_comic_2": 0.0, "fondo_comic_3": 0.45, "fondo_comic_4": 0.68,
              "fondo_rayos_1": 0.6, "fondo_rayos_2": 0.14, "fondo_rayos_3": 0.94}

def imagen_cairo(nombre):
    if nombre in _CACHE_IMG: return _CACHE_IMG[nombre]
    from PIL import Image
    ruta = next((os.path.join(_RAIZ_REC, nombre + ext) for ext in (".png", ".jpg") if os.path.exists(os.path.join(_RAIZ_REC, nombre + ext))), None)
    if not ruta: _CACHE_IMG[nombre] = None; return None
    im = Image.open(ruta).convert("RGBA")
    import numpy as np
    a = np.asarray(im).copy(); a = a[..., [2, 1, 0, 3]]
    al = a[..., 3:4].astype(np.float32) / 255.0; a[..., :3] = (a[..., :3] * al).astype(np.uint8)   # premultiplicado
    buf = bytearray(np.ascontiguousarray(a).tobytes())
    surf = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, im.width, im.height, im.width * 4)
    _CACHE_IMG[nombre] = (surf, buf); return _CACHE_IMG[nombre]

def fondo_por_color(col):
    h, sat, v = colorsys.rgb_to_hsv(*col)
    if sat < 0.15: return "fondo_comic_4"
    return min(FONDOS_IMG, key=lambda k: min(abs(FONDOS_IMG[k] - h), 1 - abs(FONDOS_IMG[k] - h)))

def background_imagen(ctx, nombre, lt, dur):
    r = imagen_cairo(nombre)
    if not r: return False
    surf = r[0]; z = 1.02 + 0.06 * min(1, lt / max(dur, 0.1))
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.rotate(0.01 * math.sin(lt * 0.7)); ctx.translate(-W / 2, -H / 2)
    ctx.set_source_surface(surf, 0, 0); ctx.paint(); ctx.restore()
    v = cairo.RadialGradient(CX, 860, 650, CX, 860, 1500)
    v.add_color_stop_rgba(0, 0, 0, 0, 0); v.add_color_stop_rgba(1, 0, 0, 0, 0.5)
    ctx.set_source(v); ctx.paint()
    return True

def lineas_velocidad(ctx, alpha):
    r = imagen_cairo("lineas_velocidad")
    if not r or alpha <= 0: return
    ctx.save(); ctx.set_source_surface(r[0], 0, 0); ctx.paint_with_alpha(alpha); ctx.restore()


# ---------------- elementos de cine (Vecteezy, licencia gratuita con atribución) ----------------
RECURSOS_ARTE = ["cine_palomitas", "cine_lentes3d", "cine_boleto", "cine_rollo", "cine_claqueta", "cine_vaso"]

def dibujar_recurso(ctx, nombre, cx, cy, s, t=0):
    """Dibuja un PNG de /recursos con contorno negro grueso (para igualar el estilo del canal)."""
    r = imagen_cairo(nombre)
    if not r: return False
    img = r[0]; w, h = img.get_width(), img.get_height()
    esc = (s * 2.1) / max(w, h)
    bob = math.sin(t * 2.5) * s * 0.03
    ctx.save(); ctx.translate(cx - w * esc / 2, cy - h * esc / 2 + bob); ctx.scale(esc, esc)
    grosor = 9 / esc
    ctx.set_source_rgb(*BLACK)
    for k in range(12):
        a = k * math.pi / 6
        ctx.mask_surface(img, math.cos(a) * grosor, math.sin(a) * grosor)
    ctx.set_source_surface(img, 0, 0); ctx.paint()
    ctx.restore(); return True
