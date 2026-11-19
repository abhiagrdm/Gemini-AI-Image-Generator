import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Vertex AI mode: draws from Google Cloud billing/credits instead of the
# Gemini API's separate Prepay balance. Needs `gcloud auth application-default
# login` done once on this machine, plus the Vertex AI API enabled on the
# project. Falls back to the plain Gemini API key when this is False.
USE_VERTEXAI = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Text model used to turn a short idea into a detailed image-generation prompt.
TEXT_MODEL = "gemini-2.5-flash"

# Image models. "default" is cheaper/faster and fine for most marketing images.
# "premium" gives better instruction-following and product fidelity, worth the
# extra cost when reference images (e.g. jewellery product shots) must be
# preserved accurately.
IMAGE_MODEL_DEFAULT = "gemini-3.1-flash-image"
IMAGE_MODEL_PREMIUM = "gemini-3-pro-image"

# gemini-3.1-flash-image / gemini-3-pro-image are still allowlist-gated on
# Vertex AI for many projects (GA already on the plain Gemini API). If a
# request 404s under Vertex AI mode, we automatically retry once with this
# older, stable-on-Vertex model instead of failing outright.
IMAGE_MODEL_VERTEX_FALLBACK = "gemini-2.5-flash-image"

DEFAULT_OUTPUT_DIR = Path(__file__).parent / "outputs"

# How many images to generate at once when batch-processing multiple
# uploaded reference photos. Kept low by default because new/trial Vertex AI
# projects get small per-minute quotas for image models — raise this only
# after requesting a quota increase in Cloud Console (IAM & Admin > Quotas,
# filter aiplatform.googleapis.com), otherwise batches will just 429.
MAX_CONCURRENT_GENERATIONS = 2

# Aspect ratios accepted by the Gemini image models' ImageConfig. The person
# generating an image picks one of these directly in the sidebar.
SUPPORTED_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
]
DEFAULT_ASPECT_RATIO = "4:5"

# Starting values shown in the pixel-dimension inputs — the person generating
# an image can change these freely per request.
DEFAULT_WIDTH_PX = 295.5
DEFAULT_HEIGHT_PX = 377.87

# How far the typed width/height ratio may drift from the selected aspect
# ratio before we block generation and ask the user to fix one or the other
# (e.g. typing 800x400 under a selected "1:1" is not allowed). Set above 2.25%
# so the app's own defaults (295.5x377.87 vs its closest ratio, 4:5) start
# out valid rather than launching in an already-blocked state.
DIMENSION_MISMATCH_TOLERANCE = 0.03
