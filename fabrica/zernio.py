"""Cliente mínimo de la API de Zernio (https://zernio.com/api/v1)."""
import json, os, urllib.request, urllib.error

BASE = os.environ.get("ZERNIO_BASE", "https://zernio.com/api/v1")

def _req(metodo, ruta, clave, cuerpo=None):
    req = urllib.request.Request(f"{BASE}{ruta}", method=metodo,
                                 data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
                                 headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Zernio {metodo} {ruta} -> {e.code}: {e.read().decode(errors='replace')[:500]}")

def subir(ruta_archivo, tipo, clave):
    """Sube un archivo con el flujo presign y devuelve la URL pública."""
    pres = _req("POST", "/media/presign", clave, {"filename": os.path.basename(ruta_archivo), "contentType": tipo})
    tam = os.path.getsize(ruta_archivo)
    with open(ruta_archivo, "rb") as f:   # envío en flujo (sirve para archivos de varios GB)
        put = urllib.request.Request(pres["uploadUrl"], method="PUT", data=f,
                                     headers={"Content-Type": tipo, "Content-Length": str(tam)})
        with urllib.request.urlopen(put, timeout=3600) as r: r.read()
    return pres["publicUrl"]

def crear_post(cuerpo, clave):
    return _req("POST", "/posts", clave, cuerpo)

def cuentas(clave):
    return _req("GET", "/accounts", clave)

def post(post_id, clave):
    return _req("GET", f"/posts/{post_id}", clave)
