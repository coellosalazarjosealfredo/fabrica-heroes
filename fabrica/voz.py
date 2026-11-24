"""Voz R: Chatterbox multilingüe (licencia MIT) clonando una voz de referencia con licencia abierta.

Cada frase se genera con varias semillas y se verifica con Whisper; se queda la que mejor coincide con el texto.
"""
import os, re, difflib, unicodedata
import numpy as np, soundfile as sf

RAIZ = os.path.dirname(os.path.abspath(__file__))
REF = os.environ.get("VOZ_REF", os.path.join(RAIZ, "voz_ref", "voz_r.wav"))
SEMILLAS = [7, 1, 23, 42, 99, 5]
_tts = None; _wm = None

def _cargar():
    global _tts, _wm
    if _tts is None:
        import perth
        if getattr(perth, "PerthImplicitWatermarker", None) is None:
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        _tts = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel(os.environ.get("WHISPER_MODELO", "small"), device="cpu", compute_type="int8")
    return _tts, _wm

def _num_a_palabras(s):
    try:
        from num2words import num2words
    except ImportError:
        return s
    def rep(m):
        n = m.group(0).replace(".", "").replace(",", "")
        try: return " " + num2words(int(n), lang="es") + " "
        except Exception: return m.group(0)
    return re.sub(r"\d[\d.,]*\d|\d", rep, s)

def normalizar(s):
    s = _num_a_palabras(s.lower())
    s = unicodedata.normalize("NFD", s); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("-", " ")
    return re.sub(r"[^a-z ]", " ", s).split()

def similitud(a, b):
    return difflib.SequenceMatcher(None, " ".join(normalizar(a)), " ".join(normalizar(b))).ratio()

def generar(decir, verificar, salida, log=print, umbral=0.93, exageracion=0.55):
    """Genera la frase `decir` (puede llevar ortografía fonética) y la compara con `verificar` (texto real)."""
    import torch
    tts, wm = _cargar()
    mejor = None
    for semilla in SEMILLAS:
        torch.manual_seed(semilla)
        w = tts.generate(decir, language_id="es", audio_prompt_path=REF, exaggeration=exageracion, cfg_weight=0.5)
        a = w.squeeze().numpy(); sr = tts.sr
        idx = np.where(np.abs(a) > 0.02)[0]
        if len(idx) == 0: continue
        a = a[max(0, idx[0] - int(sr * 0.02)):]
        sf.write(salida, a, sr)
        segs, _ = wm.transcribe(salida, language="es", word_timestamps=True)
        ws = [x for s in segs for x in s.words]
        oido = " ".join(x.word for x in ws)
        sc = max(similitud(oido, verificar), similitud(oido, decir))
        log(f"    voz semilla {semilla}: {sc:.2f} · «{oido.strip()}»")
        if mejor is None or sc > mejor[0]:
            mejor = (sc, a.copy(), ws[-1].end if ws else None)
        if sc >= umbral: break
    sc, a, fin = mejor
    if fin: a = a[:int(min(len(a) / sr, fin + 0.15) * sr)]
    sf.write(salida, a, sr)
    return {"archivo": salida, "duracion": len(a) / sr, "puntaje": sc, "sr": sr}
