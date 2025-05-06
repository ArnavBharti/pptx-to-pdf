import pytest
from pathlib import Path
from pypdf import PdfReader # Use pypdf imports

# --- Import Test Target ---
# Assuming the package is installed editable or src is in PYTHONPATH
from pptx_to_pdf import merger

# --- Import Test Dependencies ---
from rich.progress import Progress # For type hints/mocking

# --- Import ReportLab for PDF Generation ---
# This import will fail if dev dependencies (including reportlab) aren't installed,
# clearly indicating a setup issue for testing.
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    # Optionally provide a more specific error if reportlab is missing
    pytest.fail(
        "ReportLab not found. Please install development dependencies "
        "using 'uv pip install -e \".[dev]\"' to run tests."
    )


# --- Helper Function ---

def create_dummy_pdf(filepath: Path, text: str = "Dummy Page", page_count: int = 1):
    """Creates a simple PDF file with specified text and page count using ReportLab."""
    c = canvas.Canvas(str(filepath), pagesize=letter)
    for i in range(page_count):
        # Add some content that might differ per page
        page_text = f"{text} - Page {i+1}/{page_count}"
        c.drawString(100, 750, page_text)
        # Add page number at bottom right for easy visual check
        c.drawString(letter[0] - 100, 50, f"Page {i+1}")
        c.showPage() # Finalizes the current page and starts a new one
    c.save() # Saves the PDF file


# --- Test Fixtures ---

@pytest.fixture(scope="function") # Run per test function
def dummy_pdfs(tmp_path):
    """
    Fixture to create dummy PDF files in a temporary directory for testing.
    Uses reportlab (must be installed via dev dependencies).
    """
    pdf_dir = tmp_path / "pdf_sources"
    pdf_dir.mkdir()
    pdf1_path = pdf_dir / "doc_a.pdf"
    pdf2_path = pdf_dir / "doc_b.pdf"
    pdf3_path = pdf_dir / "doc_c_multipage.pdf"

    # Create the dummy PDF files unconditionally using the helper
    create_dummy_pdf(pdf1_path, text="Document A", page_count=1)
    create_dummy_pdf(pdf2_path, text="Document B", page_count=1)
    create_dummy_pdf(pdf3_path, text="Document C", page_count=2) # Create a 2-page PDF

    # Return the paths to the generated files
    return pdf1_path, pdf2_path, pdf3_path

@pytest.fixture
def mock_progress():
    """Fixture to provide a mock Progress object that doesn't render."""
    return Progress(transient=True) # Use transient so it doesn't print during tests


# --- Test Cases ---
# (Test cases remain largely the same as before, relying on the fixture)

def test_merge_two_pdfs_success(tmp_path, dummy_pdfs, mock_progress):
    """Tests successful merging of two single-page PDF files."""
    pdf1, pdf2, _ = dummy_pdfs # Unpack the generated paths
    output_pdf = tmp_path / "merged_two.pdf"
    pdfs_to_merge = [pdf1, pdf2]

    success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)

    assert success is True
    assert output_pdf.exists()
    assert pages_merged == 2 # 1 page + 1 page

    # Verify the merged PDF page count
    try:
        reader = PdfReader(output_pdf)
        assert len(reader.pages) == 2
    except Exception as e:
        pytest.fail(f"Failed to read merged PDF: {e}")

def test_merge_with_multipage_pdf(tmp_path, dummy_pdfs, mock_progress):
    """Tests merging including a multi-page PDF."""
    pdf1, _, pdf3_multi = dummy_pdfs # pdf1 (1 page), pdf3 (2 pages)
    output_pdf = tmp_path / "merged_multi.pdf"
    pdfs_to_merge = [pdf1, pdf3_multi]

    success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)

    assert success is True
    assert output_pdf.exists()
    assert pages_merged == 3 # 1 page + 2 pages

    try:
        reader = PdfReader(output_pdf)
        assert len(reader.pages) == 3
    except Exception as e:
        pytest.fail(f"Failed to read merged PDF: {e}")

def test_merge_order(tmp_path, dummy_pdfs, mock_progress):
    """Tests if the merge order is respected (check content if possible/needed)."""
    pdf1, pdf2, pdf3_multi = dummy_pdfs
    output_pdf = tmp_path / "merged_order.pdf"
    # Merge in order: pdf3_multi (2p), pdf1 (1p)
    pdfs_to_merge = [pdf3_multi, pdf1]

    success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)

    assert success is True
    assert output_pdf.exists()
    assert pages_merged == 3

    # Basic check: verify page count
    try:
        reader = PdfReader(output_pdf)
        assert len(reader.pages) == 3
        # Advanced check: Verify text content of first and last pages based on order
        page1_text = reader.pages[0].extract_text()
        page3_text = reader.pages[2].extract_text()
        assert "Document C - Page 1" in page1_text # First page should be from pdf3
        assert "Document A - Page 1" in page3_text # Last page should be from pdf1
    except Exception as e:
        pytest.fail(f"Failed to read merged PDF or verify order: {e}")


def test_merge_skips_non_existent_file(tmp_path, dummy_pdfs, mock_progress):
    """Tests merging when one specified file doesn't exist. Output should contain only valid file."""
    pdf1, _, _ = dummy_pdfs
    non_existent_pdf = tmp_path / "not_a_real_file.pdf"
    output_pdf = tmp_path / "merged_skip.pdf"

    pdfs_to_merge = [pdf1, non_existent_pdf]

    success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)

    assert success is True # Merge should still succeed with the valid file
    assert output_pdf.exists()
    assert pages_merged == 1 # Only 1 page from pdf1

    # Verify the merged PDF has only pages from the existing file
    try:
        reader = PdfReader(output_pdf)
        assert len(reader.pages) == 1
        page1_text = reader.pages[0].extract_text()
        assert "Document A" in page1_text
    except Exception as e:
        pytest.fail(f"Failed to read merged PDF: {e}")
    # Note: Capturing console output from Progress can be complex.
    # Rely on function behavior (success=True, pages_merged=1) to infer skipping occurred.

def test_merge_empty_input_list(tmp_path, mock_progress):
    """Tests merging with an empty list of input files."""
    output_pdf = tmp_path / "merged_empty.pdf"
    pdfs_to_merge = []

    success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)

    assert success is False # Should fail as no pages were added
    assert not output_pdf.exists() # Output file should not be created
    assert pages_merged == 0

# TODO: Add test for merging potentially corrupted/invalid PDFs
# This might require creating a known bad PDF or mocking pypdf's PdfReader/append methods
# def test_merge_corrupted_pdf(tmp_path, dummy_pdfs, mock_progress):
#     pdf1, _, _ = dummy_pdfs
#     corrupted_pdf_path = tmp_path / "corrupted.pdf"
#     # Create a file that is not a valid PDF
#     with open(corrupted_pdf_path, "w") as f:
#         f.write("This is not a PDF file.")
#     output_pdf = tmp_path / "merged_corrupt.pdf"
#     pdfs_to_merge = [pdf1, corrupted_pdf_path]
#
#     success, pages_merged = merger.merge_pdfs(pdfs_to_merge, output_pdf, mock_progress)
#
#     assert success is True # Should succeed but skip the bad file
#     assert output_pdf.exists()
#     assert pages_merged == 1 # Only page from pdf1
#
#     reader = PdfReader(output_pdf)
#     assert len(reader.pages) == 1
#     assert "Document A" in reader.pages[0].extract_text()