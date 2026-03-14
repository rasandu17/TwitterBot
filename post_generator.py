"""
Post Generator - Creates viral fact-style social media images.

Workflow:
  1. User sends a photo + news text via Telegram
  2. Groq generates styled caption with markup
  3. This module composites the final post image:
       - User's photo as background (cropped to square, vibrance-boosted)
       - Dark gradient banner at the bottom (soft feathered, dynamic height)
       - Bold styled text with yellow/brown color highlights
       - Optional circular inset image (if user sends two photos)
"""

import io
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── Constants ──────────────────────────────────────────────────────────────────
POST_SIZE        = 1080
BANNER_MAX_H     = 500
BANNER_MIN_H     = 280
WHITE            = (255, 255, 255)
YELLOW           = (255, 215, 0)
BROWN_BG         = (140, 0, 0)
DARK             = (8, 8, 8)
FONT_SIZE        = 64
LINE_SPACING     = 16
TEXT_PADDING     = 48
GRADIENT_FEATHER = 0.45
VIBRANCE_AMOUNT  = 0.58          # Lightroom-style vibrance boost (0–1)


# ── Vibrance boost ─────────────────────────────────────────────────────────────
def _boost_vibrance(img: Image.Image, amount: float = VIBRANCE_AMOUNT) -> Image.Image:
    """Selectively boost saturation — low-sat pixels get more boost (like Lightroom Vibrance)."""
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    mx = arr.max(axis=2)
    sat = (mx - arr.min(axis=2)) / (mx + 1e-6)
    boost = 1.0 + amount * (1.0 - sat[:, :, None])
    grey = arr.mean(axis=2, keepdims=True)
    boosted = grey + (arr - grey) * boost
    return Image.fromarray(boosted.clip(0, 255).astype(np.uint8), "RGB")


