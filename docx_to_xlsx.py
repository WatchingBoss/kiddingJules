import argparse
import sys
import docx
from openpyxl import Workbook
import os

def convert_docx_tables_to_xlsx(input_docx: str, output_xlsx: str) -> None:
    """
    Converts all tables in a docx file to an xlsx file, where each table gets its own sheet.
    """
    try:
        doc = docx.Document(input_docx)
    except Exception as e:
        print(f"Error opening docx file {input_docx}: {e}", file=sys.stderr)
        sys.exit(1)

    tables = doc.tables
    if not tables:
        print(f"No tables found in {input_docx}")
        wb = Workbook()
        wb.save(output_xlsx)
        return

    wb = Workbook()
    # Remove the default sheet created by openpyxl
    wb.remove(wb.active)

    for i, table in enumerate(tables, start=1):
        # Create a new sheet for each table
        sheet_title = f"Table_{i}"
        ws = wb.create_sheet(title=sheet_title)

        for r_idx, row in enumerate(table.rows, start=1):
            for c_idx, cell in enumerate(row.cells, start=1):
                # Clean up the text by replacing tabs and newlines if desired,
                # but docx might have newlines in cells which excel supports.
                cell_text = cell.text.strip()
                ws.cell(row=r_idx, column=c_idx, value=cell_text)

    try:
        wb.save(output_xlsx)
        print(f"Successfully converted {len(tables)} tables to {output_xlsx}")
    except Exception as e:
        print(f"Error saving xlsx file {output_xlsx}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert docx tables to xlsx.")
    parser.add_argument("input", help="Input docx file path")
    parser.add_argument("output", help="Output xlsx file path")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} does not exist.", file=sys.stderr)
        sys.exit(1)

    convert_docx_tables_to_xlsx(args.input, args.output)

if __name__ == "__main__":
    main()
