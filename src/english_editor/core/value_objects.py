class PositiveValue:
    """
    Value Object universal: valida invariante de dominio (valor > 0).
    Building block reusable en CUALQUIER sistema que requiera números positivos.
    """

    def __init__(self, value: int):
        if value <= 0:
            raise ValueError("Must be positive")
        self.value = value
