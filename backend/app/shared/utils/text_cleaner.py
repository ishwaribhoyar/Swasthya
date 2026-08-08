"""
HTML to Clean Clinical Text & Markdown Converter.

Strips HTML boilerplate (DOCTYPE, head, CSS style blocks, script tags, HTML tags)
and returns clean, readable medical text & markdown.
"""
from __future__ import annotations

import html
import re


def clean_html_to_text(raw_str: str) -> str:
    """
    Convert raw HTML output (including full document boilerplate with <style> blocks)
    into clean, readable plain text / markdown.
    """
    if not raw_str:
        return ""

    # If string contains HTML boilerplate or tags
    if "<" in raw_str and ">" in raw_str:
        # 1. Remove <style>...</style> and <script>...</script> completely
        text = re.sub(r"(?is)<style\b[^>]*>.*?</style>", "", raw_str)
        text = re.sub(r"(?is)<script\b[^>]*>.*?</script>", "", text)
        text = re.sub(r"(?is)<head\b[^>]*>.*?</head>", "", text)

        # 2. Replace structural tags with newlines
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</(?:p|div|tr|h1|h2|h3|h4|h5|h6|li)>", "\n", text)
        text = re.sub(r"(?i)</(?:td|th)>", " | ", text)

        # 3. Strip all remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # 4. Unescape HTML entities (&lt; -> <, &gt; -> >, &amp; -> &, &quot; -> ")
        text = html.unescape(text)

        # 5. Clean up excessive blank lines & trailing spaces
        lines = [line.strip() for line in text.splitlines()]
        clean_lines = []
        blank = False
        for line in lines:
            if line:
                clean_lines.append(line)
                blank = False
            elif not blank:
                clean_lines.append("")
                blank = True

        return "\n".join(clean_lines).strip()

    return raw_str.strip()
