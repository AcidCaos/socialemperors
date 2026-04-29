import os
import time
import threading
from bundle import BASE_DIR

ASSETS_CACHE_DIR = os.path.join(BASE_DIR, "download_assets", "assets")
SCAN_INTERVAL    = 30

KNOWN_EXT = {
    ".swf":  ("SWF",   "🔁"),
    ".png":  ("IMG",   "🖼️ "),
    ".mp3":  ("AUDIO", "🔊"),
    ".xml":  ("XML",   "📄"),
    ".json": ("JSON",  "📦"),
}
FALLBACK = ("OTHER", "📁")

_last_known: set = set()
_lock = threading.Lock()

def _fmt_size(b: int) -> str:
    if b < 1024:       return f"{b}B"
    elif b < 1024**2:  return f"{b / 1024:.1f}KB"
    elif b < 1024**3:  return f"{b / 1024**2:.1f}MB"
    return f"{b / 1024**3:.2f}GB"

def _scan_and_log():
    global _last_known

    if not os.path.exists(ASSETS_CACHE_DIR):
        print("[CACHE] Folder download_assets/assets/ does not exist yet.")
        print("[CACHE] Start the game at least once to begin caching assets.")
        return

    counts:  dict = {}
    sizes:   dict = {}
    icons:   dict = {}
    current: set  = set()

    for root, _, files in os.walk(ASSETS_CACHE_DIR):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                fsize = os.path.getsize(fpath)
            except OSError:
                continue

            ext          = os.path.splitext(fname)[1].lower()
            cat, icon    = KNOWN_EXT.get(ext, FALLBACK)
            counts[cat]  = counts.get(cat, 0) + 1
            sizes[cat]   = sizes.get(cat, 0) + fsize
            icons[cat]   = icon
            current.add(fpath)

    with _lock:
        new_files   = current - _last_known
        _last_known = current

    total_files = sum(counts.values())
    total_size  = _fmt_size(sum(sizes.values()))

    print(f"[CACHE] Total: {total_files} files — {total_size}")

    for cat in sorted(counts.keys()):
        icon  = icons.get(cat, FALLBACK[1])
        count = counts[cat]
        size  = _fmt_size(sizes[cat])
        print(f"[CACHE] {icon} {cat:<6}  {count:>4} files  ({size})")

    for fpath in sorted(new_files):
        rel = os.path.relpath(fpath, ASSETS_CACHE_DIR)
        try:
            fsize = _fmt_size(os.path.getsize(fpath))
        except OSError:
            fsize = "?"
        print(f"[CACHE] NEW  {rel}  ({fsize})")

def _loop():
    while True:
        _scan_and_log()
        time.sleep(SCAN_INTERVAL)


print("[CACHE] Asset cache logger started.")
threading.Thread(target=_loop, daemon=True).start()
