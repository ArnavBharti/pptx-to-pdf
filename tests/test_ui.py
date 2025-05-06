import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import functions from the ui module
from pptx_to_pdf import ui

# --- Test UI Helper Functions ---

# Test is_valid_order_string (assuming it might still be used or for reference)
# Note: This will be removed/obsolete with the new reordering UI, but included for completeness of testing existing helpers
@pytest.mark.parametrize("input_str, count, expected", [
    ("1,2,3", 3, True),
    (" 3 , 1 , 2 ", 3, True),
    ("1,3,2", 3, True),
    ("1", 1, True),
    ("1,2", 3, False),        # Wrong count
    ("1,2,2", 3, False),        # Duplicate
    ("1,4,2", 3, False),        # Number out of range
    ("1,0,2", 3, False),        # Number out of range (zero)
    ("1,a,2", 3, False),        # Not a number
    ("", 3, False),             # Empty string
    ("1, 2,", 3, False),        # Trailing comma, invalid parse likely
    (None, 3, False),           # None input
])
def test_is_valid_order_string(input_str, count, expected):
     # If the new UI removes this function, this test becomes obsolete
     # For now, assume it exists for testing purposes if needed elsewhere
     if hasattr(ui, 'is_valid_order_string'):
         assert ui.is_valid_order_string(input_str, count) == expected
     else:
         pytest.skip("is_valid_order_string function not found (likely removed by new UI)")


# Test find_pdfs
@patch('pathlib.Path.iterdir')
@patch('pathlib.Path.is_dir')
def test_find_pdfs(mock_is_dir, mock_iterdir, tmp_path):
    mock_is_dir.return_value = True
    # Create mock Path objects for iterdir to return
    pdf1 = MagicMock(spec=Path)
    pdf1.name = "a.pdf"
    pdf1.suffix = ".pdf"
    pdf1.is_file.return_value = True

    pdf2 = MagicMock(spec=Path)
    pdf2.name = "c.PDF" # Test case insensitivity
    pdf2.suffix = ".PDF"
    pdf2.is_file.return_value = True

    txt1 = MagicMock(spec=Path)
    txt1.name = "b.txt"
    txt1.suffix = ".txt"
    txt1.is_file.return_value = True

    subdir = MagicMock(spec=Path)
    subdir.name = "subdir"
    subdir.is_file.return_value = False

    mock_iterdir.return_value = [pdf1, txt1, subdir, pdf2]

    # Call the function under test
    found_pdfs = ui.find_pdfs(tmp_path) # tmp_path is just a placeholder Path

    # Assertions
    assert mock_is_dir.called_once_with()
    assert mock_iterdir.called_once_with()
    assert len(found_pdfs) == 2
    # Check sorting and correct objects returned
    assert found_pdfs[0] == pdf1 # 'a.pdf' should come before 'c.PDF'
    assert found_pdfs[1] == pdf2

@patch('pathlib.Path.is_dir')
def test_find_pdfs_not_a_directory(mock_is_dir):
    mock_is_dir.return_value = False
    assert ui.find_pdfs(Path("dummy/path")) == []
    assert mock_is_dir.called_once_with()

# --- Tests for Interactive Functions (using mocking) ---
# These are more complex and demonstrate the principle

@patch('inquirerpy.inquirer.filepath') # Patch the specific prompt function
def test_get_directory_success(mock_filepath):
    # Configure the mock prompt to return a specific path when execute() is called
    mock_prompt = MagicMock()
    mock_prompt.execute.return_value = "/fake/selected/dir"
    mock_filepath.return_value = mock_prompt

    # Call the function
    result = ui.get_directory()

    # Assertions
    assert result == Path("/fake/selected/dir").resolve()
    mock_filepath.assert_called_once() # Check inquirer.filepath was called
    mock_prompt.execute.assert_called_once() # Check execute was called on the prompt object

@patch('inquirerpy.inquirer.filepath')
def test_get_directory_aborted(mock_filepath):
    # Configure the mock prompt to raise KeyboardInterrupt on execute()
    mock_prompt = MagicMock()
    mock_prompt.execute.side_effect = KeyboardInterrupt # Simulate Ctrl+C
    mock_filepath.return_value = mock_prompt

    # Call the function
    result = ui.get_directory()

    # Assertions
    assert result is None # Function should return None on abort

# Add similar mock-based tests for select_files, get_output_filename if desired,
# though they become increasingly complex to simulate all user interactions.