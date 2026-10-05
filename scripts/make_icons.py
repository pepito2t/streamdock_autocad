import struct
import zlib
from pathlib import Path

SIZE = 144
BORDER = 10
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "com.tmbk.streamdock.autocad.sdPlugin" / "images"

ICONS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "category": ((30, 30, 30), (220, 60, 50)),
    "macro": ((30, 30, 30), (220, 60, 50)),
    "toggle-off": ((30, 30, 30), (90, 90, 90)),
    "toggle-on": ((30, 30, 30), (60, 180, 90)),
    "layer-off": ((30, 30, 30), (70, 110, 200)),
    "layer-on": ((70, 110, 200), (255, 255, 255)),
    "status": ((30, 30, 30), (200, 160, 40)),
}


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def framed_square(background: tuple[int, int, int], frame: tuple[int, int, int]) -> bytes:
    rows = []
    for y in range(SIZE):
        row = bytearray(b"\x00")
        for x in range(SIZE):
            on_frame = min(x, y, SIZE - 1 - x, SIZE - 1 - y) < BORDER
            row += bytes(frame if on_frame else background)
        rows.append(bytes(row))
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + png_chunk(b"IEND", b"")
    )


def main() -> None:
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    for name, (background, frame) in ICONS.items():
        (PLUGIN_DIR / f"{name}.png").write_bytes(framed_square(background, frame))
        print(f"wrote {name}.png")


if __name__ == "__main__":
    main()
