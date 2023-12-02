class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = "secret"
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024


class Development(Config):
    DEBUG = True


class Production(Config):
    pass
