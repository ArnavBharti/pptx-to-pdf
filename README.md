# PPTX-to-PDF: Office Document Converter & PDF Merger (Linux TUI)

**PPTX-to-PDF:** An interactive TUI tool for Linux to convert office documents (.pptx, .odp, .ppt, etc.) to PDF using LibreOffice, and optionally merge multiple PDFs into a single, ordered file.

It provides a simple command-line interface to select files for conversion and/or merging, define the order for merged documents, and name the output file.

## Features

* **Interactive TUI:** Uses `inquirerpy` for easy file selection and ordering in the terminal.
* **Office Format Conversion:** Converts `.pptx`, `.ppt`, `.odp`, and potentially other formats supported by LibreOffice to PDF.
* **PDF Merging:** Combines multiple PDF files into one.
* **Custom Order:** Allows specifying the exact order of files in the merged PDF.
* **LibreOffice Backend:** Leverages your existing LibreOffice installation (`soffice` command) for reliable conversions.
* **Dependency Check:** Verifies if LibreOffice command is found in PATH.
* **Selective Workflow:** Run conversion, merging, or both. Skip conversion to only merge existing PDFs.
* **Progress Display:** Uses `rich` for visual feedback during conversion and merging.
* **Error Handling:** Reports issues like missing files or conversion failures.

## Requirements

* **Linux Operating System:** Designed and tested for Linux environments.
* **Python:** Version 3.8 or newer.
* **uv (Recommended):** Modern, fast Python package installer and virtual environment manager. Installation instructions use `uv`. Get it from [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv). (If you prefer `pip` and `venv`, adapt the commands).
* **LibreOffice:** The core conversion capability relies on LibreOffice being installed and the `soffice` (or `libreoffice`) command being accessible in your system's PATH.
    * Install on Debian/Ubuntu: `sudo apt update && sudo apt install libreoffice`
    * Install on Fedora: `sudo dnf install libreoffice`
    * Install on Arch Linux: `sudo pacman -S libreoffice-still` or `libreoffice-fresh`
 
## Global Installation (Usage)

While this project uses `uv` and virtual environments for development, if you want to install `pptx-to-pdf` as a command-line tool accessible from anywhere on your system, using `pipx` is the recommended method:

1.  **Install pipx:** Follow the instructions at [https://pipx.pypa.io/stable/installation/](https://pipx.pypa.io/stable/installation/) or use your system package manager (e.g., `sudo apt install pipx`).
2.  **Ensure pipx paths are configured:**
    ```bash
    pipx ensurepath
    ```
    *(You may need to restart your shell after this.)*
3.  **Install pptx-to-pdf:**
    * **From Git:**
        ```bash
        pipx install git+https://github.com/arnavbharti/pptx-to-pdf.git
        ```
    * **From Local Source (run from project root):**
        ```bash
        pipx install ./
        ```

Now you can run `pptx-to-pdf` directly from any terminal.

**Note:** Even when installed globally, `pptx-to-pdf` still requires **LibreOffice** to be installed separately on your system for file conversions to work.

## Installation

**Using `uv` (Recommended):**

1.  **Clone the Repository:** (Replace with the correct URL)
    ```bash
    # Replace arnavbharti with the actual owner if forked/cloned
    git clone [https://github.com/arnavbharti/pptx-to-pdf.git](https://github.com/arnavbharti/pptx-to-pdf.git)
    cd pptx-to-pdf
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    # Create the environment (e.g., named .venv)
    uv venv .venv
    # Activate it (syntax for Linux/macOS bash/zsh)
    source .venv/bin/activate
    ```
    *(On Windows, activation might be `.venv\Scripts\activate`)*

3.  **Install the Package:**
    ```bash
    uv pip install .
    ```
    *This makes the `pptx-to-pdf` command available in your activated environment.*

## Usage

1.  **Ensure LibreOffice is installed and accessible.**
2.  **Activate your virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
3.  **Run the tool:**
    ```bash
    pptx-to-pdf
    ```
4.  **Follow the interactive TUI prompts** to select directories, files, specify order, and name the output. Converted files go to `converted_pdfs/` subdirectory; the final merged PDF is saved in the source directory.

---

## Development & Contributing

Contributions are welcome! If you'd like to develop `pptx-to-pdf` or contribute changes, follow these steps:

**1. Development Setup:**

* **Fork & Clone:** Fork the repository on GitHub and clone your fork locally.
    ```bash
    # Replace YOUR_USERNAME with your GitHub username
    git clone [https://github.com/YOUR_USERNAME/pptx-to-pdf.git](https://github.com/YOUR_USERNAME/pptx-to-pdf.git)
    cd pptx-to-pdf
    ```
* **Create Virtual Environment:** (As described in Installation)
    ```bash
    uv venv .venv
    source .venv/bin/activate
    ```
* **Install in Editable Mode with Dev Dependencies:** This installs the package so your code changes are reflected immediately, along with tools for testing, linting, and formatting.
    ```bash
    uv pip install -e ".[dev]"
    ```

**2. Making Changes:**

* **Create a Branch:** Create a new branch for your feature or bug fix.
    ```bash
    git checkout -b my-feature-or-fix
    ```
* **Write Code:** Implement your changes or fix the bug.
* **Add Tests:** Write tests for any new functionality or to cover bug fixes (place them in the `tests/` directory).

**3. Running Checks:**

Before committing, ensure your code meets quality standards:

* **Run Tests:**
    ```bash
    pytest tests/
    ```
    *(Ensure any necessary dummy files or test setup is in place, see `tests/test_merger.py`)*
* **Check Formatting (Black):**
    ```bash
    black --check src/ tests/
    ```
* **Apply Formatting (Black):**
    ```bash
    black src/ tests/
    ```
* **Check Linting (Ruff):**
    ```bash
    ruff check src/ tests/
    ```
* **Apply Linting Fixes (Ruff):** (Use with caution, review changes)
    ```bash
    ruff check src/ tests/ --fix
    ```
    *(You can also configure `ruff format` if you prefer it over `black`)*

**4. Contribution Workflow:**

* **Commit Changes:** Commit your work with clear, descriptive messages.
    ```bash
    git add .
    git commit -m "feat: Add feature X" -m "Detailed description of changes..."
    # Or: git commit -m "fix: Resolve issue Y" -m "Details..."
    ```
* **Push to Fork:** Push your branch to your GitHub fork.
    ```bash
    git push origin my-feature-or-fix
    ```
* **Open Pull Request:** Go to the original repository on GitHub and open a Pull Request (PR) from your branch to the main branch of the original repository.
* **Describe PR:** Provide a clear description of your changes in the PR. Link to any relevant issues (e.g., "Closes #123").
* **Discuss:** Respond to any feedback or questions during the review process.

*Tip: For significant changes, consider opening an issue first to discuss the proposed changes.*

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
