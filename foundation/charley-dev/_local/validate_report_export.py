"""Offline PDF error screening. A clean screen still requires visual review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def screen_pages(pages: list[str], expected_pages: int) -> dict:
    errors = []
    unreadable = []
    signatures = ("unabletoloadmodel", "unabletoopenthisreport",
                  "errorfetchingdata", "couldn'tloadthedata", "somethingwentwrong")
    for number, text in enumerate(pages, 1):
        compact = "".join(text.lower().split()).replace("’", "'")
        if not compact:
            unreadable.append(number)
        if any(signature in compact for signature in signatures):
            errors.append(number)
    return {
        "status": "FAIL" if errors or unreadable or len(pages) != expected_pages else "REVIEW_REQUIRED",
        "page_count": len(pages), "expected_visible_pages": expected_pages,
        "error_pages": errors, "unreadable_pages": unreadable,
        "limitation": "Text screening cannot certify layout, data correctness, hidden pages, or offscreen table rows.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--expected-pages", type=int, required=True)
    args = parser.parse_args()
    from pypdf import PdfReader
    result = screen_pages([page.extract_text() or "" for page in PdfReader(args.pdf).pages], args.expected_pages)
    result["pdf_sha256"] = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    print(json.dumps(result, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
