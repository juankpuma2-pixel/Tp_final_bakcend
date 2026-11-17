"""Módulo de utilidades y validación de archivos."""


def parece_imagen(contenido: bytes) -> bool:
    """
    Verifica los primeros bytes (firmas mágicas) de un archivo binario.
    Acepta:
      - JPG: b"\\xff\\xd8\\xff"
      - PNG: b"\\x89PNG\\r\\n\\x1a\\n"
      - WebP: b"RIFF"
    """
    if not contenido:
        return False

    return (
        contenido.startswith(b"\xff\xd8\xff")
        or contenido.startswith(b"\x89PNG\r\n\x1a\n")
        or contenido.startswith(b"RIFF")
    )
