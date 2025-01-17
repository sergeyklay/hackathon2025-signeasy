"""The views module for the recipient role."""

import os

from flask import abort, flash, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from se.models import AnalysisResult, File
from se.modules.progress_tracker import get_tracker

from . import recipient


@recipient.route("/downloads")
def download_report():
    """Download a file by its ID with proper security checks."""
    file_id = request.args.get("file_id", type=int)
    if not file_id:
        abort(400, description="File ID is required")

    file = File.get_or_404(file_id)

    # Verify file exists on disk
    file_path = file.get_path()
    if not os.path.exists(file_path):
        abort(404, description="File not found on disk")

    # Send file with proper mime type and original filename
    return send_file(
        file_path,
        mimetype=file.file_type,
        as_attachment=True,
        download_name=secure_filename(file.orig_filename),
    )


@recipient.route("/recipient")
def welcome():
    tracker = get_tracker("recipient")
    tracker.set_current_step("Deal")
    return render_template(
        "recipient/welcome.html",
        progress_steps=tracker.get_progress_steps(),
    )


@recipient.route("/review", endpoint="analysis", methods=["GET", "POST"])
def analysis():
    tracker = get_tracker("recipient")
    tracker.set_current_step("Review")

    if request.method == "POST":
        analysis_id = request.form.get("analysis_id")
    else:
        analysis_id = request.args.get("a", type=int)

    if not analysis_id:
        flash("Provide a Deal ID to see the analysis results.", "error")
        return render_template("recipient/review.html")

    model_analysis_result = AnalysisResult.query.get(analysis_id)
    if not model_analysis_result:
        flash(f"Deal with ID {analysis_id} not found.", "error")
        return render_template("recipient/review.html")

    file = model_analysis_result.document.file
    if not file:
        flash(
            (
                "Oops! Uploaded file not found. "
                "Please let us know about this bug. "
                "Error Code: SU1001"
            ),
            "error",
        )
        return render_template("recipient/review.html")

    return render_template(
        "recipient/review.html",
        analysis=model_analysis_result.get_combined_analysis(),
        download_link=url_for(
            "recipient.download_report", file_id=model_analysis_result.document.file_id
        ),
        progress_steps=tracker.get_progress_steps(),
        debug=request.args.get("debug", type=bool, default=False),
    )


@recipient.route("/complete")
def complete():
    tracker = get_tracker("recipient")
    tracker.set_current_step("Complete")
    return render_template(
        "recipient/complete.html",
        progress_steps=tracker.get_progress_steps(),
    )
