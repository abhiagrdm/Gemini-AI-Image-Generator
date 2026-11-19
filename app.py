from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import streamlit as st
from google import genai
from PIL import Image

from config import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_HEIGHT_PX,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WIDTH_PX,
    DIMENSION_MISMATCH_TOLERANCE,
    GEMINI_API_KEY,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PROJECT,
    IMAGE_MODEL_DEFAULT,
    IMAGE_MODEL_PREMIUM,
    IMAGE_MODEL_VERTEX_FALLBACK,
    MAX_CONCURRENT_GENERATIONS,
    SUPPORTED_ASPECT_RATIOS,
    USE_VERTEXAI,
)
from file_utils import ratio_to_float, resize_to_exact_pixels, save_image_as
from image_generator import ImageGenerationError, generate_and_save_image
from prompt_engineer import generate_detailed_prompt

st.set_page_config(page_title="AI Image Generator", page_icon="🖼️", layout="wide")


@st.cache_resource
def get_client() -> genai.Client:
    if USE_VERTEXAI:
        return genai.Client(
            vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION
        )
    return genai.Client(api_key=GEMINI_API_KEY)


with st.sidebar:
    st.header("Settings")

    if USE_VERTEXAI:
        st.caption(f"Billing: Vertex AI — project `{GOOGLE_CLOUD_PROJECT}` ({GOOGLE_CLOUD_LOCATION})")
        if not GOOGLE_CLOUD_PROJECT:
            st.error("GOOGLE_CLOUD_PROJECT is not set. Add it to your .env file and restart.")
    elif not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is not set. Add it to your .env file and restart.")

    output_dir = Path(
        st.text_input("Output folder", value=str(DEFAULT_OUTPUT_DIR))
    )

    aspect_ratio = st.selectbox(
        "Aspect ratio",
        SUPPORTED_ASPECT_RATIOS,
        index=SUPPORTED_ASPECT_RATIOS.index(DEFAULT_ASPECT_RATIO),
        help="Shape Gemini generates the image in, and the shape the final crop matches.",
    )

    px_col1, px_col2 = st.columns(2)
    with px_col1:
        width_px = st.number_input("Width (px)", min_value=1.0, value=DEFAULT_WIDTH_PX, step=1.0)
    with px_col2:
        height_px = st.number_input("Height (px)", min_value=1.0, value=DEFAULT_HEIGHT_PX, step=1.0)

    typed_ratio = width_px / height_px
    selected_ratio = ratio_to_float(aspect_ratio)
    dimensions_match = abs(typed_ratio - selected_ratio) / selected_ratio <= DIMENSION_MISMATCH_TOLERANCE
    force_mismatch = False

    if not dimensions_match:
        implied_width = height_px * selected_ratio
        implied_height = width_px / selected_ratio
        st.warning(
            f"{width_px:g} × {height_px:g} px doesn't match the {aspect_ratio} aspect ratio. "
            f"To match it, use {implied_width:.1f} × {height_px:g} px, or {width_px:g} × {implied_height:.1f} px, "
            "or pick a different aspect ratio."
        )
        force_mismatch = st.checkbox(
            "Generate anyway",
            help="For ratios more extreme than Gemini supports natively (e.g. thin website "
            "banners), no aspect ratio option will ever match closely. Checking this generates "
            "at the selected aspect ratio above, then crops harder to hit your exact pixel size "
            "— useful on purpose, but be aware more of the generated image gets cut away.",
        )

    quality = st.radio(
        "Image model",
        ["Default (fast, cheap)", "Premium (best product fidelity)"],
        help="Use Premium for jewellery/product shots where reference images must be preserved exactly.",
    )
    image_model = IMAGE_MODEL_DEFAULT if quality.startswith("Default") else IMAGE_MODEL_PREMIUM

    brand_notes = st.text_area(
        "Brand notes (optional)",
        placeholder="e.g. warm gold tones, minimal sets, no busy backgrounds.",
    )

    label = st.text_input("Filename label", value="Hero", help="e.g. Hero, Section1, Social")

    st.divider()
    st.caption(
        "Reference images (optional — for product-preservation, e.g. jewellery shots). "
        "Upload one for a single output named after that file. Upload several and each "
        "one becomes its own output image (same instructions, generated in parallel), "
        "each saved under its own file's name."
    )
    uploaded_files = st.file_uploader(
        "Upload reference image(s)", type=["png", "jpg", "jpeg"], accept_multiple_files=True
    )

    resize_only_clicked = False
    if uploaded_files:
        resize_only_clicked = st.button(
            f"Resize {len(uploaded_files)} image(s) only (no AI)",
            help="Crops+resizes each uploaded image to the size above and saves it "
            "under its own filename — skips Gemini entirely, no API usage. Uses only "
            "the width/height fields, not the aspect ratio dropdown (which only "
            "affects Gemini generation).",
        )

st.title("AI Image Generator — Gemini only")
st.caption("Type an idea. Gemini writes the detailed prompt, Gemini generates the image, it's saved automatically.")

