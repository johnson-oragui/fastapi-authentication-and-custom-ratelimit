from api.db.redis_database import get_redis_sync

def store_jti_in_cache(jti: str, exp: int, token_type: str) -> None:
    """
    Caches the jti on jwt token generation.
    """
    if token_type == 'access':
        expire_at = 60 * exp
    else:
        expire_at = 60 * 60 * 24 * exp
    key: str = f'jti_{jti}_{token_type}'
    try:
        with get_redis_sync() as redis:
            redis.set(key, 'active', ex=expire_at)
    except Exception as exc:
        print(exc)


def check_active_jti(jti: str, token_type: str) -> bool:
    """
    Check if the JTI (token ID) is active in the cache.
    """
    key: str = f'jti_{jti}_{token_type}'
    try:
        with get_redis_sync() as redis:
            return redis.get(key) == 'active'
    except Exception as exc:
        print(exc)
        return False

def revoke_jti(jti: str, token_type: str):
    """
    Revokes token.
    """
    key = f"jti_{jti}_{token_type}"

    with get_redis_sync() as redis:
        redis.delete(key)
