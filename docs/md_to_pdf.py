"""Offline Markdown -> PDF for the DealFlow readiness report (pure-python, $0, no system libs).

Usage: python md_to_pdf.py <input.md> <output.pdf> "<Document Title>"
"""
import sys
import markdown
from xhtml2pdf import pisa

CSS = """
@page { size: letter; margin: 1.6cm 1.6cm 1.8cm 1.6cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 8.6pt; color: #0f172a; line-height: 1.4; }
h1 { font-size: 17pt; color: #0f172a; border-bottom: 2px solid #b45309; padding-bottom: 4px; margin: 0 0 8px 0; }
h2 { font-size: 12pt; color: #b45309; margin: 14px 0 4px 0; }
h3 { font-size: 10pt; color: #0f172a; margin: 10px 0 3px 0; }
p { margin: 4px 0; }
code, pre { font-family: Courier, monospace; font-size: 7.4pt; background: #f1f5f9; color: #0f172a; }
pre { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; white-space: pre-wrap; }
table { width: 100%; border-collapse: collapse; margin: 6px 0; }
th { background: #0f172a; color: #ffffff; font-size: 7.6pt; text-align: left; padding: 4px 6px; border: 0.5px solid #0f172a; }
td { font-size: 7.6pt; padding: 4px 6px; border: 0.5px solid #cbd5e1; vertical-align: top; }
tr:nth-child(even) td { background: #f8fafc; }
hr { border: 0; border-top: 1px solid #cbd5e1; margin: 10px 0; }
ul, ol { margin: 4px 0 4px 14px; }
li { margin: 2px 0; }
strong { color: #0f172a; }
"""


def _sanitize(text: str) -> str:
    """Map glyphs the base PDF fonts cannot draw to ASCII (keeps the .md pretty)."""
    repl = {
        "\u2192": "->", "\u2190": "<-", "\u21c4": "<->", "\u2194": "<->",
        "\u25b2": "^", "\u25bc": "v", "\u25ba": ">", "\u25c4": "<",
        "\u2500": "-", "\u2502": "|",
        "\u250c": "+", "\u2510": "+", "\u2514": "+", "\u2518": "+",
        "\u251c": "+", "\u2524": "+", "\u252c": "+", "\u2534": "+", "\u253c": "+",
        "\u2713": "[x]", "\u274c": "[!]", "\u2705": "[ok]", "\u2022": "-",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def convert(md_path: str, pdf_path: str, title: str) -> None:
    with open(md_path, "r", encoding="utf-8") as f:
        text = _sanitize(f.read())
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "nl2br"]
    )
    html = (
        f"<html><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    with open(pdf_path, "w+b") as out:
        result = pisa.CreatePDF(src=html, dest=out)
    if result.err:
        raise SystemExit(f"PDF generation failed with {result.err} error(s)")
    print("WROTE", pdf_path)


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2], sys.argv[3])
