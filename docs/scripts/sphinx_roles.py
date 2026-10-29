"""
MkDocs hook: tidy the Sphinx markup left in the rendered docstrings.

The package docstrings use Sphinx roles (``:func:`x```) and ``::`` before code
blocks, which mkdocstrings shows literally. This keeps the code and drops the
role names, so the same docstrings read well in both places.
"""

import re

_ROLE = re.compile(
    r":(?:py:)?(?:mod|func|data|class|meth|attr|obj|exc|const):(?=<code)"
)
_LITERAL = re.compile(r"::(?=</p>)")


def on_page_content(html: str, **kwargs) -> str:
    """Remove role prefixes and literal-block markers from a page."""
    return _LITERAL.sub(":", _ROLE.sub("", html))
