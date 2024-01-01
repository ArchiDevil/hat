class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = "secret"
    MAX_CONTENT_LENGTH = 96 * 1024 * 1024


class Development(Config):
    DEBUG = True


class Testing(Config):
    TESTING = True


class Production(Config):
    SECRET_KEY = "REAL SECRET KEY"
