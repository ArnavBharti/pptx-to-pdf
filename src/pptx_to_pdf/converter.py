import subprocess
import shutil
import os
from pathlib import Path
from typing import Optional, List, Tuple

from rich.progress import Progress

# --- Configuration ---
# Try to find the LibreOffice command, prioritizing 'soffice'
SOFFICE_COMMAND = shutil.which("soffice") or shutil.which("libreoffice")
# Define supported input formats for conversion
SUPPORTED_CONVERSION_FORMATS = {
    ".pptx", # PowerPoint Open XML Presentation
    ".ppt",  # PowerPoint 97-2003 Presentation
    ".odp",  # OpenDocument Presentation
    ".ppsx", # PowerPoint Open XML Show
    ".pps",  # PowerPoint 97-2003 Show
    # Add other formats LibreOffice can handle if needed:
    # ".key", # Apple Keynote (requires specific LibreOffice build/support)
    # ".vsdx", # Visio Drawing (requires libvisio)
    # ".docx", ".doc", ".odt", # Word/Writer documents
    # ".xlsx", ".xls", ".ods", # Excel/Calc spreadsheets
}
# --- End Configuration ---

def find_soffice() -> Optional[str]:
    """Checks if soffice or libreoffice command exists in PATH."""
    return SOFFICE_COMMAND

def get_convertible_files(input_dir: Path) -> List[Path]:
    """Finds files matching SUPPORTED_CONVERSION_FORMATS in the input directory."""
    convertible_files = []
    if not input_dir.is_dir():
        return []
    # Iterate through items, checking if they are files and have a supported suffix
    for item in input_dir.iterdir():
        if item.is_file() and item.suffix.lower() in SUPPORTED_CONVERSION_FORMATS:
            convertible_files.append(item)
    # Sort alphabetically for consistent user experience
    return sorted(convertible_files)

def convert_to_pdf(
    files_to_convert: List[Path],
    output_dir: Path,
    progress: Progress,
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    """
    Converts a list of office documents to PDF using LibreOffice.

    Args:
        files_to_convert: List of Path objects for files to convert.
        output_dir: Directory Path to save the converted PDF files.
        progress: Rich Progress instance for displaying conversion status.

    Returns:
        A tuple containing:
        - List[Path]: Paths of successfully converted PDF files.
        - List[Tuple[Path, str]]: Tuples of (original_file_path, error_message)
          for conversions that failed.
    """
    if not SOFFICE_COMMAND:
        # This should ideally be checked before calling this function, but acts as a safeguard
        raise FileNotFoundError(
            "LibreOffice ('soffice' or 'libreoffice') command not found in PATH. "
            "Please install LibreOffice and ensure it's in your PATH."
        )

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    successful_pdfs: List[Path] = []
    failed_conversions: List[Tuple[Path, str]] = []

    # Add a task to the Rich progress bar
    task = progress.add_task("[cyan]Converting files...", total=len(files_to_convert))

    for input_file in files_to_convert:
        # Update progress description for the current file
        progress.update(task, description=f"[cyan]Converting: [bold]{input_file.name}[/bold]")

        # Define the expected output PDF path
        output_pdf_path = output_dir / f"{input_file.stem}.pdf"

        # Construct the command for LibreOffice headless conversion
        command = [
            SOFFICE_COMMAND,
            "--headless",            # Run without GUI
            "--convert-to", "pdf",   # Specify PDF as the output format
            "--outdir", str(output_dir.resolve()), # Specify output directory (use absolute path)
            str(input_file.resolve())              # Specify input file (use absolute path)
        ]

        try:
            # Execute the LibreOffice command
            # Set a timeout (e.g., 120 seconds) to prevent indefinite hangs
            result = subprocess.run(
                command,
                capture_output=True, # Capture stdout and stderr
                text=True,           # Decode output as text
                check=False,         # Do not raise exception on non-zero exit code
                timeout=120          # Adjust timeout if needed (seconds)
            )

            # Check for errors: non-zero return code OR 'error' in stderr OR output file missing
            stderr_lower = result.stderr.lower() if result.stderr else ""
            if result.returncode != 0:
                error_msg = f"LibreOffice exited with code {result.returncode}. Stderr: {result.stderr or 'N/A'}"
                failed_conversions.append((input_file, error_msg))
                progress.console.print(f"[bold red]Error converting {input_file.name}:[/] {error_msg[:250]}...") # Print snippet
            elif "error" in stderr_lower:
                 error_msg = f"LibreOffice reported an error. Stderr: {result.stderr}"
                 failed_conversions.append((input_file, error_msg))
                 progress.console.print(f"[bold red]Error converting {input_file.name}:[/] {error_msg[:250]}...") # Print snippet
            elif not output_pdf_path.exists():
                 # Sometimes soffice exits 0 but fails silently or creates no output
                 error_msg = "Conversion process finished but output PDF was not found."
                 failed_conversions.append((input_file, error_msg))
                 progress.console.print(f"[bold red]Error converting {input_file.name}:[/] {error_msg}")
            else:
                # Conversion successful
                successful_pdfs.append(output_pdf_path)
                progress.update(task, description=f"[green]Converted: [bold]{input_file.name}[/bold]")

        except FileNotFoundError:
             # This specific error means SOFFICE_COMMAND itself wasn't found
             # Should be caught earlier, but good practice to handle
             error_msg = f"'{SOFFICE_COMMAND}' command not found during execution."
             failed_conversions.append((input_file, error_msg))
             progress.console.print(f"[bold red]CRITICAL ERROR:[/bold red] {error_msg}")
             # Maybe re-raise or handle more severely as it affects all conversions
        except subprocess.TimeoutExpired:
            error_msg = f"Conversion timed out after 120 seconds."
            failed_conversions.append((input_file, error_msg))
            progress.console.print(f"[bold red]Timeout converting {input_file.name}:[/] {error_msg}")
        except Exception as e:
            # Catch any other unexpected exceptions during subprocess execution
            error_msg = f"An unexpected error occurred: {type(e).__name__}: {e}"
            failed_conversions.append((input_file, error_msg))
            progress.console.print(f"[bold red]Unexpected error converting {input_file.name}:[/] {error_msg}")

        # Advance the progress bar regardless of success or failure
        progress.update(task, advance=1)

    # Finalize the progress bar task
    progress.update(task, description="[green]Conversion complete.", completed=len(files_to_convert), total=len(files_to_convert))
    # Optional: Keep the progress bar visible for a moment or remove immediately
    # progress.stop_task(task)
    # progress.remove_task(task)

    return successful_pdfs, failed_conversions