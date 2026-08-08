"""
Robust HTML to Clean Markdown Converter.

Converts HTML layouts (including Sarvam AI OCR HTML outputs, tables, and CSS blocks)
into clean, beautiful Markdown format.
"""
from __future__ import annotations

import html
import re


def convert_html_to_markdown(raw_html: str) -> str:
    """
    Convert raw HTML string into clean Markdown.
    Converts HTML tables into Markdown tables, headers into # MD headers,
    and removes all CSS/HTML tags.
    """
    if not raw_html or not raw_html.strip():
        return ""

    if "<" not in raw_html or ">" not in raw_html:
        return raw_html.strip()

    text = raw_html

    # 1. Remove <style>...</style>, <script>...</script>, <head>...</head> completely
    text = re.sub(r"(?is)<style\b[^>]*>.*?</style>", "", text)
    text = re.sub(r"(?is)<script\b[^>]*>.*?</script>", "", text)
    text = re.sub(r"(?is)<head\b[^>]*>.*?</head>", "", text)

    # 2. Convert HTML Tables to Markdown Tables
    def _convert_table(match: re.Match) -> str:
        table_html = match.group(0)
        rows = re.findall(r"(?is)<tr\b[^>]*>(.*?)</tr>", table_html)
        if not rows:
            return ""

        md_rows = []
        for idx, row in enumerate(rows):
            cells = re.findall(r"(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>", row)
            clean_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if not clean_cells or all(c == "" for c in clean_cells):
                continue
            md_row = "| " + " | ".join(clean_cells) + " |"
            md_rows.append(md_row)

            # Insert separator header for the first row
            if idx == 0:
                sep = "| " + " | ".join(["---"] * len(clean_cells)) + " |"
                md_rows.append(sep)

        return "\n\n" + "\n".join(md_rows) + "\n\n"

    text = re.sub(r"(?is)<table\b[^>]*>.*?</table>", _convert_table, text)

    # 3. Convert Headers & Format Tags
    text = re.sub(r"(?is)<h1\b[^>]*>(.*?)</h1>", r"\n\n# \1\n\n", text)
    text = re.sub(r"(?is)<h2\b[^>]*>(.*?)</h2>", r"\n\n## \1\n\n", text)
    text = re.sub(r"(?is)<h3\b[^>]*>(.*?)</h3>", r"\n\n### \1\n\n", text)
    text = re.sub(r"(?is)<h4\b[^>]*>(.*?)</h4>", r"\n\n#### \1\n\n", text)

    text = re.sub(r"(?is)<strong\b[^>]*>(.*?)</strong>", r"**\1**", text)
    text = re.sub(r"(?is)<b\b[^>]*>(.*?)</b>", r"**\1**", text)
    text = re.sub(r"(?is)<em\b[^>]*>(.*?)</em>", r"*\1*", text)

    # 4. Convert Line Breaks and Block Tags to Newlines
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(?:p|div|tr|li)>", "\n", text)

    # 5. Strip Remaining HTML Tags
    text = re.sub(r"<[^>]+>", "", text)

    # 6. Unescape HTML Entities (&amp; -> &, &lt; -> <, etc.)
    text = html.unescape(text)

    # 7. Convert text tables (e.g. "TEST | VALUE | UNIT | REFERENCE") into Markdown tables
    text_lines = text.splitlines()
    md_lines = []
    in_text_table = False

    for line in text_lines:
        line_s = line.strip()
        if "|" in line_s and len(line_s.split("|")) >= 3:
            cells = [c.strip() for c in line_s.split("|") if c.strip()]
            if cells:
                md_row = "| " + " | ".join(cells) + " |"
                if not in_text_table:
                    md_lines.append("")
                    md_lines.append(md_row)
                    md_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
                    in_text_table = True
                else:
                    md_lines.append(md_row)
                continue
        else:
            in_text_table = False

        if line_s:
            md_lines.append(line_s)
        elif md_lines and md_lines[-1] != "":
            md_lines.append("")

    return "\n".join(md_lines).strip()
