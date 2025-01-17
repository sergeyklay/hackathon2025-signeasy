"""PDF analysis and manipulation tools.

Utilities for analyzing and extracting information from PDF files:
- Determine if pages contain searchable text or images
- Analyze PDF structure and content
- Count pages
"""

import logging
from pathlib import Path
from typing import List, TypedDict

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFTypeInfo(TypedDict):
    """Type definition for PDF type detection result."""

    is_pdf: bool
    total_pages: int
    page_types: List[str]
    overall_type: str


def _is_image_based(page) -> bool:
    """Check if a PDF page is predominantly image-based."""
    resources = page.get("/Resources")
    if not resources:
        return False

    xobjects = resources.get("/XObject")
    if not xobjects:
        return False

    for _, xobj in xobjects.items():
        # Resolve the indirect object
        xobj_resolved = xobj.get_object()
        if xobj_resolved.get("/Subtype") == "/Image":
            return True

    return False


def detect_pdf_type(pdf_path: str | Path) -> PDFTypeInfo:
    """Determine the type of a PDF file, including mixed-type documents.

    Analyzes a PDF file to determine its characteristics including whether pages
    are text-based or image-based, and collects metadata.

    Args:
        pdf_path (str | Path): Path to the PDF file to analyze

    Returns:
        PDFTypeInfo: Dictionary containing PDF analysis results with fields:
            - is_pdf: Whether the file is a valid PDF
            - total_pages: Number of pages in the document
            - page_types: List of page types ("text-based" or "image-based")
            - overall_type: Document type classification ("text-based", "image-based", or "mixed")

    Raises:
        FileNotFoundError: If the specified file does not exist

    Example:
        >>> result = detect_pdf_type("document.pdf")
        >>> print(result)
        {
            'is_pdf': True,
            'total_pages': 3,
            'page_types': ['text-based', 'image-based', 'text-based'],
            'overall_type': 'mixed'
        }
    """

    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    # Initialize result structure
    result: PDFTypeInfo = {
        "is_pdf": False,
        "total_pages": 0,
        "page_types": [],
        "overall_type": "Unknown",
    }

    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            page_types = []
            for page in reader.pages:
                # Check if the page contains extractable text
                if page.extract_text().strip():
                    page_types.append("text-based")
                else:
                    # Check if the page has any content streams
                    if _is_image_based(page):
                        # The page has content streams, but no text,
                        # so assume it's an image-based page
                        page_types.append("image-based")
                    else:
                        # The page has no content streams, so it's a empty page
                        page_types.append("text-based")

            result["is_pdf"] = True
            result["page_types"] = page_types
            result["total_pages"] = len(reader.pages)

            # Determine the overall type
            unique_types = set(page_types)
            if len(unique_types) == 1:
                result["overall_type"] = unique_types.pop()
            else:
                result["overall_type"] = "mixed"
    except Exception as e:
        logger.warning(f"Error while analyzing {pdf_path} with pdfimages: {e}")
        result["is_pdf"] = False

    return result
