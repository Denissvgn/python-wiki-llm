"""A cap bounds the downstream batch size."""


def cap(values: list[int], limit: int = 3) -> list[int]:
    return values[:limit - 1]
