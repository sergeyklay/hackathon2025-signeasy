import os

from se.utils import strtobool


class Config:
    """Base config, uses staging database server."""

    TESTING = False
    DEBUG = False
    BASE_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Directory settings.
    STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(BASE_PATH, "storage"))
    DOWNLOADS_DIR = os.getenv("DOWNLOADS_DIR", os.path.join(BASE_PATH, "downloads"))
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(BASE_PATH, "uploads"))

    # SQLAlchemy settings.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # File upload settings.
    ALLOWED_EXTENSIONS = {"pdf"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    MIN_FILE_SIZE = 1024  # Minimum size for a valid PDF file in bytes

    # OpenAI settings.
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", default="gpt-4o-mini")

    # Flask-DebugToolbar.
    # For more see https://flask-debugtoolbar.readthedocs.io/en/latest/#configuration
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Flask-Mail settings.
    # For details on Flask-Mail refer to:
    # https://flask-mail.readthedocs.io/en/latest/
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = strtobool(os.getenv("MAIL_USE_TLS", "true"))
    MAIL_USE_SSL = strtobool(os.getenv("MAIL_USE_SSL", "false"))
    MAIL_DEFAULT_SENDER = "SignEasy <noreply@signeasy.local>"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development config."""

    DEBUG = True
    # Uncomment the following line to enable template loading explanation.
    # EXPLAIN_TEMPLATE_LOADING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DEV_DATABASE_URI",
        "sqlite:///" + os.path.join(Config.BASE_PATH, "dev-db.sqlite3"),
    )


class TestingConfig(Config):
    """Testing config."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URI", "sqlite://")


class ProductionConfig(Config):
    """Production config."""

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "PROD_DATABASE_URI",
        "sqlite:///" + os.path.join(Config.BASE_PATH, "prod-db.sqlite3"),
    )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
