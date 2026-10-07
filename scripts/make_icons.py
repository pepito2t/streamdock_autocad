"""Draws the plugin icons with Pillow: dark rounded tile, one flat glyph per action."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 144
RADIUS = 24
STROKE = 10
TILE = (34, 36, 40)
RED = (226, 64, 52)
GREEN = (72, 190, 110)
GREY = (110, 114, 120)
BLUE = (82, 130, 220)
AMBER = (232, 170, 48)
WHITE = (245, 245, 245)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "com.tmbk.streamdock.autocad.sdPlugin" / "images"


def tile(background: tuple[int, int, int] = TILE) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), RADIUS, fill=background)
    return image, draw


def category() -> Image.Image:
    image, draw = tile()
    font = ImageFont.load_default(size=96)
    draw.text((SIZE / 2, SIZE / 2 + 4), "A", fill=RED, font=font, anchor="mm")
    return image


def macro() -> Image.Image:
    image, draw = tile()
    bolt = [(82, 18), (40, 80), (68, 80), (56, 126), (104, 60), (76, 60)]
    draw.polygon(bolt, fill=RED)
    return image


def toggle(on: bool) -> Image.Image:
    image, draw = tile()
    color = GREEN if on else GREY
    draw.rounded_rectangle((22, 50, 122, 94), 22, outline=color, width=STROKE - 2)
    knob_x = 100 if on else 44
    draw.ellipse((knob_x - 16, 56, knob_x + 16, 88), fill=color)
    return image


def layer(on: bool) -> Image.Image:
    background = BLUE if on else TILE
    color = WHITE if on else BLUE
    image, draw = tile(background)
    for offset in (0, 22, 44):
        top = 30 + offset
        rhombus = [(72, top), (118, top + 22), (72, top + 44), (26, top + 22)]
        if offset == 44:
            draw.polygon(rhombus, fill=color)
        else:
            draw.polygon(rhombus, outline=color, width=STROKE - 3)
    return image


def status() -> Image.Image:
    image, draw = tile()
    draw.ellipse((28, 28, 116, 116), outline=AMBER, width=STROKE - 2)
    draw.ellipse((64, 44, 80, 60), fill=AMBER)
    draw.rounded_rectangle((65, 68, 79, 100), 6, fill=AMBER)
    return image


def dial() -> Image.Image:
    image, draw = tile()
    draw.ellipse((26, 26, 118, 118), outline=WHITE, width=STROKE - 2)
    draw.arc((36, 36, 108, 108), start=200, end=340, fill=RED, width=STROKE - 2)
    draw.line((72, 72, 72, 38), fill=RED, width=STROKE - 2)
    draw.ellipse((64, 64, 80, 80), fill=WHITE)
    return image


def drawflow() -> Image.Image:
    image, draw = tile()
    draw.rounded_rectangle((26, 40, 66, 104), 8, outline=BLUE, width=STROKE - 3)
    draw.polygon([(80, 56), (118, 72), (80, 88)], fill=BLUE)
    draw.line((66, 72, 80, 72), fill=BLUE, width=STROKE - 3)
    return image


def block() -> Image.Image:
    image, draw = tile()
    draw.polygon([(72, 26), (118, 50), (72, 74), (26, 50)], outline=AMBER, width=STROKE - 3)
    draw.polygon([(26, 50), (72, 74), (72, 118), (26, 94)], fill=AMBER)
    draw.polygon([(118, 50), (72, 74), (72, 118), (118, 94)], outline=AMBER, width=STROKE - 3)
    return image


def plot() -> Image.Image:
    image, draw = tile()
    draw.rounded_rectangle((26, 54, 118, 104), 10, outline=WHITE, width=STROKE - 3)
    draw.rectangle((46, 30, 98, 54), fill=WHITE)
    draw.rectangle((46, 90, 98, 120), fill=TILE, outline=WHITE, width=STROKE - 4)
    draw.ellipse((100, 64, 110, 74), fill=GREEN)
    return image


def console() -> Image.Image:
    image, draw = tile()
    draw.rounded_rectangle((20, 30, 124, 114), 10, outline=WHITE, width=STROKE - 4)
    draw.line([(38, 54), (58, 72), (38, 90)], fill=GREEN, width=STROKE - 2, joint="curve")
    draw.line((66, 92, 104, 92), fill=GREEN, width=STROKE - 2)
    return image


ICONS = {
    "category": category,
    "macro": macro,
    "toggle-on": lambda: toggle(True),
    "toggle-off": lambda: toggle(False),
    "layer-on": lambda: layer(True),
    "layer-off": lambda: layer(False),
    "status": status,
    "dial": dial,
    "drawflow": drawflow,
    "block": block,
    "plot": plot,
    "console": console,
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build in ICONS.items():
        build().save(OUTPUT_DIR / f"{name}.png")
        print(f"wrote {name}.png")


if __name__ == "__main__":
    main()
