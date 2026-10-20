"""Extract course PDFs into Markdown an AI agent (Claude Code or Codex) can read before writing a study guide.

Usage (from the STUDY folder):
    .venv\\Scripts\\python tools\\extract_pdf.py <pdf file or folder> [--out work\\extract] [--images]

For every PDF it writes <out>/<pdf name>.md with a "## Page N" section per page: the text, then any tables as
pipe rows. Pages with almost no text are listed at the end (scanned slides, diagrams). With --images every page
is also rendered to <out>/<pdf name>/page-NN.png, so the agent can look at diagrams and read scanned pages.
Uses only pdfplumber and pypdfium2, which setup.cmd already installs.
"""
import argparse
from pathlib import Path

import pdfplumber


def extract(pdf, out, images=False):
    out.mkdir(parents=True, exist_ok=True)
    lines, low = [f"# {pdf.name}"], []
    with pdfplumber.open(pdf) as doc:
        for i, page in enumerate(doc.pages, 1):
            text = (page.extract_text() or "").strip()
            lines += ["", f"## Page {i}", "", text or "[no text layer: scanned page or image only, see the page image]"]
            for table in page.extract_tables() or []:
                rows = [" | ".join((c or "").replace("\n", " ").strip() for c in r) for r in table if r and any(r)]
                if rows:
                    lines += ["", *[f"| {r} |" for r in rows]]
            if len(text) < 40:
                low.append(i)
    md = out / f"{pdf.stem}.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if images:
        import pypdfium2 as pdfium

        folder = out / pdf.stem
        folder.mkdir(exist_ok=True)
        doc = pdfium.PdfDocument(str(pdf))
        for i in range(len(doc)):
            doc[i].render(scale=150 / 72).to_pil().save(folder / f"page-{i + 1:02d}.png")
    return md, low


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source", help="a PDF file or a folder (searched recursively)")
    ap.add_argument("--out", default="work/extract", help="output folder (default: work/extract)")
    ap.add_argument("--images", action="store_true", help="also render every page to PNG")
    a = ap.parse_args()
    src, out = Path(a.source), Path(a.out)
    pdfs = sorted(src.rglob("*.pdf")) if src.is_dir() else [src]
    if not pdfs:
        raise SystemExit(f"No PDFs found in {src}")
    for pdf in pdfs:
        try:
            md, low = extract(pdf, out, a.images)
        except Exception as e:  # one broken PDF must not stop the rest of the course
            print(f"FAILED  {pdf}: {type(e).__name__}: {e}")
            continue
        note = f"; little or no text on pages {low}, look at the page images" if low else ""
        print(f"ok      {pdf.name} -> {md}{note}")


if __name__ == "__main__":
    main()
