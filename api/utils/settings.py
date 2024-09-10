from decouple import config


class Settings:
    DB_URL: str = str(config('DB_URL'))
    REDIS_URL: str = str(config('REDIS_URL'))
    RABBITMQ_URL: str = str(config('RABBITMQ_URL'))

    TEST: str = str(config('TEST'))

    TEST_LOGIN_MAX_ATTEMPTS: int = int(config('TEST_LOGIN_MAX_ATTEMPTS'))
    TEST_REGISTER_MAX_ATTEMPTS: int = int(config('TEST_REGISTER_MAX_ATTEMPTS'))
    TEST_OTHERS_MAX_ATTEMPTS: int = int(config('TEST_OTHERS_MAX_ATTEMPTS'))
    

    LOGIN_MAX_ATTEMPTS: int = int(config('LOGIN_MAX_ATTEMPTS'))
    REGISTER_MAX_ATTEMPTS: int = int(config('REGISTER_MAX_ATTEMPTS'))
    OTHERS_MAX_ATTEMPTS: int = int(config('OTHERS_MAX_ATTEMPTS'))

    SECRET_KEY: str = str(config('SECRET_KEY'))
    ALGORITHM: str = str(config('ALGORITHM'))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))
    REFRESH_TOKEN_EXPIRE: int = int(config('REFRESH_TOKEN_EXPIRE'))

    INITIAL_LOCKOUT_DURATION: int = int(config('INITIAL_LOCKOUT_DURATION'))
    MAX_PENALTY_DURATION: int = int(config('MAX_PENALTY_DURATION'))
    LOCKOUT_THRESHOLD: int = int(config('LOCKOUT_THRESHOLD'))

settings = Settings()
