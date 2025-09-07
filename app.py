import os
import io
from pathlib import Path
import traceback

import gradio as gr
import PyPDF2
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------------------------------
# Env / Model
# ---------------------------------------------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if not API_KEY:
    print("⚠️ GOOGLE_API_KEY is missing. Add it to your .env")
genai.configure(api_key=API_KEY)

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def extract_text_from_pdf_path(path: str) -> str:
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()

def read_resume_input(pasted_text: str) -> str:
    """Read only pasted resume text (PDF upload removed)."""
    try:
        if pasted_text and pasted_text.strip():
            return pasted_text.strip()
        return ""
    except Exception as e:
        print("Text read error:", e)
        print(traceback.format_exc())
        return f"⚠️ Error reading text: {e}"

def call_gemini(resume_text: str, job_role: str) -> str:
    if not API_KEY:
        return ("No API key found. Set GOOGLE_API_KEY in your .env "
                "or pass it to google.generativeai.configure(api_key=...).")

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"""
You are a senior career coach. Review the following resume for the target role **{job_role}**.

Return:
- Summary (2–3 lines)
- Top strengths (bullets)
- Gaps / missing keywords (bullets)
- Tailored improvements (bullets)
- A quick 0–10 fit score

Resume:
{resume_text}
"""
        resp = model.generate_content(prompt)
        return (resp.text or "").strip() or "No response text returned by the model."
    except Exception as e:
        print("Gemini error:", e)
        print(traceback.format_exc())
        return f"🔥 Gemini error: {e}"

# ---------------------------------------------------
# Gradio UI
# ---------------------------------------------------
CUSTOM_CSS = """
:root { --radius: 16px; }
body { background: #0d1117; color: #c9d1d9; font-family: Inter, ui-sans-serif, system-ui; }
.gradio-container { max-width: 1200px !important; margin: 0 auto; }
.card { background:#161b22; border-radius:16px; padding:18px; box-shadow:0 6px 24px rgba(0,0,0,0.45); }
.card:hover { box-shadow:0 10px 30px rgba(0,0,0,0.55); transform: translateY(-2px); transition: .2s ease; }
h1 { color:#58a6ff; text-align:center; margin: 10px 0 6px; }
.subtle { text-align:center; color:#9aa6b2; margin-bottom: 22px; }
.gr-button { border-radius:12px !important; }
"""

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="violet", secondary_hue="blue"),
    css=CUSTOM_CSS,
    title="🚀 Smart Resume Analyzer"  # <--- Browser Tab Title
) as demo:

    # Force browser tab title using HTML/JS
    gr.HTML("<script>document.title = '🚀 Smart Resume Analyzer'</script>")

    gr.HTML("<h1>🚀 Smart Resume Analyzer</h1>")
    gr.HTML("<div class='subtle'>AI feedback that’s actually useful — clean, quick, and tailored to your role.</div>")

    with gr.Row():
        with gr.Column(scale=1, elem_classes="card"):
            gr.Markdown("### 📂 Paste Resume Text")
            text_comp = gr.Textbox(label="Paste Resume Here", lines=12, placeholder="Paste your resume here…")
            role_comp = gr.Textbox(label="🎯 Target Job Role", placeholder="e.g. Data Scientist, Backend Engineer")
            go_btn = gr.Button("✨ Analyze Resume", variant="primary")

        with gr.Column(scale=2, elem_classes="card"):
            gr.Markdown("### 💡 AI Feedback")
            feedback_out = gr.Textbox(label="", lines=20, interactive=False, show_copy_button=True)

    def pipeline(pasted_text, job_role):
        try:
            resume_text = read_resume_input(pasted_text)
            if not resume_text or resume_text.startswith("⚠️"):
                return (resume_text or "⚠️ Please paste your resume text.")

            if not job_role or not job_role.strip():
                return "⚠️ Please enter a target job role for tailored feedback."

            feedback = call_gemini(resume_text, job_role.strip())
            return feedback
        except Exception as e:
            print("UNCAUGHT ERROR:", e)
            print(traceback.format_exc())
            return f"💥 Unexpected error: {e}"

    go_btn.click(fn=pipeline,
                 inputs=[text_comp, role_comp],
                 outputs=[feedback_out])

if __name__ == "__main__":
    demo.launch()

