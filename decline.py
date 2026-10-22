"""Кривые падения дебита Арпса (Arps decline curves).

Единицы:
    q   — дебит, м³/сут;
    t   — время, месяцы;
    di  — начальный номинальный темп падения, 1/месяц;
    b   — показатель Арпса: 0 — экспоненциальное, 0 < b < 1 — гиперболическое,
          1 — гармоническое падение.
Накопленная добыча возвращается в м³ (сутки пересчитываются через средний месяц).
"""

import math

DAYS_PER_MONTH = 365.25 / 12


def decline_type(b: float) -> str:
    if b == 0:
        return "exponential"
    if b == 1:
        return "harmonic"
    return "hyperbolic"


def rate(qi: float, di: float, b: float, t: float) -> float:
    """Дебит в момент t."""
    if b == 0:
        return qi * math.exp(-di * t)
    return qi / (1 + b * di * t) ** (1 / b)


def cumulative(qi: float, di: float, b: float, t: float) -> float:
    """Накопленная добыча от 0 до t, м³."""
    q = rate(qi, di, b, t)
    if b == 0:
        np_month_units = (qi - q) / di
    elif b == 1:
        np_month_units = qi / di * math.log(qi / q)
    else:
        np_month_units = qi**b / ((1 - b) * di) * (qi ** (1 - b) - q ** (1 - b))
    return np_month_units * DAYS_PER_MONTH


def time_to_rate(qi: float, di: float, b: float, q_limit: float) -> float:
    """Время (мес.), за которое дебит упадёт до q_limit."""
    if q_limit >= qi:
        return 0.0
    if b == 0:
        return math.log(qi / q_limit) / di
    return ((qi / q_limit) ** b - 1) / (b * di)


def forecast(qi: float, di: float, b: float, months: int) -> list[dict]:
    """Помесячный прогноз: дебит на конец месяца и накопленная добыча."""
    return [
        {
            "month": m,
            "rate_m3_per_day": round(rate(qi, di, b, m), 3),
            "cumulative_m3": round(cumulative(qi, di, b, m), 1),
        }
        for m in range(months + 1)
    ]
