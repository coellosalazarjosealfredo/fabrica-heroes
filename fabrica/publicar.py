"""Producción y programación diaria (GitHub Actions o tu PC).

Pasos (variable PASO):
  producir   toma los siguientes guiones de data/guiones/pendientes, genera los videos en sitio/v/
             y escribe data/manifiesto.json (los videos se publican luego en GitHub Pages).
  programar  lee el manifiesto, comprueba que cada video ya es accesible en GitHub Pages
             y crea los posts programados en Buffer (YouTube Shorts + TikTok).
  canales    lista los canales conectados en Buffer (para copiar sus ID).

Variables de entorno:
  BUFFER_API_KEY        clave personal de la API de Buffer (secreto)
  YOUTUBE_CHANNEL_ID    ID del canal de YouTube en Buffer (si falta y hay uno solo, se detecta)
  TIKTOK_CHANNEL_ID     ID del canal de TikTok en Buffer (igual)
  CANTIDAD              cuántos videos por día (por defecto = nº de horarios)
  HORARIOS              "07:00,09:00,11:00,13:00,15:00,17:00,19:00,21:00"
  ZONA_HORARIA          "America/Guayaquil"
  URL_SITIO             https://<usuario>.github.io/<repo>  (la pone el workflow)
  VISIBILIDAD           public | unlisted | private  (YouTube)
  YOUTUBE_HORARIOS      horarios que también van a YouTube (Buffer gratis: 2 por día). "todos" = todos.
"""
import datetime as dt, json, os, shutil, sys, time, urllib.request, urllib.error
from zoneinfo import ZoneInfo

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(RAIZ, "data")
PEND = os.path.join(DATA, "guiones", "pendientes")
HECHOS = os.path.join(DATA, "guiones", "hechos")
TRABAJO = os.path.join(DATA, "videos")
SITIO = os.path.join(RAIZ, "sitio")
MANIF = os.path.join(DATA, "manifiesto.json")
REGISTRO = os.path.join(DATA, "registro.jsonl")
API = "https://api.buffer.com"

def env(k, d=""): return os.environ.get(k, d).strip()

def resumen(md):
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f: f.write(md + "\n")
    print(md)

