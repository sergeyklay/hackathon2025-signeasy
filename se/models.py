"""ORM models for the application and helper functions."""

import json
import os
from datetime import datetime
from typing import List

import sqlalchemy as sa
from flask import abort
from sqlalchemy import orm as so
from sqlalchemy.sql import func

from se.app import db
from se.pdftools import detect_pdf_type


class BaseMixin:
    @classmethod
    def get(cls, entity_id):
        """Return the model with the specified identifier."""
        return db.session.get(cls, entity_id)

    @classmethod
    def get_or_404(cls, entity_id):
        """Return the model with the specified identifier.

        Raise a HTTPException with 404 status code if a record with the
        specified identifier not found in the database.
        """
        rv = cls.get(entity_id)
        if rv is None:
            abort(404, description=f"{cls.__name__} not found")
        return rv

    @classmethod
    def create(cls, **kwargs):
        """Create and save a new model instance.

        Creates a new model instance with the passed parameters, saves it to
        the database using the save method and returns the created instance.
        """
        instance = cls(**kwargs)
        instance.save()
        return instance

    def save(self):
        """Save the current model to the database."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the current model from the database."""
        db.session.delete(self)
        db.session.commit()


class IdentityMixin:
    """Mixin class to add identity fields to a SQLAlchemy model."""

    id: so.Mapped[int] = so.mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    def __repr__(self):
        """Returns the object representation in string format."""
        return f"<{self.__class__.__name__} id={self.id!r}>"


class TimestampMixin:
    """Mixin class to add timestamp fields to a SQLAlchemy model."""

    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )

    updated_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
        onupdate=func.now(),
        server_default=func.now(),
    )

    def last_modified(self) -> str:
        """Get the time of the last model update."""
        modified = self.updated_at or self.created_at or datetime.utcnow()
        return modified.strftime("%a, %d %b %Y %H:%M:%S GMT")


class File(BaseMixin, IdentityMixin, TimestampMixin, db.Model):
    __tablename__ = "files"

    sha256_content: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        index=True,
        nullable=False,
    )

    filename: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        index=True,
        nullable=False,
        default="Unknown",
    )

    orig_filename: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        index=True,
        nullable=False,
    )

    file_type: so.Mapped[str] = so.mapped_column(
        sa.String(50),
        nullable=False,
    )

    file_size: so.Mapped[str] = so.mapped_column(
        sa.Integer(),
        nullable=False,
    )

    document: so.Mapped[List["Document"]] = so.relationship(
        back_populates="file",
    )

    def get_path(self) -> str:
        """Return the full path to the file."""
        from flask import current_app

        upload_folder = current_app.config.get("UPLOADS_DIR", "uploads")
        return os.path.join(upload_folder, self.filename)


class Document(BaseMixin, IdentityMixin, TimestampMixin, db.Model):
    __tablename__ = "documents"

    type: so.Mapped[str] = so.mapped_column(
        sa.String(255),
        index=True,
        default="Unknown",
    )

    file_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("files.id"),
        nullable=False,
        index=True,
    )

    file: so.Mapped["File"] = so.relationship(
        back_populates="document",
    )

    analysis_result: so.Mapped[List["AnalysisResult"]] = so.relationship(
        back_populates="document",
    )

    pages: so.Mapped[List["Page"]] = so.relationship(
        "Page",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def get_num_pages(self) -> int:
        """Return the number of pages in the document."""
        return len(self.pages) if self.pages else 0

    def get_full_content(self) -> str:
        """Return the concatenated content of all pages."""
        pages = sorted(self.pages, key=lambda p: p.page_number) if self.pages else []
        return "\n".join(page.page_content for page in pages)

    def get_pages_summary(self) -> List[dict]:
        """Return a list of dictionaries with page_number and page_content."""
        return [
            {"page_number": page.page_number, "page_content": page.page_content}
            for page in sorted(self.pages, key=lambda p: p.page_number)
        ]


# TODO: No longer needed, remove
class Page(BaseMixin, IdentityMixin, TimestampMixin, db.Model):
    """Represents the content of a specific page of a document."""

    __tablename__ = "pages"

    document_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    document: so.Mapped["Document"] = so.relationship(
        back_populates="pages",
    )

    page_number: so.Mapped[int] = so.mapped_column(
        sa.Integer(),
        nullable=False,
        index=True,
    )

    page_content: so.Mapped[str] = so.mapped_column(
        sa.Text(),
        nullable=False,
    )


class AnalysisResult(BaseMixin, IdentityMixin, TimestampMixin, db.Model):
    __tablename__ = "analysis_results"

    document_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    document: so.Mapped["Document"] = so.relationship(
        back_populates="analysis_result",
    )

    analysis_result: so.Mapped[str] = so.mapped_column(
        sa.JSON(),
    )

    analysis_steps: so.Mapped[str] = so.mapped_column(
        sa.JSON(),
    )

    def get_analysis_object(self):
        """
        Return the parsed Python object from the JSON analysis_result field.

        :return: Parsed Python object (e.g., dict) from the analysis_result field.
        """
        try:
            if self.analysis_result and isinstance(self.analysis_result, str):
                return json.loads(self.analysis_result)
            return dict()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in analysis_result: {e}")

    def get_steps_object(self):
        """
        Return the parsed Python object from the JSON analysis_steps field.

        :return: Parsed Python object (e.g., dict) from the analysis_steps field.
        """
        try:
            if self.analysis_steps and isinstance(self.analysis_steps, str):
                return json.loads(self.analysis_steps)
            return dict()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in analysis_steps: {e}")

    def get_combined_analysis(self) -> dict:
        """Merge the analysis steps and analysis result into a single dictionary."""
        step_data = self.get_steps_object()
        analysis_data = self.get_analysis_object()

        document_type = "Unknown"
        if "document_type" in analysis_data:
            document_type = analysis_data["document_type"]

        file_info = {
            "is_pdf": False,
            "total_pages": "Unknown",
            "page_types": [],
            "overall_type": "Unknown",
        }

        # Detect if the file is a PDF.
        file_type = self.document.file.file_type
        if file_type == "application/pdf":
            pdf_type = detect_pdf_type(self.document.file.get_path())
            if pdf_type:
                file_info = pdf_type

        # Initialize the result dictionary
        result = {
            "id": self.id,
            "document_type": document_type,
            "file_name": self.document.file.orig_filename,
            "file_info": file_info,
            "analysis": [],
        }

        # Process each analysis step from step_data
        for step in step_data["analysis_steps"]:
            category = step["category"]

            raw_result = analysis_data.get(category, [])
            analytics_result = []
            if step["type"] == "list":
                for item in raw_result:
                    if isinstance(item, dict):
                        analytics_result += list(item.values())
                    else:
                        analytics_result.append(item)
            else:
                analytics_result = raw_result

            analysis_item = {
                "category": category,
                "type": step["type"],
                "columns": step.get("columns", []),
                "values": analytics_result,
            }
            result["analysis"].append(analysis_item)

        return result
