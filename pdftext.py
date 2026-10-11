#!/usr/bin/env python3
"""Extract a protocol PDF to text with '===== pN =====' page markers.

Some sponsors' PDFs (e.g. Gilead) extract with every glyph shifted by -29
("3URWRFRO" = "Protocol"); such pages are decoded automatically.

Usage: python pdftext.py protocol.pdf > protocol.txt
"""
import sys

from pypdf import PdfReader


def unshift(t: str) -> str:
    # ponytail: fixed offset seen in Gilead PDFs; other broken font maps stay garbled
    return "".join(chr(ord(c) + 29) if 3 <= ord(c) <= 93 and c not in "\n " else c for c in t)


def page_text(t: str) -> str:
    fixed = unshift(t)
    return fixed if fixed.lower().count("the") > t.lower().count("the") else t


def pdf_text(path: str) -> str:
    out = []
    for i, p in enumerate(PdfReader(path).pages, 1):
        try:
            t = p.extract_text() or ""
        except Exception:  # noqa: BLE001
            t = ""
        out.append(f"===== p{i} =====\n{page_text(t)}")
    return "\n".join(out)


if __name__ == "__main__":
    assert unshift("3URWRFRO") == "Protocol"
    assert page_text("the plain text") == "the plain text"
    print(pdf_text(sys.argv[1]))
