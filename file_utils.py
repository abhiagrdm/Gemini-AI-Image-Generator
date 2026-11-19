import re
from pathlib import Path

from PIL import Image

from config import SUPPORTED_ASPECT_RATIOS


def slugify(text: str, max_words: int = 8) -> str:
    """'Lab-grown vs natural diamonds' -> 'Lab_Grown_Vs_Natural_Diamonds'"""
    words = re.findall(r"[A-Za-z0-9]+", text)
    words = words[:max_words]
    return "_".join(w.capitalize() for w in words) or "Untitled"


def next_available_path(folder: Path, base_name: str, suffix: str, ext: str) -> Path:
    """Avoids overwriting: Name_Hero_01.png, Name_Hero_02.png, ..."""
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        candidate = folder / f"{base_name}_{suffix}_{n:02d}.{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def next_available_exact_path(folder: Path, base_name: str, ext: str) -> Path:
    """Tries `base_name.ext` first (exact match), only adding a numeric
    suffix if that name is already taken."""
    folder.mkdir(parents=True, exist_ok=True)
    candidate = folder / f"{base_name}.{ext}"
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        candidate = folder / f"{base_name}_{n:02d}.{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def sanitize_filename(name: str) -> str:
    """Strips characters that are illegal in Windows filenames while keeping
    the original name (case, spaces, hyphens) otherwise intact."""
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip(" .")
    return name or "Untitled"


def ratio_to_float(ratio: str) -> float:
    w, h = ratio.split(":")
    return float(w) / float(h)


def closest_supported_ratio(target_ratio: str) -> str:
    """Gemini's ImageConfig only accepts a fixed list of ratios. Find the
    closest one so we always send a value the API will accept."""
    if target_ratio in SUPPORTED_ASPECT_RATIOS:
        return target_ratio
    target = ratio_to_float(target_ratio)
    return min(
        SUPPORTED_ASPECT_RATIOS,
        key=lambda r: abs(ratio_to_float(r) - target),
    )


def crop_to_ratio(image: Image.Image, target_ratio: float) -> Image.Image:
    """Center-crops the image so width/height exactly matches target_ratio,
    regardless of which supported ratio it was generated at."""
    w, h = image.size
    current = w / h

    if abs(current - target_ratio) < 1e-3:
        return image

    if current > target_ratio:
        # Too wide: crop left/right.
        new_w = round(h * target_ratio)
        left = (w - new_w) // 2
        return image.crop((left, 0, left + new_w, h))
    else:
        # Too tall: crop top/bottom.
        new_h = round(w / target_ratio)
        top = (h - new_h) // 2
        return image.crop((0, top, w, top + new_h))


def crop_to_exact_ratio(image: Image.Image, target_ratio: str) -> Image.Image:
    """Same as crop_to_ratio but takes a 'W:H' string, e.g. '13:8'."""
    return crop_to_ratio(image, ratio_to_float(target_ratio))


def resize_to_exact_pixels(image: Image.Image, width_px: float, height_px: float) -> Image.Image:
    """Crops to the target ratio, then resizes to the exact pixel dimensions.
    Pixel counts are rounded to the nearest whole pixel since raster images
    can't have fractional dimensions (e.g. 295.5 -> 296)."""
    image = crop_to_ratio(image, width_px / height_px)
    return image.resize((round(width_px), round(height_px)), Image.Resampling.LANCZOS)


def save_image(image: Image.Image, output_dir: Path, topic: str, label: str) -> Path:
    """Saves the generated PNG under an auto-generated name based on the
    chat idea, auto-incrementing if it exists (used when no reference image
    was uploaded)."""
    base_name = slugify(topic)
    image_path = next_available_path(output_dir, base_name, label, "png")
    image.save(image_path)
    return image_path


def save_image_as(image: Image.Image, output_dir: Path, filename_stem: str) -> Path:
    """Saves the generated PNG under the given filename (e.g. reused from an
    uploaded reference image's name), only adding a numeric suffix if that
    exact name already exists."""
    base_name = sanitize_filename(filename_stem)
    image_path = next_available_exact_path(output_dir, base_name, "png")
    image.save(image_path)
    return image_path
