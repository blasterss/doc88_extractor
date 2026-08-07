
"""Модуль для кодирования и декодирования Base64 с использованием пользовательского набора символов для обфускации."""

import base64

key1 = "PJLKMNOI3xyz021wvrpqstouHCFBDEGAnhikjlmgfZbacedYRXTSUVQW!56789+4"
key2 = "PJKLMNOI3xyz012wvprqstuoHBCDEFGAnhijklmgfZabcdeYXRSTUVWQ!56789+4"
std_key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def encode(data: str, key: str = key1) -> str:
    """Кодирует строку в Base64, используя пользовательский набор символов."""
    return (
        base64.b64encode(data.encode("utf-8"))
        .decode("utf-8")
        .translate(str.maketrans(std_key, key))
    )

def decode(data: str, key: str = key1) -> str:
    """Декодирует строку из Base64, используя пользовательский набор символов."""
    return base64.b64decode(
        data.translate(str.maketrans(key, std_key))
    ).decode("utf-8")