from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "project-dossier.md"
OUTPUT = ROOT / "docs" / "project-dossier.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
MARGIN = 54
FONT_SIZE = 11
LINE_HEIGHT = 15
MAX_WIDTH_CHARS = 88


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_markdown(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.rstrip()
        if not stripped:
            lines.append("")
            continue

        if stripped.startswith("## "):
            lines.append("")
            lines.append(stripped[3:].upper())
            lines.append("")
            continue

        if stripped.startswith("### "):
            lines.append(stripped[4:])
            continue

        if stripped.startswith("- "):
            prefix = "- "
            body = stripped[2:]
            wrapped = textwrap.wrap(body, width=MAX_WIDTH_CHARS - len(prefix)) or [body]
            for index, part in enumerate(wrapped):
                lines.append((prefix if index == 0 else "  ") + part)
            continue

        if stripped[:2].isdigit() and stripped[1:3] == ". ":
            prefix = stripped[:3]
            body = stripped[3:]
            wrapped = textwrap.wrap(body, width=MAX_WIDTH_CHARS - len(prefix)) or [body]
            for index, part in enumerate(wrapped):
                lines.append((prefix if index == 0 else "   ") + part)
            continue

        wrapped = textwrap.wrap(stripped, width=MAX_WIDTH_CHARS) or [stripped]
        lines.extend(wrapped)
    return lines


def paginate(lines: list[str]) -> list[list[str]]:
    usable_height = PAGE_HEIGHT - (MARGIN * 2)
    lines_per_page = usable_height // LINE_HEIGHT
    pages: list[list[str]] = []
    for index in range(0, len(lines), lines_per_page):
        pages.append(lines[index:index + lines_per_page])
    return pages or [[]]


def build_page_stream(lines: list[str], page_number: int, page_count: int) -> bytes:
    commands = ["BT", f"/F1 {FONT_SIZE} Tf"]
    y = PAGE_HEIGHT - MARGIN
    for line in lines:
        safe = escape_pdf_text(line)
        commands.append(f"1 0 0 1 {MARGIN} {y} Tm ({safe}) Tj")
        y -= LINE_HEIGHT
    footer = f"InvoiceBot Project Dossier  |  Page {page_number} of {page_count}"
    commands.append(f"1 0 0 1 {MARGIN} {MARGIN - 16} Tm ({escape_pdf_text(footer)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    return stream


def generate_pdf(text: str, output_path: Path) -> None:
    wrapped_lines = wrap_markdown(text)
    pages = paginate(wrapped_lines)

    objects: list[bytes] = []

    def add_object(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    content_ids: list[int] = []
    pages_parent_id_placeholder = len(objects) + 2

    for page_index, page_lines in enumerate(pages, start=1):
        stream = build_page_stream(page_lines, page_index, len(pages))
        content_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        content_ids.append(content_id)
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_parent_id_placeholder} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_id = add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii"))
    catalog_id = add_object(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))

    result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode("ascii"))
        result.extend(obj)
        result.extend(b"\nendobj\n")

    xref_offset = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    result.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    output_path.write_bytes(result)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    generate_pdf(text, OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
