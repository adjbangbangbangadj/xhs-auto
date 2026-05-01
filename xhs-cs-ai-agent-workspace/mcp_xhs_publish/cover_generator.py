#!/usr/bin/env python3
"""
Generate XHS cover images from reviewed markdown posts.

Each image is 1080x1440 (3:4 vertical), with:
- Gradient background matching the app theme
- Centered post title
- Subtle decorative elements
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import extract_front_matter, read_text  # noqa: E402

# Dimensions for XHS cover (3:4)
W, H = 1080, 1440

# Color palette
BG_GRADIENT_TOP = (99, 102, 241)    # indigo
BG_GRADIENT_BOTTOM = (139, 92, 246)  # violet
ACCENT = (6, 182, 212)               # teal
WHITE = (255, 255, 255)
WHITE_SOFT = (245, 243, 255)
DARK = (15, 23, 42)


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a suitable font. Falls back to default if Noto Sans SC not found."""
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",       # Microsoft YaHei
        "C:/Windows/Fonts/msyhbd.ttc",     # Microsoft YaHei Bold
        "C:/Windows/Fonts/simhei.ttf",     # SimHei
        "C:/Windows/Fonts/STHeiti.ttf",    # STHeiti
    ]
    for fp in font_paths:
        p = Path(fp)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def _gradient_bg(draw: ImageDraw.Draw) -> None:
    """Draw a diagonal gradient background."""
    for y in range(H):
        t = y / H
        r = int(BG_GRADIENT_TOP[0] * (1 - t) + BG_GRADIENT_BOTTOM[0] * t)
        g = int(BG_GRADIENT_TOP[1] * (1 - t) + BG_GRADIENT_BOTTOM[1] * t)
        b = int(BG_GRADIENT_TOP[2] * (1 - t) + BG_GRADIENT_BOTTOM[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap Chinese/English text to fit within max_width."""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def generate_cover(title: str, output_path: Path, subtitle: str = "") -> Path:
    """Generate a single XHS cover image."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Background gradient
    _gradient_bg(draw)

    # Decorative circles
    for cx, cy, r, alpha in [
        (860, 200, 280, 30),
        (180, 1200, 200, 25),
        (920, 1100, 160, 20),
    ]:
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        odraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # Accent line
    line_y = int(H * 0.43)
    draw.line(
        [(W // 2 - 60, line_y), (W // 2 + 60, line_y)],
        fill=ACCENT,
        width=4,
    )

    # Title
    title_font = _get_font(56, bold=True)
    wrapped = _wrap_text(title, title_font, W - 160)
    y_start = line_y - 24 - len(wrapped) * 70
    for i, line in enumerate(wrapped):
        bbox = title_font.getbbox(line)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x + 2, y_start + i * 70 + 2), line, font=title_font, fill=DARK)
        draw.text((x, y_start + i * 70), line, font=title_font, fill=WHITE)

    # Subtitle / topic
    if subtitle:
        sub_font = _get_font(32)
        bbox = sub_font.getbbox(subtitle)
        sw = bbox[2] - bbox[0]
        sx = (W - sw) // 2
        draw.text((sx, line_y + 28), subtitle, font=sub_font, fill=WHITE_SOFT)

    # Bottom label
    label_font = _get_font(28)
    label = "计算机复试 · AI 准备"
    bbox = label_font.getbbox(label)
    lw = bbox[2] - bbox[0]
    lx = (W - lw) // 2
    ly = H - 140
    draw.text((lx, ly), label, font=label_font, fill=WHITE_SOFT)

    # Footer decoration
    footer_y = H - 80
    draw.line(
        [(W // 2 - 40, footer_y), (W // 2 + 40, footer_y)],
        fill=ACCENT,
        width=2,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    return output_path


def main():
    reviewed_dir = PROJECT_ROOT / "posts" / "reviewed"
    covers_dir = PROJECT_ROOT / "posts" / "covers"
    files = sorted(reviewed_dir.glob("*.md"))

    if not files:
        print("No reviewed posts found.")
        return

    for f in files:
        text = read_text(f)
        meta = extract_front_matter(text)

        # Extract title from markdown heading
        title = ""
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        for line in body.splitlines():
            if line.startswith("# ") and not line.startswith("## "):
                title = line[2:].strip()
                break
        if not title:
            title = meta.get("title", f.stem)

        # Use content type as subtitle
        content_type = meta.get("content_type", "")
        subtitle = f"#{content_type}" if content_type else ""

        output = covers_dir / f"{f.stem}_cover.png"
        generate_cover(title, output, subtitle)
        print(f"  Generated: {output.name}  [{content_type}]")

    print(f"\nDone. {len(files)} covers saved to {covers_dir}")


if __name__ == "__main__":
    main()
