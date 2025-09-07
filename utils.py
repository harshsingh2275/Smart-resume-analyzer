import os
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

# === API CALLERS ===
def call_openai(system_prompt: str, user_prompt: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ OpenAI error: {e}"

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    try:
        import google.genai as genai
        from google.genai.types import Content, Part
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        joined = (system_prompt + "\n\n" if system_prompt else "") + user_prompt
        contents = [Content(role="user", parts=[Part.from_text(joined)])]
        result = client.models.generate_content(model=model, contents=contents)
        return result.text or "⚠️ Gemini returned no text."
    except Exception as e:
        return f"⚠️ Gemini error: {e}"

def call_cohere(system_prompt: str, user_prompt: str) -> str:
    try:
        import cohere
        co = cohere.ClientV2(os.getenv("COHERE_API_KEY"))
        model = os.getenv("COHERE_MODEL", "command-a-03-2025")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        res = co.chat(model=model, messages=messages, temperature=0.4)
        blocks = res.message.content if hasattr(res, "message") else []
        text_parts = [getattr(b, "text", None) or b.get("text") for b in blocks if b]
        return "\n".join([t for t in text_parts if t]) or "⚠️ Cohere returned no text."
    except Exception as e:
        return f"⚠️ Cohere error: {e}"

# === Resume helpers ===
def _read_pdf(file_obj) -> str:
    if PdfReader is None:
        return "⚠️ pypdf not installed. Install with: pip install pypdf"
    try:
        reader = PdfReader(file_obj.name)
        return "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
    except Exception as e:
        return f"⚠️ Could not read PDF: {e}"

def resolve_resume_text(resume_file, resume_text) -> str:
    if resume_text and resume_text.strip():
        return resume_text.strip()
    if resume_file is None:
        return ""
    name = getattr(resume_file, "name", "")
    ext = os.path.splitext(name.lower())[-1]
    if ext == ".pdf":
        return _read_pdf(resume_file)
    elif ext == ".txt":
        try:
            return resume_file.read().decode("utf-8", errors="ignore")
        except Exception:
            return resume_file.read().decode("latin-1", errors="ignore")
    else:
        return "⚠️ Unsupported file type. Please upload PDF or TXT."

def build_review_prompt(jd: str, resume: str) -> str:
    return f"""Evaluate this resume against the job description.

[JOB DESCRIPTION]
{jd}

[RESUME]
{resume}

Return your feedback in markdown with the sections described above. Do not invent work history.
"""

def build_improve_prompt(jd: str, resume: str) -> str:
    return f"""Rewrite this resume so that:
1. It highlights the candidate’s fit for the given job description.
2. Use strong action verbs, STAR-style bullets, and measurable impact where possible.
3. Preserve factual content (don’t invent degrees/jobs).
4. Make it concise, ATS-friendly, and polished.

[JOB DESCRIPTION]
{jd}

[RESUME]
{resume}

Return the improved resume in plain text format.
"""

# === PDF helper ===
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

def save_text_as_pdf(text: str, filename: str = "improved_resume.pdf") -> str:
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        margin = 50
        max_width = width - 2*margin
        y = height - margin

        for para in text.split("\n"):
            lines = simpleSplit(para, "Helvetica", 10, max_width)
            if not lines:
                lines = [""]
            for line in lines:
                c.setFont("Helvetica", 10)
                c.drawString(margin, y, line)
                y -= 14
                if y < margin:
                    c.showPage()
                    y = height - margin
        c.save()
        return filename
    except Exception as e:
        with open(filename.replace(".pdf", ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
        return filename.replace(".pdf", ".txt")
