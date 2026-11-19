import io
import time
from pathlib import Path

from google.genai import types
from PIL import Image

from file_utils import closest_supported_ratio, resize_to_exact_pixels, save_image, save_image_as


class ImageGenerationError(Exception):
    """Raised when Gemini returns no usable image (blocked, quota, etc.)."""


def _is_model_unavailable(exc: Exception) -> bool:
    """True for errors meaning 'this model isn't reachable on this account'
    (e.g. not yet allowlisted on Vertex AI) — retrying the same model is
    pointless, but a fallback model is worth trying."""
    text = str(exc).upper()
    return "404" in text or "NOT_FOUND" in text or "PERMISSION_DENIED" in text


def _is_rate_limited(exc: Exception) -> bool:
    """True for quota/rate-limit errors (429 RESOURCE_EXHAUSTED). These clear
    on their own once the per-minute quota window resets, so they need a
    longer wait than a generic transient error, not a faster retry."""
    text = str(exc).upper()
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def generate_image(
    client,
    detailed_prompt: str,
    aspect_ratio: str,
    model: str,
    reference_images: list[Image.Image] | None = None,
    max_retries: int = 3,
    fallback_model: str | None = None,
) -> tuple[Image.Image, str]:
    """Sends the detailed prompt (and optional reference images) to a Gemini
    image model and returns (PIL Image, model actually used). Retries on
    transient failures, and falls back to `fallback_model` if the primary
    model isn't reachable on this account (e.g. Vertex AI allowlist gating)."""

    api_ratio = closest_supported_ratio(aspect_ratio)

    contents = [detailed_prompt]
    if reference_images:
        contents.extend(reference_images)

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=api_ratio),
    )

    models_to_try = [model]
    if fallback_model and fallback_model != model:
        models_to_try.append(fallback_model)

    last_error = None
    for candidate_model in models_to_try:
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=candidate_model, contents=contents, config=config,
                )
                return _extract_image(response), candidate_model
            except ImageGenerationError:
                raise  # blocked / no image — retrying won't help, surface it now
            except Exception as exc:  # network errors, 429/503, 404s, etc.
                last_error = exc
                if _is_model_unavailable(exc):
                    break  # stop retrying this model, move on to the fallback
                if attempt < max_retries:
                    if _is_rate_limited(exc):
                        time.sleep(15 * attempt)  # 15s, 30s — QPM quotas reset roughly per-minute
                    else:
                        time.sleep(2 ** attempt)  # 2s, 4s, 8s backoff
                continue

    raise ImageGenerationError(
        f"Image generation failed on {models_to_try}: {last_error}"
    )


def generate_and_save_image(
    client,
    detailed_prompt: str,
    aspect_ratio: str,
    model: str,
    output_dir: Path,
    target_width_px: float,
    target_height_px: float,
    reference_image: Image.Image | None = None,
    filename_stem: str | None = None,
    topic: str = "",
    label: str = "Hero",
    fallback_model: str | None = None,
) -> tuple[Path, str]:
    """One full job: generate an image (optionally from a single reference
    photo), resize it to the exact target pixel size, and save it — either
    under `filename_stem` (reused from a reference photo's name) or a name
    derived from `topic`. Returns (saved path, model actually used)."""

    image, model_used = generate_image(
        client,
        detailed_prompt=detailed_prompt,
        aspect_ratio=aspect_ratio,
        model=model,
        reference_images=[reference_image] if reference_image is not None else None,
        fallback_model=fallback_model,
    )
    image = resize_to_exact_pixels(image, target_width_px, target_height_px)

    if filename_stem:
        path = save_image_as(image, output_dir, filename_stem=filename_stem)
    else:
        path = save_image(image, output_dir, topic=topic, label=label)

    return path, model_used


def _extract_image(response) -> Image.Image:
    if not response.candidates:
        feedback = getattr(response, "prompt_feedback", None)
        raise ImageGenerationError(
            f"No candidates returned. Prompt may have been blocked: {feedback}"
        )

    candidate = response.candidates[0]
    finish_reason = getattr(candidate, "finish_reason", None)

    for part in candidate.content.parts:
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))

    raise ImageGenerationError(
        "Response contained no image data. "
        f"finish_reason={finish_reason}. This usually means the prompt tripped "
        "a safety filter — rephrase the idea and try again."
    )
