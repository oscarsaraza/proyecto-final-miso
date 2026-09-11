def calcular_prima(monto: float, edad: int, score: int) -> float:
    """Sin aleatoriedad, para que las corridas del experimento sean reproducibles."""
    factor_riesgo = 1.6 - (score / 1000)
    factor_edad = 1 + max(0, edad - 30) * 0.01
    return round(monto * 0.012 * factor_riesgo * factor_edad, 2)
