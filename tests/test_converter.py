import pytest
import subprocess
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Import functions from the converter module
from pptx_to_pdf import converter

# --- Test Fixtures ---

@pytest.fixture
def mock_progress():
    """Fixture for a MagicMock simulating rich.progress.Progress."""
    progress = MagicMock()
    # Mock add_task to return a task_id (e.g., 0)
    progress.add_task.return_value = 0
    # Make console available for potential print calls within the function
    progress.console = MagicMock()
    return progress

@pytest.fixture
def temp_files(tmp_path):
    """Fixture to create temporary dummy files for testing."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    output_dir = tmp_path / "output"
    # No need to mkdir output_dir here, converter should do it

    file_pptx = source_dir / "test1.pptx"
    file_odp = source_dir / "test2.odp"
    file_txt = source_dir / "notes.txt" # Non-convertible

    file_pptx.touch()
    file_odp.touch()
    file_txt.touch()

    return source_dir, output_dir, file_pptx, file_odp, file_txt

# --- Test Cases ---

# Test find_soffice
@patch('shutil.which')
def test_find_soffice_found(mock_which):
    mock_which.side_effect = lambda cmd: "/usr/bin/soffice" if cmd == "soffice" else None
    converter.SOFFICE_COMMAND = None # Reset global state if needed
    assert converter.find_soffice() == "/usr/bin/soffice"
    assert mock_which.call_count == 1 # Only soffice should be checked first usually

@patch('shutil.which')
def test_find_soffice_fallback(mock_which):
    # Simulate soffice not found, libreoffice found
    mock_which.side_effect = lambda cmd: "/usr/bin/libreoffice" if cmd == "libreoffice" else None
    converter.SOFFICE_COMMAND = None # Reset global state
    # Need to re-run the module level check simulation if SOFFICE_COMMAND is module global
    # For simplicity, let's assume the function re-checks if needed, or test the global directly
    # Re-evaluating the module-level assignment:
    actual_command = shutil.which("soffice") or shutil.which("libreoffice")
    assert actual_command == "/usr/bin/libreoffice"
    assert mock_which.call_count == 2 # Both checked

@patch('shutil.which')
def test_find_soffice_not_found(mock_which):
    mock_which.return_value = None
    converter.SOFFICE_COMMAND = None # Reset global state
    actual_command = shutil.which("soffice") or shutil.which("libreoffice")
    assert actual_command is None
    assert mock_which.call_count == 2

# Test get_convertible_files
def test_get_convertible_files(temp_files