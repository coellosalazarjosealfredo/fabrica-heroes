# Formato de los guiones

Cada video es un archivo JSON en `data/guiones/pendientes/`. Se producen en orden alfabético,
así que nómbralos con fecha y número: `20261125-01-tema-corto.json`.

## Reglas de contenido

- **Duración:** 22–29 s de voz (unas 55–70 palabras). Más de 29,4 s se acelera automáticamente (máx. ×1,15).
- **Gancho en el primer bloque** (0–3 s): dato, pregunta, lista o misterio. Sin saludos.
- **Cierre en bucle:** la última frase conecta con la primera; el último bloque termina con `{"tipo": "bucle"}`.
- **Prohibido:** pedir que se suscriban, den like, comenten o sigan.
- **Datos verificados** con al menos una fuente fiable (ponla en `fuentes`). Nada de rumores presentados como hechos:
  si es rumor, dilo ("según rumores…").
- **Arte original:** nunca pidas dibujar personajes, trajes, logotipos o emblemas de Marvel/DC. Usa solo el
  catálogo de `arte` de abajo. Los nombres de personajes y películas sí pueden aparecer como texto.
- **Ritmo dinámico:** un bloque cada 2–4 s; cambia de tipo de escena en cada bloque; usa `escenas` (lista)
  para meter 2 escenas en un bloque largo.

## Estrategia de crecimiento (obligatoria)

- **Cuenta regresiva a Avengers: Doomsday** (estreno 18-dic-2026): hasta esa fecha, el guion `NN=01` de cada día es
  "Faltan X días para Doomsday: …" con un dato nuevo y verificado. Primer bloque: escena `titulo` con `numero` = días que faltan
  (contados desde la fecha de publicación) y `serie` = `{"texto": "CUENTA REGRESIVA DOOMSDAY", "total": <días que faltaban el 25-nov>}`.
- **Series en partes:** si un tema da para más, divídelo en "Parte 1" y "Parte 2" (mismo día, horarios seguidos) y termina la parte 1
  con un cierre que invite a ver la siguiente sin pedir follow ("la parte 2 es todavía más loca…").
- **Pregunta para comentar** al final de `descripcion` y `texto_tiktok` (nunca en la voz): "¿Cuál te falta por ver? 👇".
- **Aprende de los números:** si existe `data/estadisticas.json`, repite los formatos y temas con más vistas y abandona los de menos.

## Estructura

```json
{
  "id": "H-20261125-01",
  "publicacion": {
    "titulo_youtube": "Título con gancho (máx. 100) #shorts",
    "descripcion": "Texto para YouTube con hashtags",
    "texto_tiktok": "Texto para TikTok con hashtags",
    "tags": ["marvel", "ucm"]
  },
  "serie": {"texto": "TOP 5 TAQUILLA MARVEL", "total": 5},
  "fuentes": ["https://..."],
  "bloques": [
    {"texto": "Lo que se ve en subtítulos", "decir": "Lo que lee la voz (opcional)", "paso": 1,
     "escena": {"tipo": "titulo", "...": "..."}}
  ]
}
```

- `texto`: lo que aparece en los subtítulos, bien escrito (Endgame, Spider-Man, 2026…).
- `decir` (opcional): cómo debe leerlo la voz. Úsalo para **nombres en inglés escritos como suenan**
  y para **números en letras**: "Éndgueim", "Infíniti Uór", "Spáider Man", "Dédpul", "Dúmsdei",
  "Róbert Dáuni Yúnior", "dos mil veintiséis".
- `serie` + `paso` (opcional): barra de progreso arriba ("TOP 5 … · 3/5").

## Tipos de escena

| tipo | campos |
|---|---|
| `titulo` | `lineas` (1–3; texto o `{"t":"…","c":"cromo/verde/rojo/amarillo/dorado/blanco"}`), `arte`, `numero`, `pie`, `pie_color` |
| `ficha` | `titulo`, `anio`, `arte`, `color`, `check` (true/false), `rango` ("#1"), `cifra` ("US$ 2.799 MILLONES"), `destacar` |
| `dos_fichas` | `titulo`, `fichas` (2 fichas), `pie`, `pie_color` |
| `mosaico` | `lineas`, `fichas` (2–6), `destacar` (índice) |
| `medallones` | `lineas`, `items` (2–8 de `{"arte","texto","color"}`) |
| `cifra` | `valor`, `prefijo`, `sufijo`, `decimales`, `texto`, `arte` |
| `versus` | `titulo`, `a` (ficha), `b` (ficha) |
| `lista` | `titulo`, `items` (2–5 textos cortos) |
| `protagonista` | `personaje`, `lineas`, `cifra` o `etiqueta`, `arte` (respaldo) |
| `bucle` | repite la primera escena (úsalo al final) |

Campos comunes: `fondo` o `color` ("#1F3B8A"), `impacto` (true = sacudida),
`globo` (texto corto de cómic, máx. ~22 caracteres, ej. "¡NO LO SABÍAS!", "¿SERÁ CIERTO?"), `globo_tipo` ("ovalo" o "nube").
Usa `globo` en 1-2 escenas por video como máximo: en el gancho (sobre todo con `palomito`) y en remates o rumores.
Las escenas `cifra` y `versus` ya llevan explosión de cómic automática.

## Personajes ilustrados (carpeta `personajes/`)

Si hay PNG en `personajes/` (`nombre-busto.png`, `nombre-cuerpo.png`), úsalos con `"personaje": "nombre"` en
`ficha` (o `"personajes": ["a","b"]`, máx. 3), en cada item de `medallones`, en `titulo` y en `protagonista`.
Usa SOLO nombres que existan en esa carpeta; pon siempre también un `arte` del catálogo como respaldo.

## Catálogo de `arte` (todo original)

`palomito` (mascota del canal), `robot`, `ciudad`, `telarana`, `gemas`, `reloj_arena`, `mascara`, `martillo`,
`rayo`, `escudo`, `trofeo`, `claqueta`, `portal`, `planeta`, `calavera`, `corona`, `dinero`, `fuego`, `ojo`,
`espada`, `casco`, `estrella`, `nave`, `libro`, `interrogacion`.

Elementos de cine (ideales para taquilla, estrenos, fechas y reseñas): `cine_palomitas`, `cine_lentes3d`, `cine_boleto`,
`cine_rollo`, `cine_claqueta`, `cine_vaso`.

Colores sugeridos: `#1F3B8A` azul · `#8A1F2B` rojo · `#4B1F7A` morado · `#7A5A12` dorado ·
`#14532D` verde · `#3A3F55` gris · `#0E5E6F` turquesa · `#7A2E12` naranja.
