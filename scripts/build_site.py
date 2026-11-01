"""
Generate the public site from `content/`.

    python scripts/build_site.py --base-url https://sensitor.fr --app-url https://app.sensitor.fr [--out site]

`--base-url` is where the site is served (canonical addresses, sitemap, RSS);
`--app-url` is the member area (sign-in, lessons, newsletter form), read from
SENSITOR_PUBLIC_URL when not given. The output folder is emptied first and is
not kept in git: a static host runs this command as its build step.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sensitor.site.build import Site  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--base-url", default=os.getenv("SENSITOR_SITE_URL", "http://localhost:8000"))
    parser.add_argument("--app-url", default=os.getenv("SENSITOR_PUBLIC_URL", "http://localhost:8501"))
    parser.add_argument("--out", default="site")
    args = parser.parse_args(argv)
    try:
        site = Site(args.base_url, args.app_url)
    except ValueError as exc:            # an article that breaks the content rules
        print(f"Articles invalides :\n{exc}")
        return 1
    pages = site.write(Path(args.out))
    print(f"{len(pages)} pages écrites dans {args.out}/, dont {len(site.articles)} article(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
