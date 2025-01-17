"""The views module for the app."""

import os

from flask import abort, render_template

from se.utils import strtobool

from . import main


@main.before_app_request
def maintained():
    try:
        maintenance = strtobool(os.getenv("MAINTENANCE_MODE", "False"))
        if bool(maintenance):
            abort(503)
    except ValueError:
        pass


@main.route("/", methods=["GET"], endpoint="home")
def home():
    return render_template("main/home.html")


@main.route("/about", methods=["GET"], endpoint="about")
def about():
    return render_template("main/about.html")


@main.route("/privacy", methods=["GET"], endpoint="privacy")
def privacy():
    return render_template("main/privacy.html")


@main.route("/licensing", methods=["GET"], endpoint="licensing")
def licensing():
    return render_template("main/licensing.html")


@main.route("/contact", methods=["GET"], endpoint="contact")
def contact():
    return render_template("main/contact.html")
