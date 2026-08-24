"""
Export a static snapshot of the public feed for the Vercel frontend to fall
back on when the real backend (this script's --url) is offline.
Run this while ourfeed.py is up, then redeploy vercel-frontend/ to Vercel.

Usage: python export_snapshot.py [--url http://localhost:8731]
"""
import argparse
import json
import urllib.request
from pathlib import Path

OUT_FILE = Path(__file__).parent / "vercel-frontend" / "data" / "snapshot.json"


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as res:
        return json.loads(res.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8731")
    args = parser.parse_args()

    config = fetch_json(f"{args.url}/api/config")
    entries = fetch_json(f"{args.url}/api/public/feed")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"config": config, "entries": entries}, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(entries)} entries to {OUT_FILE}")
    print("Now redeploy vercel-frontend/ to Vercel for this to take effect.")


if __name__ == "__main__":
    main()
