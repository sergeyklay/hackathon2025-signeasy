"""The views module for the sender role."""

import json
import os

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_mail import Message

from se.models import AnalysisResult, Document, File
from se.modules.agent_controller import AgentController
from se.modules.progress_tracker import get_tracker
from se.modules.upload_manager import UploadManager

from . import sender


@sender.route("/sender", endpoint="welcome")
def welcome():
    tracker = get_tracker("sender")
    tracker.set_current_step("Upload")
    return render_template(
        "sender/welcome.html",
        progress_steps=tracker.get_progress_steps(),
    )


@sender.route("/analysis", endpoint="analysis")
def analysis():
    analysis_id = request.args.get("a", type=int)
    debug = request.args.get("debug", type=bool, default=False)

    tracker = get_tracker("sender")
    tracker.set_current_step("Review")

    if not analysis_id:
        flash("Upload a document to see the analysis results.", "error")
        return render_template("sender/analysis.html")

    model_analysis_result = AnalysisResult.query.get(analysis_id)
    if not model_analysis_result:
        flash(f"Analysis result with ID {analysis_id} not found.", "error")
        return render_template("sender/analysis.html")

    return render_template(
        "sender/analysis.html",
        analysis=model_analysis_result.get_combined_analysis(),
        progress_steps=tracker.get_progress_steps(),
        debug=debug,
    )


def allowed_file(filename) -> bool:
    """Check if the file has an allowed extension."""
    exts = current_app.config.get("ALLOWED_EXTENSIONS", {})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in exts


def validate_file(file):
    # Validate if file exists
    if not file:
        return False, "No file provided."

    # Validate file extension
    if not allowed_file(file.filename):
        exts = current_app.config.get("ALLOWED_EXTENSIONS", {})
        message = "Invalid file type"
        if len(exts) > 0:
            message += f". Allowed types: {', '.join(exts)}"
        return False, message

    # Validate file size
    file.stream.seek(0, os.SEEK_END)  # Move to the end of the file stream
    file_size = file.stream.tell()  # Get the current position (file size in bytes)
    file.stream.seek(0)  # Reset the cursor to the beginning of the file stream

    min_size = current_app.config.get("MIN_FILE_SIZE", 0)
    max_size = current_app.config.get("MAX_FILE_SIZE", 5 * 1024 * 1024)

    if file_size < min_size:
        return False, f"File is too small. Minimum size is {min_size} bytes."

    if file_size > max_size:
        return (
            False,
            f"File size exceeds the maximum limit of {max_size / (1024 * 1024)} MB.",
        )

    return True, None


@sender.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    is_valid, error_message = validate_file(file)

    if not is_valid:
        flash(error_message or "Invalid file", "error")
        return redirect(url_for("sender.welcome"))

    # 1. Uploading the file
    upload_manager = UploadManager(current_app.config.get("UPLOADS_DIR"))
    uploaded_file = upload_manager.save_file(file)

    model_file = File.create(
        sha256_content=uploaded_file.sha256_content,
        filename=uploaded_file.filename,
        orig_filename=uploaded_file.orig_filename,
        file_type=uploaded_file.content_type,
        file_size=uploaded_file.content_length,
    )
    model_file.save()

    # 2. Create a Document entity
    model_document = Document.create(
        file=model_file,
        type="Unknown",
    )
    model_document.save()

    # 3. Analysis with LlamaIndex
    # Initialize AgentController
    agent = AgentController(
        persist_dir=current_app.config.get("STORAGE_DIR") or "storage"
    )

    analysis_result, steps = agent.run(model_file.get_path())

    if not steps or len(steps) == 0:
        message = (
            "No analysis steps determined by the system. "
            "Please let us know about this bug. "
            "Error Code: SA1001"
        )
        flash(message, "error")
        return redirect(url_for("sender.welcome"))

    if not analysis_result or len(analysis_result) == 0:
        message = (
            "No analysis result determined by the system. "
            "Please let us know about this bug. "
            "Error Code: SA1002"
        )
        flash(message, "error")
        return redirect(url_for("sender.welcome"))

    model_analysis_result = AnalysisResult.create(
        document=model_document,
        analysis_result=json.dumps(analysis_result),
        analysis_steps=json.dumps(steps),
    )
    model_analysis_result.save()

    model_document.type = analysis_result.get("document_type", "Unknown")
    model_document.save()

    # 4. Defining and adding signature fields
    # TODO: Implement signature placement

    # 5. Redirect to /analysis with the results.
    # For example '/analysis?a=2&d=20250105_114947_File2_with_signatures.pdf'
    flash("File uploaded successfully!", "success")
    redirect_to = url_for(
        "sender.analysis",
        a=model_analysis_result.id,
    )
    return redirect(redirect_to)


@sender.route("/send", endpoint="send")
def send():
    analysis_id = request.args.get("a", type=int)
    analysis_result = None
    analysis_date = None
    document_name = None

    tracker = get_tracker("sender")
    tracker.set_current_step("Send")

    if not analysis_id:
        flash("Upload a document to be able send it.", "error")
    else:
        model_analysis_result = AnalysisResult.query.get(analysis_id)
        if not model_analysis_result:
            flash(f"Analysis result with ID {analysis_id} not found.", "error")
        else:
            analysis_result = model_analysis_result.get_analysis_object()
            analysis_date = model_analysis_result.created_at
            document_name = model_analysis_result.document.file.orig_filename

    return render_template(
        "sender/send.html",
        analysis_id=analysis_id,
        progress_steps=tracker.get_progress_steps(),
        analysis_result=analysis_result,
        document_name=document_name,
        analysis_date=analysis_date,
    )


@sender.route("/mail", endpoint="mail", methods=["POST"])
def sendmail():
    recipient_email = request.form.get("email")
    recipient_name = request.form.get("name")
    recipient_message = request.form.get("message")
    analysis_id = request.form.get("analysis_id")

    if not recipient_email:
        flash("Recipient email is required.", "error")
        return redirect(url_for("sender.welcome"))

    if not recipient_name:
        recipient_name = "there"

    subject = "Invitation to Sign the Document"
    full_url = url_for("recipient.analysis", a=analysis_id, _external=True)

    html_content = render_template(
        "sender/invitation-email.html",
        recipient=recipient_name,
        message=recipient_message,
        full_url=full_url,
        analysis_id=analysis_id,
    )
    text_content = render_template(
        "sender/invitation-email.txt",
        recipient=recipient_name,
        message=recipient_message,
        full_url=full_url,
        analysis_id=analysis_id,
    )

    msg = Message(
        subject=subject,
        recipients=[recipient_email],
        body=text_content,
        html=html_content,
    )

    try:
        with current_app.extensions["mail"].connect() as conn:
            conn.send(msg)
        session["email_sent"] = True
        flash("Document successfully sent!", "success")
        return redirect(url_for("sender.send_confirmation"))
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        flash("Failed to send email. Please try again.", "error")
        return redirect(url_for("sender.welcome"))


@sender.route("/send-confirmation", endpoint="send_confirmation")
def send_confirmation():
    if not session.get("email_sent"):
        flash("Please send an email first.", "error")
        return redirect(url_for("sender.welcome"))

    session.pop("email_sent", None)
    return render_template("sender/confirmation.html")
