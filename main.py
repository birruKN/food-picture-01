#!/usr/bin/env python3
"""food-picture-01 entry: a steaming bowl of tonkotsu ramen.

The picture ships beside this program as entry.png (JPEG bytes under the
name the rules keep: the gate tells PNG and JPEG apart by first bytes).
The program checks the picture against the competition caps and copies it
byte for byte to <output>/entry.png, so every run writes identical bytes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import sys

MAX_BYTES = 1_048_576  # 1 MiB
MAX_SIDE = 1024        # pixels, either axis

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"


def png_dimensions(data):
    """(width, height) from a PNG's IHDR chunk, or None if not a PNG."""
    if not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


# Start-of-frame markers that carry a JPEG's dimensions (baseline/extended/
# progressive); the other SOFn values are reserved or arithmetic-coded.
_JPEG_SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_dimensions(data):
    """(width, height) from the first SOF segment, or None if not found.

    Walks the marker stream: each segment after the SOI marker is a 0xFF
    prefix, a marker byte, and (except for standalone markers) a two-byte
    big-endian length that counts itself. A SOF payload opens with the
    sample precision, then height, then width.
    """
    pos = 2  # skip the SOI marker (FF D8)
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker in _JPEG_SOF_MARKERS:
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            pos += 2  # standalone marker: no length field follows
            continue
        segment_length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if segment_length < 2:
            return None
        pos += 2 + segment_length
    return None


def check_picture(data):
    """Raise SystemExit unless the picture fits the competition gate."""
    if len(data) > MAX_BYTES:
        raise SystemExit(f"picture is {len(data)} bytes, over the 1 MiB cap")
    if data.startswith(PNG_SIGNATURE):
        dimensions = png_dimensions(data)
        if dimensions is None:
            raise SystemExit("PNG signature but no IHDR chunk")
    elif data.startswith(JPEG_SIGNATURE):
        dimensions = jpeg_dimensions(data)
        if dimensions is None:
            raise SystemExit("JPEG signature but no SOF segment")
    else:
        raise SystemExit("picture is neither PNG nor JPEG")
    if dimensions is not None and max(dimensions) > MAX_SIDE:
        raise SystemExit(f"picture is {dimensions[0]}x{dimensions[1]}, over 1024 a side")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "entry.png"), "rb") as picture_file:
        data = picture_file.read()
    check_picture(data)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as out_file:
        out_file.write(data)
    print(f"wrote {out_path} ({len(data)} bytes)")


if __name__ == "__main__":
    sys.exit(main())
