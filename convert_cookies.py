"""
Convert a Chrome JSON cookie export to Netscape cookies.txt (the format yt-dlp reads).

Usage:
    python convert_cookies.py <input.json> [output.txt]

If output path is omitted, writes alongside the input file with a .txt extension.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def convert(json_path: Path, txt_path: Path) -> int:
    cookies: list[dict] = json.loads(json_path.read_text(encoding="utf-8"))
    lines = [
        "# Netscape HTTP Cookie File\n",
        "# Converted from Chrome JSON export.\n",
        "\n",
    ]
    for c in cookies:
        domain = c.get("domain", "")
        include_sub = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        expiry = int(c.get("expirationDate") or 0) or 2147483647
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
    txt_path.write_text("".join(lines), encoding="utf-8")
    return len(cookies)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    json_path = Path(sys.argv[1]).resolve()
    txt_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else json_path.with_suffix(".txt")
    n = convert(json_path, txt_path)
    print(f"Wrote {n} cookies to {txt_path}")


if __name__ == "__main__":
    main()