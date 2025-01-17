"""The main blueprint module for the application."""

from flask import Blueprint

main = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    # TODO: static_folder, static_url_path
)

from . import errors, views  # noqa: F401, E402
