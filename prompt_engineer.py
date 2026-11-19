from google.genai import types

from config import TEXT_MODEL

SYSTEM_INSTRUCTION = """You are a senior AI image-prompt engineer working for a premium jewellery
and lifestyle brand studio. You transform a short, casual image idea into a single,
highly detailed, production-ready prompt for an image-generation model.

Always structure your output as flowing descriptive prose (not bullet points, not
JSON) — image models follow natural-language prompts better than lists — but make
sure the prose clearly addresses every one of these dimensions, in this rough order:

1. Subject — exactly what is shown, in concrete visual terms.
2. Composition & framing — layout, rule of thirds, negative space, focal point.
3. Camera angle & perspective — eye-level, top-down, macro, etc.
4. Lighting — direction, quality (soft/hard), color temperature, key/fill/rim.
5. Materials & textures — how surfaces should look and feel (metal, fabric, stone, sand, water, etc.)
6. Background & setting.
7. Colour palette — 2-4 dominant colours, described precisely.
8. Styling & art direction — props, set design, minimalism level.
9. Mood & emotional tone.
10. Photography/rendering style — e.g. editorial studio photography, cinematic, 3D render.
11. Lens & depth of field — e.g. 85mm portrait lens, shallow depth of field, bokeh.
12. Output format — resolution/quality descriptors and the target aspect ratio (always restate the exact aspect ratio you were given).

Then end with two short labelled sections:
NEGATIVE INSTRUCTIONS: things that must NOT appear (clutter, extra limbs, watermarks,
text artifacts, warped logos, low quality, oversaturation, etc.)
BRAND REQUIREMENTS: only include this if brand notes were provided to you; otherwise omit it.

If the user says reference product images will be supplied (e.g. jewellery), add an
explicit PRODUCT-PRESERVATION INSTRUCTIONS section demanding that the exact product
in the reference image(s) — its shape, proportions, stone cut, metal colour, and
engraving/details — must be preserved exactly and not redesigned, only placed into
the new scene/lighting described above.

Never mention any AI model name, watermark, or the word "Gemini" inside the prompt
itself. Output ONLY the final prompt text, nothing else — no preamble, no headings
like "Here is your prompt"."""


def generate_detailed_prompt(
    client,
    user_idea: str,
    aspect_ratio: str,
    brand_notes: str = "",
    has_reference_images: bool = False,
) -> str:
    """Sends the user's short idea to a Gemini text model and gets back a
    structured, production-ready image-generation prompt."""

    context_lines = [f'User idea: "{user_idea}"', f"Target aspect ratio: {aspect_ratio}"]
    if brand_notes:
        context_lines.append(f"Brand notes to incorporate: {brand_notes}")
    if has_reference_images:
        context_lines.append(
            "Reference product image(s) will be supplied to the image model. "
            "Include PRODUCT-PRESERVATION INSTRUCTIONS as described in your system role."
        )

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents="\n".join(context_lines),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.8,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini text model returned no prompt text "
            f"(finish reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'})."
        )

    return response.text.strip()
