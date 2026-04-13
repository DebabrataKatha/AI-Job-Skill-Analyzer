import streamlit as st
import PyPDF2
import time
import os
from google import genai

# ------------------ GEMINI SETUP ------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Gemini API key not found. Please set it in Streamlit Secrets.")
    st.stop()

client = genai.Client(
    api_key=api_key,
    http_options={"api_version": "v1"}
)

MODEL = "models/gemini-2.5-flash"

# ------------------ FALLBACK SKILLS ------------------
def fallback_skills(text):
    basic = [
        "python","java","c++","sql","aws","docker","git","linux",
        "machine learning","data analysis","html","css","javascript"
    ]
    return [s for s in basic if s in text.lower()]

# ------------------ PDF TEXT EXTRACTION ------------------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text.lower()

# ------------------ RESUME SKILLS ------------------
def extract_resume_skills(text):
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Extract technical skills from this resume:\n{text}"
        )
        skills = response.text.lower().split(",")
        return [s.strip() for s in skills if s.strip()]
    except:
        return fallback_skills(text)

# ------------------ JOB SKILLS ------------------
def extract_job_skills(text):
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=f"Extract required technical skills from this job description:\n{text}"
        )
        skills = response.text.lower().split(",")
        return [s.strip() for s in skills if s.strip()]
    except:
        return fallback_skills(text)

# ------------------ MATCH LOGIC ------------------
def calculate_match(resume_skills, job_skills):
    if not job_skills:
        return 0, [], []

    resume_set = set(resume_skills)
    job_set = set(job_skills)

    matched = list(resume_set & job_set)
    missing = list(job_set - resume_set)

    percent = (len(matched) / len(job_set)) * 100

    return round(percent, 2), matched, missing

# ------------------ AI ROADMAP (FINAL FIXED VERSION) ------------------
def ai_suggestions(missing):
    if not missing:
        return "✅ You are a strong match for this job!"

    try:
        time.sleep(1)

        response = client.models.generate_content(
            model=MODEL,
            contents=f"""
You are an expert career mentor.

Skills to learn:
{missing}

Create a detailed learning roadmap.

Rules:
- Write 4–5 steps
- Start from beginner → advanced
- Explain each step clearly
- Mention tools or concepts to learn

Example:

Step 1: Learn basics of Python (variables, loops, functions)
Step 2: Practice using small datasets
Step 3: Learn advanced tools like Pandas and NumPy
Step 4: Build real-world projects
Step 5: Deploy your project

Now generate roadmap:
"""
        )

        if response and response.text:
            return response.text.strip()

    except:
        pass

    # 🔥 SMART FALLBACK (DETAILED)
    return f"""
Step 1: Start with basics of {missing[0]} (fundamentals and concepts)

Step 2: Practice using tutorials and small exercises

Step 3: Work on beginner projects using {', '.join(missing[:2])}

Step 4: Learn advanced concepts and tools related to these skills

Step 5: Build real-world applications to strengthen your understanding
"""

# ------------------ STREAMLIT UI ------------------
st.title("🤖 AI Job Skill Analyzer")

file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job = st.text_area("Paste Job Description")

if st.button("Analyze"):
    if file and job:

        resume_text = extract_text_from_pdf(file)

        resume_skills = extract_resume_skills(resume_text)
        job_skills = extract_job_skills(job.lower())

        match, matched, missing = calculate_match(resume_skills, job_skills)

        suggestions = ai_suggestions(missing)

        st.subheader("📊 Results")
        st.write(f"Match Percentage: {match}%")

        st.write("✅ Matched Skills:", matched)
        st.write("❌ Missing Skills:", missing)

        st.subheader("💡 Learning Roadmap")
        st.write(suggestions)

    else:
        st.warning("Upload resume and job description")
