# Gemini-Powered AI Image Generator

An AI-powered product photography application built with **Streamlit and Google's Gemini API**. Transform rough image descriptions into detailed photography prompts and generate high-quality, brand-consistent product images using reference photos. Automatically apply brand guidelines, preserve product characteristics, generate images in custom aspect ratios, and save them at exact pixel dimensions to your chosen output folder.

---

## Demo

> Built with Streamlit. Runs locally in your browser and can be deployed to a cloud hosting platform.

---

## How It Works

The application uses a **two-stage Gemini AI pipeline** to transform simple descriptions into production-ready product images.

1. **Prompt Engineering:** Gemini (`gemini-2.5-flash`) converts rough descriptions into detailed photography prompts covering composition, camera angle, lighting, materials, background, colour palette, styling, mood, lens and depth of field.

2. **Brand & Product Context:** Incorporates custom brand guidelines and reference product images into the generation instructions. Dedicated product-preservation instructions help maintain the original product's appearance, including shape, proportions, colours, materials and distinctive details.

3. **Image Generation:** Gemini Image models (`gemini-3.1-flash-image` or `gemini-3-pro-image`) generate the final image using the enhanced prompt and optional reference image.

4. **Image Processing:** Pillow (PIL) automatically crops and resizes generated images using LANCZOS resampling to achieve the requested pixel dimensions.

5. **Automatic Storage:** Saves the final images as PNG files in the user-defined output folder, with automatic filename handling to prevent overwriting existing files.

---

## Tech Stack

| **Layer** | **Tool** |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) |
| Programming Language | Python |
| AI / Prompt Engineering | [Google Gemini API](https://ai.google.dev/) (`gemini-2.5-flash`) |
| Image Generation | Gemini 3.1 Flash Image |
| Premium Image Generation | Gemini 3 Pro Image |
| API Integration | [Google Gen AI SDK](https://github.com/googleapis/python-genai) (`google-genai`) |
| Cloud AI Infrastructure | [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) (optional) |
| Image Processing | [Pillow](https://pypi.org/project/pillow/) |
| Configuration Management | python-dotenv |
| Parallel Processing | concurrent.futures |

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/abhisheka24/AI-Image-Generator.git

cd AI-Image-Generator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API credentials

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key

GOOGLE_GENAI_USE_VERTEXAI=false
```

Alternatively, configure Google Cloud Vertex AI:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

For Vertex AI, enable the Vertex AI API and authenticate using Google Cloud Application Default Credentials:

```bash
gcloud auth application-default login
```

**Note:** The application supports either Gemini API key authentication or Vertex AI authentication.

### 4. Run the application

```bash
streamlit run app.py
```

The application will open in your browser at:

`http://localhost:8501`

---

## Usage

1. **Configure Output Folder:** Specify where generated images should be saved. The application automatically creates the folder if it does not exist.

2. **Choose Image Dimensions:** Select an aspect ratio (1:1, 4:5, 3:4, 16:9, etc.) and enter your desired width and height in pixels.

3. **Select Image Model:** Choose between Default (Gemini 3.1 Flash Image) for faster, lower-cost generation or Premium (Gemini 3 Pro Image) for higher-quality product imagery.

4. **Add Brand Guidelines:** Enter brand-specific instructions covering colours, backgrounds, lighting, styling, props and visual identity.

5. **Upload Reference Images:** Upload one or multiple product photographs. Each uploaded reference image becomes an individual generation job.

6. **Describe Your Image:** Enter a rough description in the chat interface. For example, "A diamond ring placed on an ivory display stand with soft studio lighting."

7. **Review the Generated Prompt:** Expand the Generated Image Prompt section to inspect the detailed prompt automatically created by Gemini.

8. **Generate & Save:** View the generated images directly in Streamlit. Each successful image is automatically saved as a PNG in your selected output folder.

### Additional Feature: Resize Only

The application also provides a resize-only option that crops and resizes uploaded images to the requested pixel dimensions without calling Gemini or consuming API credits.

---

## Project Features

| **Feature** | **Description** |
|---|---|
| AI Prompt Engineering | Converts rough descriptions into detailed photography prompts |
| Brand Consistency | Applies custom brand guidelines to every generation |
| Reference-Based Generation | Uses uploaded product images as visual references |
| Product Preservation | Includes dedicated instructions to minimise changes to original product details |
| Multiple Image Models | Offers Default and Premium Gemini image models |
| Custom Aspect Ratios | Supports 10 predefined aspect ratios |
| Exact Pixel Dimensions | Uses Pillow to crop and resize images to requested dimensions |
| Batch Generation | Generates one image per uploaded reference photo |
| Parallel Processing | Processes multiple image-generation jobs concurrently |
| Automatic File Saving | Saves generated PNG images directly to the selected folder |
| Safe File Naming | Prevents accidental overwriting of existing images |
| Retry & Fallback Mechanism | Handles temporary API errors and supports a Vertex AI fallback model |
| Resize-Only Mode | Resizes images without using AI or making API calls |

---

## Project Structure

```text
AI-Image-Generator/
│
├── app.py                  # Main Streamlit application and user interface
├── config.py               # API configuration, models, aspect ratios and defaults
├── prompt_engineer.py      # Gemini-powered prompt generation
├── image_generator.py      # Gemini image generation, retries and fallback
├── file_utils.py           # Image cropping, resizing and file management
│
├── requirements.txt        # Python dependencies
├── .env                    # API credentials (not committed to GitHub)
├── .env.example            # Environment variable template
├── .gitignore              # Excludes sensitive and unnecessary files
├── README.md               # Project documentation
│
└── outputs/                # Generated images (created automatically)
```

---

## Models & API

The application uses Google's official **Google Gen AI Python SDK (`google-genai`)** to interact with Gemini models.

| **Purpose** | **Model** |
|---|---|
| Prompt Engineering | `gemini-2.5-flash` |
| Default Image Generation | `gemini-3.1-flash-image` |
| Premium Image Generation | `gemini-3-pro-image` |
| Vertex AI Fallback | `gemini-2.5-flash-image` |

### API Integration

- **Prompt Generation:** Sends the user's description, selected aspect ratio and brand guidelines to Gemini.
- **Image Generation:** Sends the enhanced prompt and optional reference image to the selected Gemini image model.
- **Image Processing:** Uses Pillow for centre cropping, aspect ratio adjustment and exact pixel resizing.
- **Error Handling:** Implements automatic retries for temporary failures and rate limits, along with model fallback when supported by the configuration.

All model names, aspect ratios, default dimensions and generation settings are maintained in `config.py`.

---

## Important Notes

- Product-preservation instructions help maintain reference product characteristics, but AI generation cannot guarantee pixel-perfect replication.
- Exact output dimensions are achieved through post-generation image processing.
- Gemini API usage may incur charges depending on the selected model and usage limits.
- Vertex AI model availability may depend on project access and regional availability.
- Keep API credentials private and never commit your `.env` file to GitHub.

---

**Author:** Abhishek Agrawal · MBA Finance · 2026

**Connect:** [LinkedIn](https://www.linkedin.com/in/abhisheka24) · [Email](mailto:abhishek.iitk.mba@gmail.com)
