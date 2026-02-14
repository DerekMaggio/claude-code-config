#!/usr/bin/env python3
"""Filter CSV files to keep only specified columns."""

import csv
import sys
from pathlib import Path


def load_columns_to_keep(columns_file: Path) -> list[str]:
    """Load column names from file, one per line."""
    with open(columns_file) as f:
        return [line.strip() for line in f if line.strip()]


def filter_csv(input_file: Path, output_file: Path, columns: list[str]) -> None:
    """Filter CSV to keep only specified columns."""
    with open(input_file, newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Validate columns exist
        missing = [col for col in columns if col not in reader.fieldnames]
        if missing:
            print(f"Warning: Columns not found in CSV: {missing}", file=sys.stderr)

        valid_columns = [col for col in columns if col in reader.fieldnames]

        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=valid_columns)
            writer.writeheader()

            for row in reader:
                filtered_row = {col: row[col] for col in valid_columns}
                writer.writerow(filtered_row)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.csv> [output.csv]", file=sys.stderr)
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file.with_stem(f"{input_file.stem}_filtered")

    script_dir = Path(__file__).parent
    columns_file = script_dir / "COLUMNS_TO_KEEP"

    if not columns_file.exists():
        print(f"Error: {columns_file} not found", file=sys.stderr)
        sys.exit(1)

    columns = load_columns_to_keep(columns_file)
    filter_csv(input_file, output_file, columns)
    print(f"Filtered CSV written to: {output_file}")


if __name__ == "__main__":
    main()
