from pathlib import Path
from typing import List, Sequence, Tuple
# Make sure to use pypdf, not the old PyPDF2
from pypdf import PdfWriter, PdfReader
from pypdf.errors import PdfReadError
from rich.progress import Progress

def merge_pdfs(
    pdf_files: Sequence[Path], # Use Sequence for broader type hint (lists, tuples)
    output_path: Path,
    progress: Progress,
) -> Tuple[bool, int]:
    """
    Merges a sequence of PDF files into a single output PDF.

    Args:
        pdf_files: An ordered sequence of Path objects for PDF files to merge.
        output_path: The Path object for the final merged PDF file.
        progress: Rich Progress instance for displaying merging status.

    Returns:
        A tuple containing:
        - bool: True if merging was successful (at least one page added), False otherwise.
        - int: The total number of pages added to the merged document.
    """
    merger = PdfWriter()
    success = False
    pages_added_count = 0
    skipped_files = 0

    # Add a task to the Rich progress bar
    task = progress.add_task("[cyan]Merging PDFs...", total=len(pdf_files))

    try:
        for i, pdf_path in enumerate(pdf_files):
            filename = pdf_path.name
            progress.update(task, description=f"[cyan]Adding: [bold]{filename}[/bold] ({i+1}/{len(pdf_files)})")

            if not pdf_path.is_file():
                progress.console.print(f"[yellow]Warning:[/yellow] Skipping non-existent file: {filename}")
                skipped_files += 1
                progress.update(task, advance=1)
                continue

            try:
                # Open each PDF and append its pages
                # Using strict=False allows handling some slightly corrupted PDFs
                reader = PdfReader(str(pdf_path), strict=False)
                merger.append(reader) # Append all pages from the reader
                pages_added_count += len(reader.pages)

            except PdfReadError as e:
                progress.console.print(f"[bold red]Error reading {filename}:[/] {e}. Skipping this file.")
                skipped_files += 1
            except Exception as e: # Catch other potential pypdf errors
                progress.console.print(f"[bold red]Error adding {filename}:[/] {type(e).__name__}: {e}. Skipping.")
                skipped_files += 1

            progress.update(task, advance=1)

        # Only write the output file if pages were successfully added
        if pages_added_count > 0:
            progress.update(task, description=f"[cyan]Writing final PDF ({pages_added_count} pages)...")
            # Ensure the parent directory exists for the output file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as fout:
                merger.write(fout)
            success = True
            status_message = f"[green]Merging complete ({pages_added_count} pages)."
            if skipped_files > 0:
                status_message += f" [yellow]Skipped {skipped_files} file(s).[/yellow]"
            progress.update(task, description=status_message, completed=len(pdf_files), total=len(pdf_files))
        else:
             progress.console.print("[bold red]Error:[/bold red] No valid PDF pages could be added. Output file not created.")
             success = False
             progress.update(task, description="[red]Merging failed.", completed=len(pdf_files), total=len(pdf_files))

    except Exception as e:
        # Catch unexpected errors during the merging loop or writing phase
        progress.console.print(f"[bold red]Failed to merge PDFs due to unexpected error:[/bold red] {e}")
        success = False
        if not progress.tasks[task].finished:
             progress.update(task, description="[red]Merging failed.", completed=len(pdf_files), total=len(pdf_files))
    finally:
        # Ensure the PdfWriter is closed to release resources
        merger.close()
        # Optional: Stop/remove task if not already finished by success/failure paths
        # if not progress.tasks[task].finished:
        #    progress.stop_task(task)
        #    progress.remove_task(task)

    return success, pages_added_count