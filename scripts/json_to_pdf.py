"""
scripts/json_to_pdf.py

CLI tool to convert a Planorai JSON report into a formatted PDF document.

Usage:
    python scripts/json_to_pdf.py <input_report.json> [output_report.pdf]
    python scripts/json_to_pdf.py --input <input_report.json> --output <output_report.pdf>
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.pdf_generator import generate_pdf_from_json_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Planorai JSON plan to a formatted PDF blueprint."
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to the JSON report file (e.g., student-knowledge-assistant.json)",
    )
    parser.add_argument(
        "pdf_file",
        nargs="?",
        help="Optional destination path for the output PDF (defaults to same name with .pdf)",
    )
    parser.add_argument(
        "-i", "--input",
        dest="opt_input",
        help="Alternative flag to specify input JSON file",
    )
    parser.add_argument(
        "-o", "--output",
        dest="opt_output",
        help="Alternative flag to specify output PDF file",
    )

    args = parser.parse_args()
    input_path = args.opt_input or args.json_file
    output_path = args.opt_output or args.pdf_file

    if not input_path:
        # Search for any recent report JSON in current or data directory
        candidates = list(Path(".").glob("*.json"))
        # Exclude package files
        candidates = [c for c in candidates if c.name not in {"package.json", "package-lock.json", "tsconfig.json"}]
        if candidates:
            print("No file specified. Found potential report JSON files in workspace:")
            for idx, c in enumerate(candidates, 1):
                print(f"  [{idx}] {c}")
            print("\nPlease provide the file path:\n  python scripts/json_to_pdf.py <filename.json>")
            return
        else:
            parser.print_help()
            print("\nError: Please provide the path to your JSON report file.")
            sys.exit(1)

    src = Path(input_path)
    if not src.exists():
        print(f"Error: File '{src}' does not exist.")
        sys.exit(1)

    try:
        print(f"Converting '{src}' to PDF...")
        dest = generate_pdf_from_json_file(src, output_path)
        size_kb = dest.stat().st_size / 1024
        print(f"[SUCCESS] PDF generated successfully: {dest.resolve()} ({size_kb:.1f} KB)")
    except Exception as exc:
        print(f"[ERROR] Failed to generate PDF: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
