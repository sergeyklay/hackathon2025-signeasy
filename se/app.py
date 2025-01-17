import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app=None, metadata=metadata)


def create_app(config=None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    configure_app(app, config)
    configure_logging(app)
    configure_directories(app)
    configure_ai(app)
    configure_blueprints(app)
    configure_extensions(app)
    configure_context_processors(app)

    return app


def configure_app(app: Flask, config_name=None):
    """Configure application."""
    from se.config import Config, config

    # Use the default config and override it afterwards
    app.config.from_object(config["default"])

    if config is not None:
        # Config name as a string
        if isinstance(config_name, str) and config_name in config:
            app.config.from_object(config[config_name])
            config[config_name].init_app(app)
        # Config as an object
        else:
            app.config.from_object(config_name)
            if isinstance(config_name, Config):
                config_name.init_app(app)

    # Update config from environment variable (if any). This environment
    # variable can be set in the shell before starting the server:
    #
    #    $ export SE_SETTINGS="/var/www/signeasy/settings.cfg"
    #    $ flask --app runner:app run
    #
    # The configuration files themselves are actual Python files.  Only values
    # in uppercase are actually stored in the con fig object later on. So make
    # sure to use uppercase letters for your config keys.
    app.config.from_envvar("SE_SETTINGS", silent=True)


def configure_logging(app: Flask):
    """Configure the logger for the application."""
    import logging

    # Remove the default Flask logger handlers
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    log_level = app.config.get("LOG_LEVEL", logging.DEBUG)

    # Set the logging level for the app logger
    app.logger.setLevel(log_level)

    # Formatter for log messages
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        fmt=fmt,
        datefmt=datefmt,
    )

    # Stream handler for stdout
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)

    # Attach handlers to the app logger
    app.logger.addHandler(stdout_handler)

    # Configure Werkzeug logger (used for HTTP request logs)
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.handlers.clear()
    werkzeug_logger.addHandler(stdout_handler)
    werkzeug_logger.propagate = False

    logging.basicConfig(
        stream=sys.stdout,
        level=log_level,
        format=fmt,
        datefmt=datefmt,
    )


def configure_directories(app: Flask):
    """Configure directories for the application."""
    keys = ["STORAGE_DIR", "DOWNLOADS_DIR", "UPLOADS_DIR"]
    for key in keys:
        directory = app.config.get(key)
        if directory:
            os.makedirs(directory, exist_ok=True)


def configure_ai(app: Flask):
    """Configure the AI models for the application."""
    import openai
    from llama_index.core import Settings
    from llama_index.llms.openai import OpenAI

    openai.api_key = app.config.get("OPENAI_API_KEY")
    model = app.config.get("OPENAI_MODEL")
    if model:
        Settings.llm = OpenAI(model=model)


def configure_blueprints(app: Flask):
    """Configure blueprints for the application."""
    from se.blueprints.main import main

    app.register_blueprint(main)

    from se.blueprints.sender import sender

    app.register_blueprint(sender)

    from se.blueprints.recipient import recipient

    app.register_blueprint(recipient)


def configure_extensions(app: Flask):
    """Configure extensions for the application."""
    from flask_debugtoolbar import DebugToolbarExtension
    from flask_mail import Mail
    from flask_migrate import Migrate, upgrade

    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Migrate
    migrate = Migrate()
    migrate.init_app(app, db)

    # Flask-Mail
    mail = Mail()
    mail.init_app(app)

    if app.debug:
        # Debug toolbar
        DebugToolbarExtension(app)

        @app.cli.command()
        def cleanup():
            """Clean up the database."""
            db.drop_all()
            db.create_all()

    @app.cli.command()
    def deploy():
        """Run deployment tasks."""
        # Migrate database to latest revision.
        upgrade()

    @app.cli.command()
    def seed():
        """Add seed data to the database."""
        from se.seeder import demo_seed

        demo_seed()


def configure_context_processors(app: Flask):
    """Configure the context processors."""
    import inspect

    from se import models

    @app.shell_context_processor
    def make_shell_context():
        """Configure flask shell command to autoimport app objects."""
        return {
            "app": app,
            "db": db,
            **dict(inspect.getmembers(models, inspect.isclass)),
        }


def load_env_vars(base_path: str):
    """Load the current dotenv as system environment variable."""
    dotenv_path = os.path.join(base_path, ".env")

    from dotenv import load_dotenv

    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