# ── Font loading ───────────────────────────────────────────────────────────────
def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = (
        ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
        if bold else
        ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ── Text parsing ───────────────────────────────────────────────────────────────
def _parse(text: str) -> list:
    import re
    parts = []
    pattern = re.compile(r'\[yellow\](.*?)\[/yellow\]|\[brown\](.*?)\[/brown\]', re.DOTALL)
    cursor = 0
    for m in pattern.finditer(text):
        before = text[cursor:m.start()]
        if before:
            parts.append((before, "white"))
        if m.group(1) is not None:
            parts.append((m.group(1), "yellow"))
        elif m.group(2) is not None:
            parts.append((m.group(2), "brown"))
        cursor = m.end()
    tail = text[cursor:]
    if tail:
        parts.append((tail, "white"))
    return parts


def _tokenize(parts: list) -> list:
    tokens = []
    for segment, style in parts:
        words = segment.split(" ")
        for i, word in enumerate(words):
            if word:
                tokens.append((word, style))
            if i < len(words) - 1:
                tokens.append((" ", style))
    return tokens


# ── Text layout & drawing ──────────────────────────────────────────────────────
def _word_wrap(tokens: list, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    lines = []
    current = []
    current_w = 0

    for token, style in tokens:
        token_w = int(font.getlength(token))
        if token == " ":
            if current:
                current.append((token, style))
                current_w += token_w
        else:
            if current_w + token_w > max_width and current:
                while current and current[-1][0] == " ":
                    current.pop()
                lines.append(current)
                current = [(token, style)]
                current_w = token_w
            else:
                current.append((token, style))
                current_w += token_w

    if current:
        while current and current[-1][0] == " ":
            current.pop()
        lines.append(current)
    return lines


def _measure_line(line: list, font: ImageFont.FreeTypeFont) -> float:
    return sum(font.getlength(w) for w, _ in line)


def _draw_text_block(draw: ImageDraw.Draw, lines: list, font: ImageFont.FreeTypeFont,
                     canvas_width: int, start_y: int, line_height: int) -> None:
    BOX_PAD_X = 10
    BOX_PAD_Y = 5

    y = start_y
    for line in lines:
        line_w = _measure_line(line, font)
        x = (canvas_width - line_w) / 2

        for word, style in line:
            word_w = font.getlength(word)

            if style == "brown" and word.strip():
                box = [x - BOX_PAD_X, y - BOX_PAD_Y,
                       x + word_w + BOX_PAD_X, y + line_height - LINE_SPACING + BOX_PAD_Y]
                draw.rounded_rectangle(box, radius=6, fill=BROWN_BG)
                draw.text((x, y), word, font=font, fill=WHITE)
            elif style == "yellow" and word.strip():
                draw.text((x, y), word, font=font, fill=YELLOW)
            else:
                draw.text((x, y), word, font=font, fill=WHITE)

            x += word_w

        y += line_height


# ── Smooth gradient banner ─────────────────────────────────────────────────────
def _draw_gradient_banner(canvas: Image.Image, banner_y: int, banner_h: int) -> None:
    """Sine-eased feathered dark gradient — photographic soft look matching reference."""
    overlay = Image.new("RGBA", (POST_SIZE, POST_SIZE), (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)
    feather_px = int(banner_h * GRADIENT_FEATHER)

    for dy in range(banner_h):
        if dy < feather_px:
            t = dy / feather_px
            alpha = int(252 * (0.5 - 0.5 * math.cos(t * math.pi)))
        else:
            alpha = 252
        draw_o.line([(0, banner_y + dy), (POST_SIZE, banner_y + dy)],
                    fill=(DARK[0], DARK[1], DARK[2], alpha))

    canvas.alpha_composite(overlay)


# ── Circular inset ─────────────────────────────────────────────────────────────
def _add_circle_inset(canvas: Image.Image, inset: Image.Image,
                      size: int = 220, border: int = 8) -> None:
    inset = inset.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    bd = size + border * 2
    disc = Image.new("RGBA", (bd, bd), (0, 0, 0, 0))
    ImageDraw.Draw(disc).ellipse([0, 0, bd - 1, bd - 1], fill=(*BROWN_BG, 255))
    margin_right, margin_top = 55, 55
    bx = POST_SIZE - bd - margin_right
    by = margin_top
    canvas.alpha_composite(disc, (bx, by))
    circle = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circle.paste(inset, mask=mask)
    canvas.alpha_composite(circle, (bx + border, by + border))


# ── Main entry ─────────────────────────────────────────────────────────────────
def create_post_from_photo(
    bg_bytes: bytes,
    styled_text: str,
    inset_bytes: bytes | None = None,
) -> io.BytesIO:
    """
    Compose a viral post image.

    Args:
        bg_bytes:     Raw bytes of the background image.
        styled_text:  Caption with [yellow]/[brown] markup from Groq.
        inset_bytes:  Optional bytes of a second image for the circular inset.

    Returns:
        BytesIO JPEG of the finished 1080x1080 post.
    """
    # ── 1. Prepare & vibrance-boost background ────────────────────────────────
    bg = Image.open(io.BytesIO(bg_bytes)).convert("RGB")
    w, h = bg.size
    side = min(w, h)
    bg = bg.crop(((w - side) // 2, (h - side) // 2,
                   (w + side) // 2, (h + side) // 2))
    bg = bg.resize((POST_SIZE, POST_SIZE), Image.LANCZOS)
    bg = _boost_vibrance(bg, VIBRANCE_AMOUNT)
    canvas = bg.convert("RGBA")

    # ── 2. Parse & measure text ───────────────────────────────────────────────
    font = _load_font(FONT_SIZE, bold=True)
    line_height = FONT_SIZE + LINE_SPACING
    max_text_w = POST_SIZE - TEXT_PADDING * 2

    parts = _parse(styled_text)
    tokens = _tokenize(parts)
    lines = _word_wrap(tokens, font, max_text_w)
    total_text_h = len(lines) * line_height

    # ── Dynamic banner height — grows with caption ────────────────────────────
    vertical_padding = TEXT_PADDING * 2 + int(line_height * 0.4)
    banner_h = max(BANNER_MIN_H, min(total_text_h + vertical_padding, BANNER_MAX_H))
    banner_y = POST_SIZE - banner_h

    # ── 3. Smooth dark gradient banner ───────────────────────────────────────
    _draw_gradient_banner(canvas, banner_y, banner_h)

    # ── 4. Optional circular inset ────────────────────────────────────────────
    if inset_bytes:
        try:
            _add_circle_inset(canvas, Image.open(io.BytesIO(inset_bytes)))
        except Exception as e:
            print(f"[post_generator] Inset image failed: {e}")

    # ── 5. Draw text ──────────────────────────────────────────────────────────
    draw = ImageDraw.Draw(canvas)
    text_start_y = banner_y + (banner_h - total_text_h) // 2
    _draw_text_block(draw, lines, font, POST_SIZE, text_start_y, line_height)

    # ── 6. Export ─────────────────────────────────────────────────────────────
    out = canvas.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=92, optimize=True)
    buf.seek(0)
    buf.name = "post.jpg"
    return buf