if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.write(turn["content"])
        for image_path in turn.get("image_paths", []):
            if Path(image_path).exists():
                st.image(image_path)
                st.caption(f"Saved to: {image_path}")
            else:
                st.caption(f"⚠️ No longer found on disk (was it moved or deleted?): {image_path}")

if resize_only_clicked:
    st.session_state.history.append(
        {
            "role": "user",
            "content": f"Resize {len(uploaded_files)} uploaded image(s) to {width_px:g} × {height_px:g} px (no AI generation).",
        }
    )
    with st.chat_message("user"):
        st.write(st.session_state.history[-1]["content"])

    with st.chat_message("assistant"):
        saved_paths = []
        for f in uploaded_files:
            resized = resize_to_exact_pixels(Image.open(f), width_px, height_px)
            path = save_image_as(resized, output_dir, filename_stem=Path(f.name).stem)
            st.image(str(path), caption=f.name)
            saved_paths.append(str(path))

        st.success(f"Resized and saved {len(saved_paths)} image(s) to: {output_dir}")
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": f"Resized {len(saved_paths)} image(s), no AI generation used.",
                "image_paths": saved_paths,
            }
        )

idea = st.chat_input("Describe the image you want...")

if idea:
    st.session_state.history.append({"role": "user", "content": idea})
    with st.chat_message("user"):
        st.write(idea)

    with st.chat_message("assistant"):
        if USE_VERTEXAI and not GOOGLE_CLOUD_PROJECT:
            st.error("Cannot generate — GOOGLE_CLOUD_PROJECT is missing.")
            st.stop()
        if not USE_VERTEXAI and not GEMINI_API_KEY:
            st.error("Cannot generate — GEMINI_API_KEY is missing.")
            st.stop()
        if not dimensions_match and not force_mismatch:
            st.error(
                f"Cannot generate — {width_px:g} × {height_px:g} px doesn't match the "
                f"selected {aspect_ratio} aspect ratio. Fix one in the sidebar, or check "
                "\"Generate anyway\" if this ratio is intentionally more extreme than Gemini supports."
            )
            st.stop()

        client = get_client()
        fallback_model = IMAGE_MODEL_VERTEX_FALLBACK if USE_VERTEXAI else None

        # One job per uploaded reference photo (each gets its own output,
        # named after that photo). No uploads -> a single job from the idea.
        if uploaded_files:
            jobs = [
                {"reference_image": Image.open(f), "filename_stem": Path(f.name).stem, "display_name": f.name}
                for f in uploaded_files
            ]
        else:
            jobs = [{"reference_image": None, "filename_stem": None, "display_name": idea}]

        try:
            with st.spinner("Gemini is writing the detailed image prompt..."):
                detailed_prompt = generate_detailed_prompt(
                    client,
                    user_idea=idea,
                    aspect_ratio=aspect_ratio,
                    brand_notes=brand_notes,
                    has_reference_images=bool(uploaded_files),
                )
            with st.expander("Generated image prompt"):
                st.write(detailed_prompt)

            def run_job(job):
                return generate_and_save_image(
                    client,
                    detailed_prompt=detailed_prompt,
                    aspect_ratio=aspect_ratio,
                    model=image_model,
                    output_dir=output_dir,
                    target_width_px=width_px,
                    target_height_px=height_px,
                    reference_image=job["reference_image"],
                    filename_stem=job["filename_stem"],
                    topic=idea,
                    label=label,
                    fallback_model=fallback_model,
                )

            results = {}  # index -> (path, model_used) or ("error", message)
            progress = st.progress(0.0, text=f"Generating 0/{len(jobs)} image(s)...")
            workers = min(MAX_CONCURRENT_GENERATIONS, len(jobs))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                future_to_index = {pool.submit(run_job, job): i for i, job in enumerate(jobs)}
                done = 0
                for future in as_completed(future_to_index):
                    i = future_to_index[future]
                    try:
                        results[i] = future.result()
                    except ImageGenerationError as exc:
                        results[i] = ("error", str(exc))
                    except Exception as exc:  # noqa: BLE001 - one job failing shouldn't crash the batch
                        results[i] = ("error", str(exc))
                    done += 1
                    progress.progress(done / len(jobs), text=f"Generating {done}/{len(jobs)} image(s)...")
            progress.empty()

            saved_paths = []
            for i, job in enumerate(jobs):
                result = results[i]
                if result[0] == "error":
                    st.error(f"{job['display_name']}: failed — {result[1]}")
                    continue
                path, model_used = result
                st.image(str(path), caption=job["display_name"] if uploaded_files else None)
                if model_used != image_model:
                    st.caption(f"Used fallback model `{model_used}` (`{image_model}` unavailable).")
                saved_paths.append(str(path))

            if saved_paths:
                st.success(f"Saved {len(saved_paths)} image(s) to: {output_dir}")

            st.session_state.history.append(
                {
                    "role": "assistant",
                    "content": f"Done. Generated {len(saved_paths)}/{len(jobs)} image(s).",
                    "image_paths": saved_paths,
                }
            )

        except Exception as exc:  # noqa: BLE001 - surface any unexpected error (e.g. prompt stage) to the user
            st.error(f"Something went wrong: {exc}")
