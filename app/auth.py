import hashlib
import secrets
from typing import Optional, Dict
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Временное хранилище активных токенов (в продакшене заменить на БД)
# Для первого запуска используем словарь в памяти
_active_tokens: Dict[str, int] = {}  # token -> user_id


def hash_password(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет пароль"""
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int) -> str:
    """
    Создаёт простой токен (временное решение)
    """
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = user_id
    return token


def verify_token(token: str) -> Optional[int]:
    """
    Проверяет токен, возвращает user_id или None
    """
    return _active_tokens.get(token)


def revoke_token(token: str) -> None:
    """
    Отзывает токен (логаут)
    """
    if token in _active_tokens:
        del _active_tokens[token]


def get_token_fingerprint(token: str) -> str:
    """
    Получает fingerprint токена
    """
    return hashlib.sha256(token.encode()).hexdigest()