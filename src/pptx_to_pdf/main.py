import sys
from pathlib import Path
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    MofNCompleteColumn, # Show count like [1/5]
)

# Use absolute imports from the package itself (requires proper installation or PYTHONPATH)
# Or stick to relative imports if running directly via python src/pptx_to_pdf/main.py
from . import ui
from . import converter
from . import merger

# --- Configuration ---
DEFAULT_OUTPUT_SUBDIR = "converted_pdfs" # Subdirectory for converted files
APP_VERSION = "0.1.1" # Keep in sync with pyproject.toml
# --- End Configuration ---

console = Console()

def display_welcome():
    """Displays a welcome panel."""
    console.print(Panel(
        f"[bold cyan]PPTX-to-PDF Converter & Merger[/bold cyan] (v{APP_VERSION})\n"
        "An interactive tool to convert office documents and merge PDFs on Linux.",
        title="[yellow]Welcome![/yellow]",
        border_style="blue"
    ))

def display_summary(source_dir, output_dir, converted_count, merge_input_count, merge_output_file, pages_merged):
    """Displays a summary panel upon successful completion."""
    summary_text = "[bold green]Operation Summary:[/bold green]\n\n"
    summary_text += f"[cyan]Source Directory:[/cyan] {source_dir}\n"
    if converted_count is not None:
        summary_text += f"[cyan]Conversion Output:[/cyan] {output_dir}\n"
        summary_text += f"[cyan]Files Converted:[/cyan] {converted_count}\n"
    else:
        summary_text += "[yellow]Conversion step skipped.[/yellow]\n"

    if merge_output_file:
        summary_text += f"\n[cyan]Files Merged:[/cyan] {merge_input_count}\n"
        summary_text += f"[cyan]Total Pages Merged:[/cyan] {pages_merged}\n"
        summary_text += f"[cyan]Merged Output File:[/cyan] {merge_output_file}\n"
    else:
         summary_text += "\n[yellow]Merging step skipped or failed.[/yellow]\n"

    console.print(Panel(summary_text, title="[blue]Finished[/blue]", border_style="green", padding=(1, 2)))


