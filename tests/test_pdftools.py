from pathlib import Path
from unittest.mock import patch

import pytest

from se.pdftools import detect_pdf_type


def test_nonexistent_file():
    """Test with a nonexistent file."""
    with pytest.raises(FileNotFoundError):
        detect_pdf_type("nonexistent.pdf")


def test_empty_pdf(tmp_path):
    """Test with an empty PDF file."""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")

    result = detect_pdf_type(empty_pdf)
    assert result == {
        "is_pdf": False,
        "total_pages": 0,
        "page_types": [],
        "overall_type": "Unknown",
    }


def test_text_based_pdf():
    """Test with a text-based PDF file."""
    pdf_path = Path("tests/resources/blank.pdf")

    result = detect_pdf_type(pdf_path)
    assert result["is_pdf"] is True
    assert result["total_pages"] == 1
    assert result["page_types"] == ["text-based"]
    assert result["overall_type"] == "text-based"


def test_image_based_pdf(mocker):
    """Test with an image-based PDF using a mocked pdfimages."""
    pdf_path = Path("tests/resources/agreement-10.pdf")

    result = detect_pdf_type(pdf_path)
    assert result["is_pdf"] is True
    assert result["total_pages"] == 2
    assert result["page_types"] == ["image-based", "image-based"]
    assert result["overall_type"] == "image-based"


def test_invalid_pdf(tmp_path):
    """Test with an invalid PDF file."""
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("This is not a PDF file")

    result = detect_pdf_type(invalid_pdf)
    assert result["is_pdf"] is False
    assert result["total_pages"] == 0
    assert result["page_types"] == []
    assert result["overall_type"] == "Unknown"


def test_mixed_type_pdf(tmp_path):
    """Test with a mixed-type PDF."""
    test_pdf = tmp_path / "mixed.pdf"
    test_pdf.write_bytes(
        b"""%PDF-1.7
1 0 obj<</Pages 2 0 R/Type/Catalog>>endobj
2 0 obj<</Count 2/Kids[3 0 R 4 0 R]/Type/Pages>>endobj
3 0 obj<</Parent 2 0 R/Type/Page>>endobj
4 0 obj<</Parent 2 0 R/Type/Page>>endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000107 00000 n
0000000148 00000 n
trailer
<</Root 1 0 R/Size 5>>
startxref
189
%%EOF"""
    )  # Minimal valid PDF content with 2 pages

    # Patch the PdfReader at the module where it's imported
    with patch("se.pdftools.PdfReader") as mock_reader:
        # Mock a PDF with 2 pages - one text-based, one image-based
        mock_reader.return_value.pages = [
            type(
                "Page", (), {"extract_text": lambda: "Some text", "get": lambda x: None}
            ),
            type(
                "Page",
                (),
                {
                    "extract_text": lambda: "",
                    "get": lambda x: (
                        {
                            "/XObject": {
                                "Im0": type(
                                    "XObject",
                                    (),
                                    {"get_object": lambda: {"/Subtype": "/Image"}},
                                )
                            }
                        }
                        if x == "/Resources"
                        else None
                    ),
                },
            ),
        ]

        result = detect_pdf_type(test_pdf)
        assert result["is_pdf"] is True
        assert result["total_pages"] == 2
        assert result["page_types"] == ["text-based", "image-based"]
        assert result["overall_type"] == "mixed"


def test_empty_page_pdf(tmp_path):
    """Test with a PDF containing an empty page."""
    # Create a dummy PDF file
    test_pdf = tmp_path / "empty_page.pdf"
    test_pdf.write_bytes(
        b"""%PDF-1.7
1 0 obj<</Pages 2 0 R/Type/Catalog>>endobj
2 0 obj<</Count 1/Kids[3 0 R]/Type/Pages>>endobj
3 0 obj<</Parent 2 0 R/Type/Page>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000107 00000 n
trailer
<</Root 1 0 R/Size 4>>
startxref
149
%%EOF"""
    )  # Minimal valid PDF content

    with patch("pypdf.PdfReader") as mock_reader:
        # Mock a PDF with an empty page (no text, no images)
        mock_reader.return_value.pages = [
            type("Page", (), {"extract_text": lambda: "", "get": lambda x: None})
        ]

        result = detect_pdf_type(test_pdf)
        assert result["is_pdf"] is True
        assert result["total_pages"] == 1
        assert result["page_types"] == ["text-based"]
        assert result["overall_type"] == "text-based"
