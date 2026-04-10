"""
path_utils.py — Lazarus API Defence Platform
Utility for normalising raw URL path strings before comparison or storage.
"""

import re


def normalize_path(path: str) -> str:
    """
    Return a cleaned version of a raw URL path string.

    Applied transformations (in order):
    1. Lowercase the entire path.
    2. Strip any embedded query string (everything from '?' onward).
    3. Collapse consecutive slashes  (e.g. //api//v2  →  /api/v2).
    4. Strip trailing slashes — except for the root path '/'.
    """
    if not path or not isinstance(path, str):
        return path

    # 1. Lowercase
    path = path.lower()

    # 2. Remove embedded query parameters (e.g. /api/v2/resource?foo=bar)
    path = path.split("?", 1)[0]

    # 3. Collapse consecutive slashes into a single slash
    path = re.sub(r"/+", "/", path)

    # 4. Strip trailing slash — but preserve the bare root "/"
    if path != "/":
        path = path.rstrip("/")

    return path
