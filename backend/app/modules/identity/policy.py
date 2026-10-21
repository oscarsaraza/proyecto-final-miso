"""Política contra fuerza bruta del acceso del asegurado. Funciones puras, sin base de datos."""
import math
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Optional

MAX_PASSWORD_FAILURES = 5
LOCK_STEPS = (timedelta(minutes=15), timedelta(minutes=30), timedelta(minutes=60))
LOCK_COUNT_RESET_AFTER = timedelta(hours=24)

MAX_CODE_ATTEMPTS = 3
OTP_MIN_INTERVAL = timedelta(seconds=60)
OTP_MAX_PER_HOUR = 5

IP_WINDOW = timedelta(minutes=15)
IP_MAX_LOGIN_FAILURES = 20
IP_MAX_OTP_REQUESTS = 30

MIN_PASSWORD_LENGTH = 8


def seconds_until(moment: datetime, now: datetime) -> int:
    return max(1, math.ceil((moment - now).total_seconds()))


def lock_duration(lock_count: int) -> timedelta:
    return LOCK_STEPS[min(max(lock_count, 1), len(LOCK_STEPS)) - 1]


def effective_lock_count(lock_count: int, locked_until: Optional[datetime], now: datetime) -> int:
    """El bloqueo creciente se olvida si pasó un día desde el último."""
    if locked_until is not None and now - locked_until >= LOCK_COUNT_RESET_AFTER:
        return 0
    return lock_count


def otp_request_retry_after(previous_requests: Iterable[datetime], now: datetime) -> Optional[int]:
    recent = sorted(t for t in previous_requests if now - t < timedelta(hours=1))
    if not recent:
        return None
    if now - recent[-1] < OTP_MIN_INTERVAL:
        return seconds_until(recent[-1] + OTP_MIN_INTERVAL, now)
    if len(recent) >= OTP_MAX_PER_HOUR:
        return seconds_until(recent[-OTP_MAX_PER_HOUR] + timedelta(hours=1), now)
    return None


def window_retry_after(events: Iterable[datetime], limit: int, now: datetime) -> Optional[int]:
    """Si hay `limit` eventos en la ventana, segundos hasta que salga el más viejo de los que cuentan."""
    recent = sorted(t for t in events if now - t < IP_WINDOW)
    if len(recent) < limit:
        return None
    return seconds_until(recent[-limit] + IP_WINDOW, now)


def is_strong_password(password: str) -> bool:
    return (
        len(password) >= MIN_PASSWORD_LENGTH
        and any(c.isalpha() for c in password)
        and any(c.isdigit() for c in password)
    )


def client_ip(headers: Mapping[str, str], fallback: Optional[str]) -> Optional[str]:
    """Cloudflare pone CF-Connecting-IP; el balanceador de AWS pone X-Forwarded-For."""
    cf = headers.get("cf-connecting-ip")
    if cf:
        return cf.strip()
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return fallback
