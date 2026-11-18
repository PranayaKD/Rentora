import urllib.request
import re

urls = [
    "https://rentora-6d1s.onrender.com/",
    "https://rentora-6d1s.onrender.com/cars/",
    "https://rentora-6d1s.onrender.com/cars/?page=2",
    "https://rentora-6d1s.onrender.com/health/",
]

headers = {"User-Agent": "Mozilla/5.0"}

for url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            content = resp.read().decode("utf-8")
            cloudinary_urls = set(re.findall(r"https://res\.cloudinary\.com/[^\s\"'>]+", content))
            placeholders = re.findall(r"car-placeholder\.jpg", content)
            print(f"[{resp.status}] {url}")
            print(f"    Cloudinary images: {len(cloudinary_urls)} | Placeholders: {len(placeholders)}")
    except Exception as e:
        print(f"Error checking {url}: {e}")