# ---------------------------------------------------------------- Buffer
def gql(query, variables=None):
    req = urllib.request.Request(API, method="POST", data=json.dumps({"query": query, "variables": variables or {}}).encode(),
                                 headers={"Authorization": f"Bearer {env('BUFFER_API_KEY')}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: out = json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Buffer HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")
    if out.get("errors"): raise RuntimeError(f"Buffer: {json.dumps(out['errors'], ensure_ascii=False)[:600]}")
    return out["data"]

def canales():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    res = []
    for o in orgs:
        q = "query($i: ChannelsInput!) { channels(input: $i) { id name displayName service isQueuePaused } }"
        for c in gql(q, {"i": {"organizationId": o["id"]}})["channels"]:
            res.append(dict(c, organizacion=o.get("name")))
    return res

def id_canal(servicio, var):
    if env(var): return env(var)
    cs = [c for c in canales() if c["service"] == servicio]
    if len(cs) == 1: return cs[0]["id"]
    if not cs:
        resumen(f"⚠️ No hay ningún canal de {servicio} conectado en Buffer: se omite esa red."); return None
    sys.exit(f"Define la variable {var}: hay {len(cs)} canales de {servicio} en Buffer (ejecuta el paso 'canales').")

def crear_post(canal, texto, url_video, cuando_utc, meta):
    q = """mutation($i: CreatePostInput!) { createPost(input: $i) {
             ... on PostActionSuccess { post { id dueAt } }
             ... on MutationError { message } } }"""
    i = {"channelId": canal, "text": texto, "schedulingType": "automatic", "mode": "customScheduled",
         "dueAt": cuando_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "aiAssisted": True,
         "assets": [{"video": {"url": url_video, "metadata": {"thumbnailOffset": 1200}}}], "metadata": meta}
    r = gql(q, {"i": i})["createPost"]
    if "message" in r and "post" not in r: raise RuntimeError(r["message"])
    return r["post"]

# ---------------------------------------------------------------- pasos
def horarios_hoy(horarios, zona):
    tz = ZoneInfo(zona); ahora = dt.datetime.now(tz); out = []
    for h in horarios:
        hh, mm = map(int, h.split(":"))
        t = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if t <= ahora + dt.timedelta(minutes=20): t += dt.timedelta(days=1)
        out.append(t)
    return sorted(out)

def paso_producir():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import motor
    horarios = [h.strip() for h in env("HORARIOS", "07:00,09:00,11:00,13:00,15:00,17:00,19:00,21:00").split(",") if h.strip()]
    cantidad = int(env("CANTIDAD", str(len(horarios))) or len(horarios))
    for d in (PEND, HECHOS, TRABAJO, os.path.join(SITIO, "v")): os.makedirs(d, exist_ok=True)
    archivos = sorted(f for f in os.listdir(PEND) if f.endswith(".json"))[:cantidad]
    if not archivos:
        resumen("⚠️ No hay guiones pendientes en data/guiones/pendientes"); json.dump([], open(MANIF, "w")); return 0
    manifiesto = []
    for i, nombre in enumerate(archivos):
        g = json.load(open(os.path.join(PEND, nombre), encoding="utf-8"))
        vid = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in str(g.get("id", nombre[:-5])))
        print(f"\n▶ [{i+1}/{len(archivos)}] {nombre}", flush=True)
        try:
            info = motor.producir(g, os.path.join(TRABAJO, vid), log=lambda m: print(m, flush=True))
        except Exception as e:
            print(f"  ❌ falló {nombre}: {e}", flush=True); continue
        sello = dt.datetime.utcnow().strftime("%Y%m%d%H%M")
        destino = f"v/{vid}-{sello}.mp4"
        shutil.copy(info["video"], os.path.join(SITIO, destino))
        manifiesto.append({"guion": nombre, "id": g.get("id"), "ruta_sitio": destino, "duracion": info["duracion"],
                           "publicacion": g.get("publicacion", {})})
        print(f"  ✅ {destino} · {info['duracion']} s · {info['segundos_render']} s de render", flush=True)
    json.dump(manifiesto, open(MANIF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(SITIO, "index.html"), "w") as f: f.write("<!doctype html><title>fabrica-heroes</title><p>Medios de la fábrica.</p>")
    resumen(f"## Producción\n\n{len(manifiesto)} video(s) listos de {len(archivos)} guiones.")
    return 0

def accesible(url, intentos=20):
    for k in range(intentos):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200: return True
        except Exception: pass
        time.sleep(15)
    return False

def paso_programar():
    if not env("BUFFER_API_KEY"): sys.exit("Falta el secreto BUFFER_API_KEY")
    for d in (PEND, HECHOS): os.makedirs(d, exist_ok=True)
    manifiesto = json.load(open(MANIF, encoding="utf-8")) if os.path.exists(MANIF) else []
    if not manifiesto: resumen("Nada que programar."); return 0
    zona = env("ZONA_HORARIA", "America/Guayaquil")
    horarios = [h.strip() for h in env("HORARIOS", "07:00,09:00,11:00,13:00,15:00,17:00,19:00,21:00").split(",") if h.strip()]
    slots = horarios_hoy(horarios, zona)
    yt, tk = id_canal("youtube", "YOUTUBE_CHANNEL_ID"), id_canal("tiktok", "TIKTOK_CHANNEL_ID")
    base = env("URL_SITIO").rstrip("/")
    filas = []
    for i, m in enumerate(manifiesto):
        url = f"{base}/{m['ruta_sitio']}"
        cuando = slots[i % len(slots)] + dt.timedelta(days=i // len(slots))
        utc = cuando.astimezone(dt.timezone.utc)
        pub = m.get("publicacion", {})
        fila = {"guion": m["guion"], "id": m.get("id"), "url": url, "programado": cuando.isoformat(timespec="minutes")}
        if not accesible(url):
            fila["error"] = "el video no está accesible en GitHub Pages"; filas.append(fila); continue
        hhmm = cuando.strftime("%H:%M")
        yt_hor = env("YOUTUBE_HORARIOS", "13:00,21:00")
        if yt and yt_hor != "todos" and hhmm not in [h.strip() for h in yt_hor.split(",")]:
            fila["youtube_error"] = "solo TikTok en este horario (límite diario de YouTube en Buffer)"
        elif yt:
          try:
            p = crear_post(yt, pub.get("descripcion", ""), url, utc,
                           {"youtube": {"title": (pub.get("titulo_youtube") or pub.get("titulo") or "")[:100], "categoryId": "1",
                                        "privacy": env("VISIBILIDAD", "public"), "madeForKids": False, "isAiGenerated": True}})
            fila["youtube_post"] = p["id"]
          except Exception as e: fila["youtube_error"] = str(e)[:300]
        else: fila["youtube_error"] = "sin canal en Buffer"
        if tk:
          try:
            p = crear_post(tk, pub.get("texto_tiktok") or pub.get("descripcion", ""), url, utc, {"tiktok": {"isAiGenerated": True}})
            fila["tiktok_post"] = p["id"]
          except Exception as e: fila["tiktok_error"] = str(e)[:300]
        else: fila["tiktok_error"] = "sin canal en Buffer"
        ok = "youtube_post" in fila or "tiktok_post" in fila
        if ok and os.path.exists(os.path.join(PEND, m["guion"])):
            try: shutil.move(os.path.join(PEND, m["guion"]), os.path.join(HECHOS, m["guion"]))
            except Exception as e: print("  (no pude archivar el guion:", e, ")")
        filas.append(fila)
        with open(REGISTRO, "a", encoding="utf-8") as f: f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    lineas = [f"| {f['guion']} | {f['programado']} | {'✅' if f.get('youtube_post') else '❌ ' + f.get('youtube_error', f.get('error', ''))[:80]} | "
              f"{'✅' if f.get('tiktok_post') else '❌ ' + f.get('tiktok_error', f.get('error', ''))[:80]} |" for f in filas]
    resumen("## Programación en Buffer\n\n| Guion | Hora | YouTube | TikTok |\n|---|---|---|---|\n" + "\n".join(lineas))
    restantes = len([x for x in os.listdir(PEND) if x.endswith(".json")])
    resumen(f"\nGuiones pendientes: **{restantes}**")
    return 0

def paso_canales():
    if not env("BUFFER_API_KEY"): sys.exit("Falta el secreto BUFFER_API_KEY")
    cs = canales()
    resumen("## Canales en Buffer\n\n| Red | Nombre | ID |\n|---|---|---|\n" + "\n".join(f"| {c['service']} | {c.get('displayName') or c['name']} | `{c['id']}` |" for c in cs))
    return 0

if __name__ == "__main__":
    paso = env("PASO", "producir")
    sys.exit({"producir": paso_producir, "programar": paso_programar, "canales": paso_canales}[paso]())
