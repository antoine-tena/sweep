"""Tailles lisibles : la mémoire se compte en octets, s'affiche en Mo ou Go."""

BYTES_PER_MIB = 1024**2
BYTES_PER_GIB = 1024**3


def format_size(size_bytes: int) -> str:
    if size_bytes >= BYTES_PER_GIB:
        return f"{size_bytes / BYTES_PER_GIB:.1f} Go".replace(".", ",")
    return f"{size_bytes / BYTES_PER_MIB:.0f} Mo"
