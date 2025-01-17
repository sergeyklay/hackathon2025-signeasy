"""The sender blueprint module for the application."""

from flask import Blueprint

sender = Blueprint(
    "sender",
    __name__,
    template_folder="templates",
    # TODO: static_folder, static_url_path
)

from . import views  # noqa: F401, E402
