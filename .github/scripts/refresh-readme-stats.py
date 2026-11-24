import sys
from http.client import HTTPException
from pathlib import Path
from time import sleep
from urllib.request import urlopen
from xml.etree import ElementTree as ET


ASSETS = Path(__file__).resolve().parents[2] / "assets"
API = "https://github-readme-stats-enhanced-ap.vercel.app/api"
OPTIONS = "username=Apricityx&theme=transparent&hide_border=true&include_managed_repos=true"
CARDS = (
    ("github-stats.svg", f"{API}?{OPTIONS}&show_icons=true", "stars"),
    ("top-languages.svg", f"{API}/top-langs?{OPTIONS}&layout=compact", "lang-items"),
)
SVG_TAG = "{http://www.w3.org/2000/svg}svg"
MAX_SIZE = 256 * 1024


def download_card(url, marker):
    with urlopen(url, timeout=20) as response:
        if response.headers.get_content_type() != "image/svg+xml":
            raise ValueError("response is not an SVG")
        data = response.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise ValueError("SVG exceeds the size limit")

    # The service can return an error card with an SVG content type.
    root = ET.fromstring(data)
    if root.tag != SVG_TAG or not any(
        element.get("data-testid") == marker for element in root.iter()
    ):
        raise ValueError("response is not the expected stats card")
    return b"\n".join(line.rstrip() for line in data.splitlines()).rstrip() + b"\n"


def refresh():
    ASSETS.mkdir(exist_ok=True)
    succeeded = False
    for filename, url, marker in CARDS:
        for attempt in range(3):
            try:
                data = download_card(url, marker)
            except (OSError, HTTPException, ValueError, ET.ParseError) as error:
                if attempt < 2:
                    sleep(2 ** (attempt + 1))
                    continue
                print(
                    f"::warning::{filename} not updated; keeping the previous SVG ({error})",
                    file=sys.stderr,
                )
            else:
                (ASSETS / filename).write_bytes(data)
                print(f"Downloaded {filename}")
                succeeded = True
            break
    return 0 if succeeded else 1


if __name__ == "__main__":
    sys.exit(refresh())
