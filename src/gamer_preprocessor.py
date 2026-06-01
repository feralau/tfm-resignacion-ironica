#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gamer_preprocessor.py — Preprocesador específico para lenguaje gamer
hispanohablante. Módulo 1 del pipeline del TFM (§4.1).

Responsabilidades:
 - Normalización de variantes ortográficas del argot (rito/RITO/Rito Games
   -> rito; xD/xd/xDDD/xddd -> xd; petao/petado/petadisimo -> petado).
 - Conservación deliberada de marcadores irónicos relevantes (xD, :@@@,
   alargamientos enfáticos como "novedaaaad") porque son señal, no ruido.
 - Reducción de reiteraciones extremas (xddddddd -> xddd) sin destruir el
   énfasis.
 - Normalización ligera de mayúsculas grito a marca explícita.
 - Limpieza mínima: URLs -> token, citas de foro -> token, mensajes vacíos.

DECISIÓN DE DISEÑO: el preprocesador es ligero a propósito. Un texto
demasiado «limpio» pierde justo las señales pragmáticas que el TFM busca
detectar (mayúsculas, repeticiones, emoticonos). Lo que se normaliza son
variantes ORTOGRÁFICAS de una misma forma, no rasgos expresivos.

API:
    pre = GamerPreprocessor()
    texto_limpio = pre.transform(texto_crudo)

    # Lote
    textos_limpios = pre.transform_batch([t1, t2, t3])

Para el clasificador, llamar a .transform() antes del tokenizador.
Se publicará como paquete PyPI independiente (§4.7).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

# --------------------------------------------------------------------------- #
# Normalizaciones de variantes ortográficas (núcleo del inventario emic).    #
# Cada regla: regex case-insensitive -> forma canónica.                       #
# --------------------------------------------------------------------------- #

_NORMALIZATIONS: list[tuple[re.Pattern, str]] = [
    # Disfemismo irónico estrella: variantes de "rito"
    (re.compile(r"\brito\s+(games?|gumes|gomez)\b", re.IGNORECASE), "rito"),
    (re.compile(r"\bri+to+\b", re.IGNORECASE), "rito"),
    # gg-cierre, fórmula fija
    (re.compile(r"\bgg\s*wp\s*rito\b", re.IGNORECASE), "gg_wp_rito"),
    (re.compile(r"\bgg\s*rito\b", re.IGNORECASE), "gg_rito"),
    (re.compile(r"\bgg\s*wp\b", re.IGNORECASE), "gg_wp"),
    # Rito pls y variantes (meme-fórmula)
    (re.compile(r"\brito\s*pl[a-z]*\b", re.IGNORECASE), "rito_pls"),
    # Indie company y compañía indie
    (re.compile(r"\b(?:compañ[ií]a|company|juego)\s+indie\b", re.IGNORECASE), "indie_company"),
    (re.compile(r"\bindie\s+company\b", re.IGNORECASE), "indie_company"),
    # Conjuros mágico-técnicos
    (re.compile(r"\bthere\s*is\s*no\s*u?rf?\s*level\b", re.IGNORECASE), "thereisnourflevel"),
    (re.compile(r"\bthereisno[a-z]*\b", re.IGNORECASE), "thereisnourflevel"),
    (re.compile(r"\bkonami\s*code\b", re.IGNORECASE), "konami_code"),
    # Argot técnico con variantes ortográficas frecuentes
    (re.compile(r"\bpet(ao|ado|adisimo|adísimo|adita|á)\b", re.IGNORECASE), "petado"),
    (re.compile(r"\blagg+(eado|eadisimo|eadísimo|azo)?\b", re.IGNORECASE), "lag"),
    (re.compile(r"\blog[uí]?ear\b", re.IGNORECASE), "loguear"),
    (re.compile(r"\bunava[il]+able\b", re.IGNORECASE), "unavailable"),
    # Marcadores de ironía: xD y variantes (preservar como señal)
    (re.compile(r"\bx+d+\b", re.IGNORECASE), "xd"),
    # Luto irónico
    (re.compile(r"^F$", re.IGNORECASE | re.MULTILINE), "rip"),
    (re.compile(r"\bdep\b", re.IGNORECASE), "rip"),
    # Acrónimos emocionales importados (texto ya en minúsculas, conservar)
    (re.compile(r"\bw\s*t\s*f\b", re.IGNORECASE), "wtf"),
    (re.compile(r"\bf\s*m\s*l\b", re.IGNORECASE), "fml"),
]

# Reiteraciones extremas: comprimir a longitud 3 (mantiene énfasis sin ruido)
_REPEAT_3 = re.compile(r"(.)\1{3,}")  # 4+ -> 3

