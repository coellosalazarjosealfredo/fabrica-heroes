# Fábrica de Shorts de superhéroes

Cada día, sin intervención:

1. **~02:00 (Ecuador)** — Claude busca tendencias de Marvel/DC/cine de superhéroes y deja los guiones del día
   en `data/guiones/pendientes/` (formato en `GUIONES.md`).
2. **03:00** — GitHub Actions produce los videos (voz R, arte original, subtítulos karaoke, efectos).
3. Los publica en **GitHub Pages** (enlace público que Buffer necesita) y los **programa en Buffer**
   para YouTube Shorts y TikTok en los horarios de `HORARIOS`.

## Configuración (una sola vez)

1. **Buffer:** conecta el YouTube y el TikTok del canal. Genera tu clave en
   https://publish.buffer.com/settings/api (o *Settings → API*).
2. **Secreto en GitHub:** *Settings → Secrets and variables → Actions → New repository secret*
   - `BUFFER_API_KEY` = tu clave de Buffer.
3. **GitHub Pages:** *Settings → Pages → Build and deployment → Source:* **GitHub Actions**.
4. **IDs de los canales:** *Actions → Producción diaria → Run workflow → modo* `canales`. Copia los ID y
   créalos como *variables* (pestaña *Variables*): `YOUTUBE_CHANNEL_ID`, `TIKTOK_CHANNEL_ID`.
5. **Prueba:** *Run workflow → modo* `solo_render`, cantidad 1 → descarga el video en *Artifacts*.

## Variables opcionales

| Variable | Por defecto |
|---|---|
| `CANTIDAD` | 8 videos por día |
| `HORARIOS` | `07:00,09:00,11:00,13:00,15:00,17:00,19:00,21:00` |
| `ZONA_HORARIA` | `America/Guayaquil` |
| `VISIBILIDAD` | `public` (YouTube) |

## Probar en tu PC

```bash
pip install -r fabrica/requirements.txt   # Python 3.11, ffmpeg y libcairo instalados
python fabrica/motor.py data/guiones/pendientes/<guion>.json salida/
```

Licencias: fuentes Bangers y Anton (SIL OFL), voz de referencia CC BY-SA 4.0 (ver `fabrica/voz_ref/ATRIBUCION.md`),
modelo de voz Chatterbox (MIT). Todo el arte es original de este repositorio.