def run():
    """Main function to run the TUI application."""
    display_welcome()
    final_merge_output_path = None
    final_pages_merged = 0
    final_merge_input_count = 0
    final_converted_count = None # Use None to indicate skipped conversion

    # 1. Check for LibreOffice Dependency
    # ===================================
    if not converter.find_soffice():
        console.print(
            "[bold red]Error:[/bold red] LibreOffice command ('soffice' or 'libreoffice') "
            "not found in your system's PATH."
        )
        console.print("Please install LibreOffice to use the conversion feature:")
        console.print("- sudo apt install libreoffice (Debian/Ubuntu)")
        console.print("- sudo dnf install libreoffice (Fedora)")
        console.print("- sudo pacman -S libreoffice-still (Arch)")
        # Ask if user wants to proceed *only* with merging existing PDFs
        try:
            proceed = ui.inquirer.confirm(
                message="Proceed with PDF merging only (requires existing PDFs)?",
                default=False
            ).execute()
            if not proceed:
                console.print("[yellow]Exiting as requested.[/yellow]")
                sys.exit(1)
            libreoffice_available = False
        except ui.AbortedCommand:
             console.print("\nOperation aborted.")
             sys.exit(1)
    else:
        libreoffice_available = True
        console.print(f"[green]✓ Found LibreOffice command:[/green] {converter.SOFFICE_COMMAND}\n")

    # 2. Get Source Directory
    # =======================
    source_dir = ui.get_directory("Enter the directory containing files to process:")
    if not source_dir:
        sys.exit(1) # Exit if directory selection was aborted or failed
    console.print(f"[cyan]Using source directory:[/cyan] {source_dir}")

    # Define the output directory for converted files (relative to source)
    conversion_output_dir = source_dir / DEFAULT_OUTPUT_SUBDIR

    # 3. Conversion Step (Optional)
    # ==============================
    converted_pdf_files = [] # List to hold paths of newly converted PDFs
    if libreoffice_available:
        console.rule("[bold blue]Step 1: Convert Office Files to PDF[/bold blue]")
        # Find potentially convertible files in the source directory
        convertible_files = converter.get_convertible_files(source_dir)

        if not convertible_files:
            console.print("[yellow]No convertible office files found in this directory.[/yellow]")
            # Ask if user wants to skip conversion and proceed directly to merging
            try:
                 proceed = ui.inquirer.confirm(
                     message="Skip conversion and proceed to merge existing PDFs?",
                     default=True
                 ).execute()
                 if not proceed:
                     console.print("Exiting.")
                     sys.exit(0)
                 # Set count to 0 if skipped this way
                 final_converted_count = 0
            except ui.AbortedCommand:
                 console.print("\nOperation aborted.")
                 sys.exit(1)

        else:
            # Prompt user to select which files to convert
            files_to_convert = ui.select_files(
                convertible_files,
                prompt="Select files to convert to PDF:",
                file_type_label="convertible office files"
            )

            if files_to_convert is None: # User aborted selection
                sys.exit(1)

            if not files_to_convert: # User selected none, but didn't abort
                console.print("[yellow]No files selected for conversion.[/yellow]")
                final_converted_count = 0
                # Ask again if they want to proceed to merge step
                try:
                    proceed = ui.inquirer.confirm(message="Proceed to merge existing PDFs?", default=True).execute()
                    if not proceed:
                        console.print("Exiting.")
                        sys.exit(0)
                except ui.AbortedCommand:
                    console.print("\nOperation aborted.")
                    sys.exit(1)
            else:
                # Proceed with conversion
                console.print(f"\n[cyan]Preparing to convert {len(files_to_convert)} file(s) into:[/cyan] {conversion_output_dir}")
                conversion_output_dir.mkdir(parents=True, exist_ok=True) # Ensure output dir exists

                # Use Rich Progress for visual feedback during conversion
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    MofNCompleteColumn(), # Shows [1/5] etc.
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=console,
                    transient=False, # Keep progress visible after completion
                ) as progress:
                    successful_pdfs, failed_conversions = converter.convert_to_pdf(
                        files_to_convert, conversion_output_dir, progress
                    )
                    converted_pdf_files.extend(successful_pdfs) # Store paths of successfully converted files
                    final_converted_count = len(successful_pdfs) # Store count

                # Report conversion summary
                if failed_conversions:
                    console.print("\n[bold yellow]Conversion Issues:[/bold yellow]")
                    for file, error in failed_conversions:
                        # Error details were printed during conversion by the converter function
                        console.print(f"- [yellow]{file.name}[/yellow]: Conversion failed.")
                if successful_pdfs:
                    console.print(f"\n[green]✓ Successfully converted {len(successful_pdfs)} file(s) to PDF.[/green]")
                elif not failed_conversions: # No successes, no failures (shouldn't happen if files were selected)
                    console.print("[yellow]No files were converted.[/yellow]")

                # Add a small delay for user to read the output
                time.sleep(1)

    else:
        # LibreOffice not available, skipping conversion section
        console.print("\n[yellow]Skipping conversion step as LibreOffice was not found.[/yellow]\n")


    # 4. Merging Step (Optional)
    # ==========================
    console.rule("[bold blue]Step 2: Merge PDF Files[/bold blue]")

    # Determine where to look for PDFs: preferentially the conversion output dir,
    # otherwise the original source dir.
    pdf_scan_dir = conversion_output_dir if conversion_output_dir.exists() and any(conversion_output_dir.iterdir()) else source_dir
    console.print(f"(Scanning for PDFs in: {pdf_scan_dir})")
    all_pdfs_in_dir = ui.find_pdfs(pdf_scan_dir)

    # Create the pool of PDFs available for merging:
    # Combine newly converted PDFs and existing PDFs found in the scan directory.
    # Use dict.fromkeys to preserve order (converted first) and remove duplicates.
    potential_merge_pool = list(dict.fromkeys(converted_pdf_files + all_pdfs_in_dir))
    potential_merge_pool.sort(key=lambda p: p.name) # Sort final pool alphabetically for display

    if not potential_merge_pool:
        console.print(f"[yellow]No PDF files found in '{pdf_scan_dir}' to merge.[/yellow]")
        console.print("\nTool finished.")
        # Display summary even if only conversion happened (or nothing)
        display_summary(source_dir, conversion_output_dir, final_converted_count, 0, None, 0)
        sys.exit(0)

    # Ask user if they want to proceed with merging
    try:
        do_merge = ui.inquirer.confirm(
            message=f"Found {len(potential_merge_pool)} PDF(s). Select files to merge?",
            default=True
        ).execute()
        if not do_merge:
            console.print("\nSkipping merge step as requested.")
            display_summary(source_dir, conversion_output_dir, final_converted_count, 0, None, 0)
            sys.exit(0)
    except ui.AbortedCommand:
        console.print("\nOperation aborted.")
        sys.exit(1)

    # Prompt user to select which PDFs to merge from the pool
    pdfs_to_merge = ui.select_files(potential_merge_pool, "Select PDF files to merge:", "PDF files")

    if pdfs_to_merge is None: # User aborted selection
        sys.exit(1)

    if not pdfs_to_merge: # User selected none, but didn't abort
        console.print("[yellow]No PDF files selected for merging.[/yellow]")
        display_summary(source_dir, conversion_output_dir, final_converted_count, 0, None, 0)
        sys.exit(0)

    # Order the selected PDFs if more than one was chosen
    if len(pdfs_to_merge) > 1:
        ordered_pdfs = ui.order_files(pdfs_to_merge)
        if ordered_pdfs is None: # User aborted ordering
            sys.exit(1)
    else:
        ordered_pdfs = pdfs_to_merge # Use the single selected file directly

    if not ordered_pdfs: # Should not happen if selection worked, but safety check
        console.print("[yellow]No files remaining after ordering step.[/yellow]")
        display_summary(source_dir, conversion_output_dir, final_converted_count, 0, None, 0)
        sys.exit(0)

    console.print("\n[bold]Files will be merged in this order:[/bold]")
    for i, file in enumerate(ordered_pdfs):
        console.print(f"  [cyan]{i + 1}[/cyan]. {file.name}")

    # Get the desired output filename for the merged PDF
    # Default saving location is the original source directory
    output_merge_filename = ui.get_output_filename(default_name=f"{source_dir.name}_merged.pdf")
    if not output_merge_filename: # User aborted filename input
        sys.exit(1)

    final_output_path = source_dir / output_merge_filename
    final_merge_input_count = len(ordered_pdfs) # Store for summary

    console.print(f"\n[cyan]Merging {len(ordered_pdfs)} PDF(s) into:[/cyan] {final_output_path}")

    # Use Rich Progress for merging feedback
    merge_success = False
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False, # Keep progress bar visible
    ) as progress:
        merge_success, final_pages_merged = merger.merge_pdfs(ordered_pdfs, final_output_path, progress)

    if merge_success:
        console.print(f"\n[bold green]✓ Successfully merged PDFs into:[/bold green] {final_output_path}")
        final_merge_output_path = final_output_path # Store for summary
    else:
        console.print("\n[bold red]PDF merging process encountered errors or resulted in an empty file.[/bold red]")
        # Keep final_merge_output_path as None

    # 5. Display Final Summary
    # ========================
    display_summary(source_dir, conversion_output_dir, final_converted_count, final_merge_input_count, final_merge_output_path, final_pages_merged)

    if not final_merge_output_path and do_merge: # If merging was attempted but failed
        sys.exit(1) # Exit with error code

    sys.exit(0) # Exit successfully

# Entry point for the script
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully if it happens outside prompts
        console.print("\n[yellow]Operation interrupted by user. Exiting.[/yellow]")
        sys.exit(1)
    except Exception as e:
        # Catch any unexpected top-level errors
        console.print(f"\n[bold red]An unexpected critical error occurred:[/bold red]")
        console.print_exception(show_locals=False) # Print traceback
        sys.exit(2)