# Artefacto de exportación Excel/CSV: saltos de línea internos del mensaje
# guardados como la cadena literal "_x000D_" (\r) o "_x000A_" (\n). Afecta a
# ~41% del subcorpus. Se neutralizan a espacio ANTES de cualquier otra regla
# para que no contaminen la tokenización ni rompan los patrones del argot.
_XML_ESCAPE = re.compile(r"_x00[0-9A-Fa-f]{2}_")

# URLs (en este corpus aparecen pegadas a menudo)
_URL = re.compile(r"https?://\S+|www\.\S+")

# Citas de foro tipo "#22225" o "@usuario"
_CITA_NUM = re.compile(r"#\d+")
_MENCION = re.compile(r"@\w+")

# Mayúsculas grito: más del 50% de letras en mayúscula y >= 4 letras
_LETRAS = re.compile(r"[A-ZÁÉÍÓÚÑa-záéíóúñ]")
_MAYUS = re.compile(r"[A-ZÁÉÍÓÚÑ]")


def _es_grito(text: str) -> bool:
    letras = _LETRAS.findall(text)
    if len(letras) < 4:
        return False
    # Acrónimos y fórmulas rituales en caja alta (GG, GG WP, RITO, XD...) no son
    # gritos sino convención tipográfica del registro. Si el texto, sin espacios,
    # tiene <= 5 caracteres alfabéticos en total, se considera fórmula, no grito.
    if sum(1 for c in text if c.isalpha()) <= 5:
        return False
    mayus = sum(1 for c in letras if _MAYUS.match(c))
    return mayus / len(letras) > 0.5


class GamerPreprocessor:
    """Preprocesador de dominio gamer hispanohablante.

    Parameters
    ----------
    lowercase : bool
        Si True (por defecto), normaliza a minúsculas después de aplicar
        las reglas. Las mayúsculas grito se marcan con [GRITO] antes.
    mark_shouting : bool
        Si True, añade un token [GRITO] al inicio del mensaje cuando se
        detecta mayúscula sostenida. Marca expresiva preservada.
    """

    def __init__(self, lowercase: bool = True, mark_shouting: bool = True) -> None:
        self.lowercase = lowercase
        self.mark_shouting = mark_shouting

    def transform(self, text: str) -> str:
        if not text:
            return ""
        original = text

        # 0. Neutralizar artefactos de exportación (_x000D_ / _x000A_) a espacio.
        #    Debe ir lo primero: antes de _es_grito (para no contar el artefacto
        #    como caracteres) y antes de las reglas de argot.
        text = _XML_ESCAPE.sub(" ", text)

        # 1. Detectar grito antes de minusculizar (si está activado)
        grito = self.mark_shouting and _es_grito(text)

        # 2. Normalizar Unicode (NFC: forma compuesta canónica)
        text = unicodedata.normalize("NFC", text)

        # 3. URLs, citas, menciones -> tokens
        text = _URL.sub(" [URL] ", text)
        text = _CITA_NUM.sub(" [CITA] ", text)
        text = _MENCION.sub(" [USR] ", text)

        # 4. Reglas de normalización del argot
        for rx, repl in _NORMALIZATIONS:
            text = rx.sub(repl, text)

        # 5. Reiteraciones extremas (después de las reglas para no romperlas)
        text = _REPEAT_3.sub(r"\1\1\1", text)

        # 6. Minúsculas
        if self.lowercase:
            text = text.lower()

        # 7. Marca de grito al inicio
        if grito:
            text = "[grito] " + text

        # 8. Limpiar espacios sobrantes
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def transform_batch(self, texts: Iterable[str]) -> list[str]:
        return [self.transform(t) for t in texts]


# --------------------------------------------------------------------------- #
# Tests rápidos integrados (ejecutar el módulo directamente)                  #
# --------------------------------------------------------------------------- #

def _selftest() -> None:
    pre = GamerPreprocessor()
    casos = [
        ("RITO PLSSSSS", "rito_pls"),
        ("Rito Games strikes again", "rito strikes again"),
        ("xDDDDDDDDD", "xd"),
        ("gg wp rito", "gg_wp_rito"),
        ("compañía indie", "indie_company"),
        ("THEREISNOURFLEVEL", "thereisnourflevel"),
        ("petadisimo el server", "petado el server"),
        ("F", "rip"),
        ("ME CAGO EN DIOS", "[grito]"),  # detecta grito
        ("https://example.com/foo", "[url]"),
        ("#12345", "[cita]"),
        ("noooooooo", "nooo"),  # 4+ -> 3
    ]
    print("Auto-tests del preprocesador:")
    fallos = 0
    for entrada, esperado in casos:
        salida = pre.transform(entrada)
        ok = esperado.lower() in salida.lower()
        print(f"  [{'OK' if ok else 'FAIL'}] {entrada!r:35} -> {salida!r}")
        if not ok:
            fallos += 1
            print(f"        esperaba contener: {esperado!r}")
    print(f"\n{'Todo OK' if fallos == 0 else f'{fallos} fallos'}")


if __name__ == "__main__":
    _selftest()
