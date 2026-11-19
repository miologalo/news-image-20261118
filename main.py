"""news-image-20261118 entry (Python 3.13, standard library only).

Copies the bundled front-page image (entry.png, JPEG bytes) to
/output/entry.png and validates it before exiting: the file must exist,
be at most 1 MiB, carry JPEG or PNG magic, and be at most 1024x1024
pixels. Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in
for /output:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576
MAX_DIM = 1024

JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def jpeg_size(path):
    """Return (width, height) of a JPEG by scanning for its SOF marker."""
    with open(path, "rb") as fh:
        data = fh.read()
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height = struct.unpack(">H", data[i + 5:i + 7])[0]
            width = struct.unpack(">H", data[i + 7:i + 9])[0]
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + length
    raise ValueError("no SOF marker found in JPEG")


def png_size(path):
    """Return (width, height) of a PNG from its IHDR chunk."""
    with open(path, "rb") as fh:
        header = fh.read(33)
    if header[12:16] != b"IHDR":
        raise ValueError("PNG missing IHDR chunk")
    width = struct.unpack(">I", header[16:20])[0]
    height = struct.unpack(">I", header[20:24])[0]
    return width, height


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, "entry.png")

    if not os.path.isfile(src):
        print(f"missing bundled image: {src}", file=sys.stderr)
        return 1
    size = os.path.getsize(src)
    if size > MAX_BYTES:
        print(f"image too large: {size} bytes", file=sys.stderr)
        return 1
    with open(src, "rb") as fh:
        magic = fh.read(8)
    if magic[:3] == JPEG_MAGIC:
        width, height = jpeg_size(src)
        kind = "JPEG"
    elif magic[:8] == PNG_MAGIC:
        width, height = png_size(src)
        kind = "PNG"
    else:
        print("image is neither JPEG nor PNG", file=sys.stderr)
        return 1
    if width > MAX_DIM or height > MAX_DIM:
        print(f"image too large: {width}x{height}", file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, dst)
    # Self-check: the copy must be byte-identical to the bundled image,
    # so the two grader runs can never disagree.
    with open(src, "rb") as fh:
        src_bytes = fh.read()
    with open(dst, "rb") as fh:
        dst_bytes = fh.read()
    if src_bytes != dst_bytes:
        print("copy mismatch: output differs from bundled image", file=sys.stderr)
        return 1
    print(f"wrote {dst}: {kind} {width}x{height}, {size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
