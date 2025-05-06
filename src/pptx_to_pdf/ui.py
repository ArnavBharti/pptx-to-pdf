from typing import List, Optional, Sequence
from pathlib import Path
import sys
import copy # Needed for managing choices list

# Keep the imports as they are (assuming lowercase 'inquirerpy' worked)
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
# from inquirerpy.exceptions import AbortedCommand # REMOVED - Doesn't exist in v0.3.4

from rich.console import Console
from rich.panel import Panel

console = Console()

# --- Directory Selection ---
# (get_directory function remains as corrected in previous step)
def get_directory(prompt: str = "Enter the directory containing your files:", default: str = ".") -> Optional[Path]:
    """Prompts user for a directory path using inquirerpy."""
    try:
        path_str = inquirer.filepath(
            message=prompt,
            default=default,
            only_directories=True,
            validate=lambda p: Path(p).is_dir(),
            invalid_message="Please select a valid directory.",
        ).execute()
        if path_str is None:
             console.print("\n[yellow]Operation cancelled or no input provided.[/yellow]")
             return None
        return Path(path_str).resolve()
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user (Ctrl+C).")
        return None
    except Exception as e:
        console.print(f"[bold red]Error getting directory:[/bold red] {e}")
        return None

# --- File Selection ---
# (select_files function remains as corrected in previous step)
def select_files(
    files: List[Path],
    prompt: str = "Select files to process:",
    file_type_label: str = "files"
) -> Optional[List[Path]]:
    """Allows user to select multiple files from a list using checkbox prompt."""
    if not files:
        console.print(f"[yellow]No {file_type_label} found to select.[/yellow]")
        return []

    choices = [Choice(value=file, name=file.name) for file in files]
    try:
        selected_files = inquirer.checkbox(
            message=prompt,
            choices=choices,
            instruction="(Use Spacebar to select/deselect, Enter to confirm)",
            border=True,
        ).execute()
        if selected_files is None: # Check for explicit None return
            console.print("\n[yellow]Operation cancelled or no input provided.[/yellow]")
            return None
        return selected_files
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user (Ctrl+C).")
        return None
    except Exception as e:
         console.print(f"[bold red]Error during file selection:[/bold red] {e}")
         return None

# --- Output Filename Input ---
# (get_output_filename function remains as corrected in previous step)
def get_output_filename(default_name: str = "merged_output.pdf") -> Optional[str]:
    """Prompts user for the output filename for the merged PDF."""
    try:
        filename = inquirer.text(
            message="Enter the desired name for the merged PDF file:",
            default=default_name,
            validate=lambda name: len(name.strip()) > 0 and name.lower().endswith(".pdf"),
            invalid_message="Filename cannot be empty and must end with .pdf",
        ).execute()
        if filename is None: # Check for explicit None return
            console.print("\n[yellow]Operation cancelled or no input provided.[/yellow]")
            return None
        return filename.strip()
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user (Ctrl+C).")
        return None
    except Exception as e:
        console.print(f"[bold red]Error getting output filename:[/bold red] {e}")
        return None


# --- File Ordering (NEW Interactive Version) ---
def order_files(files: Sequence[Path]) -> Optional[List[Path]]:
    """
    Allows the user to interactively specify the merge order by picking files one by one.

    Args:
        files: The sequence (list/tuple) of Path objects selected for merging.

    Returns:
        A list of Path objects in the user-specified order, or None if aborted.
        Returns the original list if 0 or 1 file is provided.
    """
    if not files or len(files) < 2:
        # No ordering needed for 0 or 1 file
        return list(files)

    console.print(Panel(
        f"You selected {len(files)} files to merge. Please specify the desired order.",
        title="[bold blue]Specify Merge Order[/bold blue]",
        border_style="blue"
        ))

    ordered_files: List[Path] = []
    # Work with a copy so we can remove items without affecting the original list
    # Create choices mapping display name back to Path object
    remaining_choices_map = {f.name: f for f in files}

    try:
        for i in range(len(files)):
            position = i + 1
            # Get the names of the files still available to choose from
            available_display_names = sorted(list(remaining_choices_map.keys()))

            if not available_display_names: # Should not happen if logic is correct
                console.print("[bold red]Error:[/bold red] No more choices available unexpectedly.")
                return None

            selected_display_name = inquirer.select(
                message=f"Select file for position #{position}:", # <-- REMOVED RICH TAGS
                choices=available_display_names,
                # Use fuzzy search if list is long? Maybe later enhancement.
                # fuzzy=len(available_display_names) > 10,
                border=True,
                # cycle=False,
            ).execute()

            # Handle potential cancellation/abortion
            if selected_display_name is None:
                console.print("\n[yellow]Operation cancelled or no input provided during ordering.[/yellow]")
                return None # Abort the whole ordering process

            # Add the corresponding Path object to the ordered list
            selected_file_path = remaining_choices_map[selected_display_name]
            ordered_files.append(selected_file_path)

            # Remove the selected file from the available choices for the next iteration
            del remaining_choices_map[selected_display_name]

            # Optional: Show progress
            console.print(f"  [green]✓[/green] Position {position}: {selected_display_name}")

        # Verify we got the correct number of files
        if len(ordered_files) == len(files):
            console.print("\n[green]File order confirmed.[/green]")
            return ordered_files
        else:
            # This indicates a logic error in the loop
            console.print("[bold red]Error:[/bold red] Ordering process failed unexpectedly.")
            return None

    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user (Ctrl+C).")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during ordering:[/bold red] {e}")
        return None

# --- (is_valid_order_string function is now removed/obsolete) ---

# --- find_pdfs function remains the same ---
def find_pdfs(input_dir: Path) -> List[Path]:
    """Finds PDF files in the specified directory."""
    pdf_files = []
    if not input_dir.is_dir():
        return []
    for item in input_dir.iterdir():
        if item.is_file() and item.suffix.lower() == ".pdf":
            pdf_files.append(item)
    return sorted(pdf_files)