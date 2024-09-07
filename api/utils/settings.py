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

settings = Settings()
