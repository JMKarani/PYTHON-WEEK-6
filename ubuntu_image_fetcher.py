import os
import sys
import json
import time
import hashlib
import requests
from urllib.parse import urlparse, unquote
from typing import Optional

FETCH_DIR = "Fetched_Images"
MANIFEST = os.path.join(FETCH_DIR, "_manifest.json")
DEFAULT_TIMEOUT = 15
MAX_BYTES = 15 * 1024 * 1024  # 15 MB safety cap

HEADERS = {
    "User-Agent": "UbuntuImageFetcher/1.0 (+community; respectful; educational)",
    "Accept": "image/*, */*;q=0.8",
}

def load_manifest() -> dict:
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"hashes": {}, "files": []}
    return {"hashes": {}, "files": []}

def save_manifest(m: dict) -> None:
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    name = unquote(name).strip()
    if not name or "." not in name:
        # Fallback if no filename in URL
        name = f"downloaded_{int(time.time()*1000)}.jpg"
    # Strip problematic characters
    name = "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " "))
    return name or f"image_{int(time.time()*1000)}.jpg"

def filename_from_headers(resp: requests.Response) -> Optional[str]:
    cd = resp.headers.get("Content-Disposition", "")
    # Simple parse for filename="..."
    if "filename=" in cd:
        part = cd.split("filename=", 1)[-1].strip().strip(";")
        part = part.strip('"').strip("'")
        if part:
            return part
    return None

def ensure_unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(path):
        path = f"{base} ({i}){ext}"
        i += 1
    return path

def is_image_response(resp: requests.Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return ctype.startswith("image/")

def respectful_fetch(url: str, manifest: dict) -> None:
    try:
        os.makedirs(FETCH_DIR, exist_ok=True)

        # HEAD (optional): check type/size early if supported
        try:
            head = requests.head(url, headers=HEADERS, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
            if head.ok:
                if not head.headers.get("Content-Type", "").startswith("image/"):
                    print(f"✗ Skipped (not an image): {url}")
                    return
                clen = head.headers.get("Content-Length")
                if clen and int(clen) > MAX_BYTES:
                    print(f"✗ Skipped (too large: {int(clen)/1024/1024:.1f} MB): {url}")
                    return
        except requests.RequestException:
            # Some servers don’t support HEAD—continue with GET
            pass

        with requests.get(url, headers=HEADERS, stream=True, timeout=DEFAULT_TIMEOUT) as r:
            r.raise_for_status()
            if not is_image_response(r):
                print(f"✗ Not an image (Content-Type={r.headers.get('Content-Type','?')}): {url}")
                return

            # Decide filename (Content-Disposition > URL > fallback)
            fname = filename_from_headers(r) or safe_filename_from_url(url)
            out_path = ensure_unique_path(os.path.join(FETCH_DIR, fname))

            # Stream to file with size cap and hash for duplicate detection
            h = hashlib.sha256()
            total = 0
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_BYTES:
                        f.close()
                        os.remove(out_path)
                        print(f"✗ Aborted (exceeded {MAX_BYTES//1024//1024} MB): {url}")
                        return
                    h.update(chunk)
                    f.write(chunk)

            file_hash = h.hexdigest()

            # Duplicate prevention: if hash already seen, delete new file
            if file_hash in manifest["hashes"]:
                os.remove(out_path)
                print(f"• Duplicate skipped (already have {manifest['hashes'][file_hash]}): {url}")
                return

            # Record new file
            manifest["hashes"][file_hash] = os.path.basename(out_path)
            manifest["files"].append(os.path.basename(out_path))
            save_manifest(manifest)

            print(f"✓ Successfully fetched: {os.path.basename(out_path)}")
            print(f"✓ Image saved to {out_path}")

    except requests.exceptions.RequestException as e:
        print(f"✗ Connection error: {e}")
    except Exception as e:
        print(f"✗ An error occurred: {e}")

def main():
    print("Welcome to the Ubuntu Image Fetcher")
    print("A tool for mindfully collecting images from the web\n")

    # Accept one or many URLs (space/comma/newline separated)
    raw = input("Please enter one or more image URLs:\n> ").strip()
    if not raw:
        print("No URL provided. Exiting respectfully.")
        sys.exit(0)

    # Split by whitespace or comma
    urls = [u.strip() for part in raw.split() for u in part.split(",") if u.strip()]
    manifest = load_manifest()

    for url in urls:
        respectful_fetch(url, manifest)

    print("\nConnection strengthened. Community enriched.")

if __name__ == "__main__":
    main()
